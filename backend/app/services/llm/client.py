"""LLM access through OpenRouter's OpenAI-compatible API.

Structured output is forced with a function tool call. If the endpoint rejects forced tool choice, the client
falls back to `response_format=json_object` with the schema embedded in the system prompt. Either way the output
is validated with Pydantic, retried once with the validation error, then rejected (LLMOutputError).
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ValidationError
from tenacity import RetryError, Retrying, retry_if_exception, stop_after_attempt, wait_random_exponential

from app.core.config import Settings, get_settings
from app.core.errors import LLMNotConfigured, LLMOutputError, LLMUnavailable
from app.services.llm.structured import inline_schema, parse_arguments

log = logging.getLogger("dealbridge.llm")

Kind = Literal["main", "fast"]


class LLMClient(Protocol):
    def complete_structured(
        self,
        kind: Kind,
        system: str,
        messages: list[dict],
        output_model: type[BaseModel],
        tool_name: str,
        max_tokens: int,
        temperature: float,
    ) -> BaseModel: ...


def _retryable(exc: BaseException) -> bool:
    import openai

    if isinstance(exc, (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)):
        return True
    return isinstance(exc, openai.APIStatusError) and exc.status_code >= 500


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        import openai

        self.s = settings
        self._openai = openai
        self._clients = {
            "main": openai.OpenAI(
                api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL, timeout=settings.LLM_TIMEOUT_SECONDS, max_retries=0
            ),
            "fast": openai.OpenAI(
                api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL, timeout=settings.LLM_FAST_TIMEOUT_SECONDS, max_retries=0
            ),
        }
        self.json_mode_fallback = False  # set when the endpoint refuses forced tool_choice
        self.omit_temperature = False  # set when the model refuses the temperature parameter

    def _model(self, kind: Kind) -> str:
        return self.s.LLM_MODEL if kind == "main" else self.s.LLM_FAST_MODEL

    def _call(self, kind: Kind, payload: dict) -> Any:
        client = self._clients[kind]
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self.s.LLM_MAX_RETRIES + 1),
                wait=wait_random_exponential(multiplier=1, max=8),
                retry=retry_if_exception(_retryable),
                reraise=False,
            ):
                with attempt:
                    return client.chat.completions.create(**payload)
        except RetryError as exc:
            log.warning("llm retries exhausted", extra={"kind": kind, "error": type(exc.last_attempt.exception()).__name__})
            raise LLMUnavailable() from exc
        except self._openai.AuthenticationError as exc:
            raise LLMUnavailable("The LLM provider rejected the API key. Check LLM_API_KEY.") from exc
        except self._openai.APIStatusError:
            raise
        except self._openai.APIError as exc:
            raise LLMUnavailable() from exc

    def _payload(self, kind, system, messages, output_model, tool_name, max_tokens, temperature) -> dict:
        schema = inline_schema(output_model)
        payload: dict = {"model": self._model(kind), "max_tokens": max_tokens}
        if self.s.LLM_REASONING_EFFORT:
            payload["extra_body"] = {"reasoning_effort": self.s.LLM_REASONING_EFFORT}
        if not self.omit_temperature:
            payload["temperature"] = temperature
        if self.json_mode_fallback:
            sys = (
                f"{system}\n\nRespond ONLY with a JSON object for `{tool_name}` that validates against this JSON schema:\n"
                f"{json.dumps(schema)}"
            )
            payload["messages"] = [{"role": "system", "content": sys}, *messages]
            payload["response_format"] = {"type": "json_object"}
        else:
            payload["messages"] = [{"role": "system", "content": system}, *messages]
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {"name": tool_name, "description": f"Return the {tool_name} result.", "parameters": schema},
                }
            ]
            payload["tool_choice"] = {"type": "function", "function": {"name": tool_name}}
        return payload

    def _extract(self, resp) -> str | None:
        choice = resp.choices[0].message
        if self.json_mode_fallback:
            return choice.content
        calls = getattr(choice, "tool_calls", None) or []
        return calls[0].function.arguments if calls else None

    def complete_structured(self, kind, system, messages, output_model, tool_name, max_tokens, temperature):
        convo = list(messages)
        last_error = ""
        for validation_try in range(2):
            payload = self._payload(kind, system, convo, output_model, tool_name, max_tokens, temperature)
            start = time.perf_counter()
            try:
                resp = self._call(kind, payload)
            except self._openai.BadRequestError as exc:
                text = str(exc).lower()
                if "temperature" in text and not self.omit_temperature:
                    self.omit_temperature = True
                    log.warning("model rejected temperature; omitting it", extra={"model": payload["model"]})
                    return self.complete_structured(kind, system, messages, output_model, tool_name, max_tokens, temperature)
                if "tool" in text and not self.json_mode_fallback:
                    self.json_mode_fallback = True
                    log.warning("endpoint rejected forced tool_choice; using json_object mode", extra={"model": payload["model"]})
                    return self.complete_structured(kind, system, messages, output_model, tool_name, max_tokens, temperature)
                raise LLMUnavailable("The LLM provider rejected the request.") from exc
            except self._openai.APIStatusError as exc:
                raise LLMUnavailable() from exc
            usage = getattr(resp, "usage", None)
            log.info(
                "llm call",
                extra={
                    "model": payload["model"],
                    "kind": kind,
                    "tool": tool_name,
                    "latency_ms": round((time.perf_counter() - start) * 1000),
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                },
            )
            raw = self._extract(resp)
            try:
                return parse_arguments(raw, output_model)
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                last_error = str(exc)[:1500]
                log.warning(
                    "llm output failed validation",
                    extra={
                        "tool": tool_name,
                        "try": validation_try + 1,
                        "finish_reason": getattr(resp.choices[0], "finish_reason", None),
                        "error": last_error[:300],
                    },
                )
                convo = [
                    *messages,
                    {
                        "role": "user",
                        "content": f"Your previous `{tool_name}` output was invalid: {last_error}\nCall `{tool_name}` again with valid arguments.",
                    },
                ]
        raise LLMOutputError(f"The language model returned invalid `{tool_name}` output twice.")


Responder = BaseModel | Callable[[str, list[dict]], BaseModel] | Exception


class FakeLLMClient:
    """Scripted responses for tests (APP_ENV=test only). Responses are queued per output model."""

    def __init__(self):
        self._queues: dict[str, deque[Responder]] = defaultdict(deque)
        self.calls: list[dict] = []
        self._lock = threading.Lock()

    def push(self, output_model: type[BaseModel], *responses: Responder) -> None:
        with self._lock:
            self._queues[output_model.__name__].extend(responses)

    def reset(self) -> None:
        with self._lock:
            self._queues.clear()
            self.calls.clear()

    def pending(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._queues.items() if v}

    def complete_structured(self, kind, system, messages, output_model, tool_name, max_tokens, temperature):
        with self._lock:
            self.calls.append({"kind": kind, "tool": tool_name, "model": output_model.__name__, "messages": messages, "system": system})
            q = self._queues.get(output_model.__name__)
            if not q:
                raise AssertionError(f"FakeLLMClient: unexpected call for {output_model.__name__} ({tool_name})")
            r = q.popleft()
        if isinstance(r, Exception):
            raise r
        out = r(system, messages) if callable(r) and not isinstance(r, BaseModel) else r
        return output_model.model_validate(out.model_dump() if isinstance(out, BaseModel) else out)


_fake: FakeLLMClient | None = None
_real: OpenAICompatibleClient | None = None


def get_fake_llm() -> FakeLLMClient:
    global _fake
    if get_settings().APP_ENV != "test":
        raise RuntimeError("FakeLLMClient is only available when APP_ENV=test")
    if _fake is None:
        _fake = FakeLLMClient()
    return _fake


def get_llm() -> LLMClient:
    """The configured client. Raises LLMNotConfigured (503) when no key is set."""
    global _real
    s = get_settings()
    if s.LLM_USE_FAKE:
        if s.APP_ENV != "test":
            raise RuntimeError("LLM_USE_FAKE is only allowed when APP_ENV=test")
        return get_fake_llm()
    if not s.LLM_API_KEY.strip():
        raise LLMNotConfigured()
    if _real is None:
        _real = OpenAICompatibleClient(s)
    return _real
