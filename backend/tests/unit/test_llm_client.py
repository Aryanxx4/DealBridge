"""QwenClient behaviour with a stubbed OpenAI client (no network)."""

import json
from types import SimpleNamespace

import httpx
import openai
import pytest
from pydantic import BaseModel

from app.core.config import load_settings
from app.core.errors import LLMOutputError, LLMUnavailable
from app.services.llm.client import QwenClient
from app.services.llm.structured import inline_schema


class Out(BaseModel):
    answer: str
    score: int


class Nested(BaseModel):
    items: list[Out]


def _settings():
    return load_settings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://x:y@h/db",
        QDRANT_URL="http://q",
        APP_SECRET_KEY="k",
        LLM_API_KEY="sk-test-not-real",
        LLM_MAX_RETRIES=1,
    )


def _tool_resp(args):
    call = SimpleNamespace(function=SimpleNamespace(arguments=json.dumps(args) if isinstance(args, dict) else args))
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[call], content=None))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )


def _json_resp(args):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None, content=json.dumps(args)))], usage=None)


class Stub:
    def __init__(self, responses):
        self.responses = list(responses)
        self.payloads = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **payload):
        self.payloads.append(payload)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _client(responses):
    c = QwenClient(_settings())
    stub = Stub(responses)
    c._clients = {"main": stub, "fast": stub}
    return c, stub


def _bad_request(msg):
    req = httpx.Request("POST", "https://example.invalid")
    return openai.BadRequestError(msg, response=httpx.Response(400, request=req), body=None)


def test_forced_tool_call_payload_and_parse():
    c, stub = _client([_tool_resp({"answer": "ok", "score": 3})])
    out = c.complete_structured("main", "sys", [{"role": "user", "content": "q"}], Out, "my_tool", 100, 0.0)
    assert out == Out(answer="ok", score=3)
    p = stub.payloads[0]
    assert p["model"] == "qwen3.8-max" and p["tool_choice"] == {"type": "function", "function": {"name": "my_tool"}}
    assert p["extra_body"] == {"enable_thinking": False} and p["messages"][0] == {"role": "system", "content": "sys"}
    assert p["tools"][0]["function"]["parameters"]["required"] == ["answer", "score"]


def test_fast_kind_uses_fast_model():
    c, stub = _client([_tool_resp({"answer": "ok", "score": 1})])
    c.complete_structured("fast", "s", [], Out, "t", 10, 0.0)
    assert stub.payloads[0]["model"] == "qwen3.8-flash"


def test_validation_error_retried_once_then_rejected():
    c, stub = _client([_tool_resp({"answer": "x"}), _tool_resp({"answer": "x", "score": 2})])
    assert c.complete_structured("main", "s", [{"role": "user", "content": "q"}], Out, "t", 10, 0.0).score == 2
    assert "was invalid" in stub.payloads[1]["messages"][-1]["content"]
    c, _ = _client([_tool_resp("not json"), _tool_resp({"score": "x"})])
    with pytest.raises(LLMOutputError):
        c.complete_structured("main", "s", [], Out, "t", 10, 0.0)


def test_missing_tool_call_counts_as_invalid():
    empty = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[], content="plain text"))], usage=None)
    c, _ = _client([empty, _tool_resp({"answer": "a", "score": 1})])
    assert c.complete_structured("main", "s", [], Out, "t", 10, 0.0).answer == "a"


def test_temperature_rejection_falls_back_without_temperature():
    c, stub = _client([_bad_request("temperature is not supported for this model"), _tool_resp({"answer": "a", "score": 1})])
    c.complete_structured("main", "s", [], Out, "t", 10, 0.2)
    assert "temperature" in stub.payloads[0] and "temperature" not in stub.payloads[1]


def test_tool_choice_rejection_falls_back_to_json_mode():
    c, stub = _client([_bad_request("tool_choice is not supported"), _json_resp({"answer": "a", "score": 1})])
    assert c.complete_structured("main", "s", [], Out, "t", 10, 0.0).answer == "a"
    p = stub.payloads[1]
    assert p["response_format"] == {"type": "json_object"} and "tools" not in p and "JSON schema" in p["messages"][0]["content"]


def test_transient_errors_retry_then_raise_unavailable():
    req = httpx.Request("POST", "https://example.invalid")
    c, stub = _client([openai.APIConnectionError(request=req), openai.APIConnectionError(request=req)])
    with pytest.raises(LLMUnavailable):
        c.complete_structured("main", "s", [], Out, "t", 10, 0.0)
    assert len(stub.payloads) == 2  # LLM_MAX_RETRIES=1 -> two attempts


def test_auth_error_maps_to_unavailable():
    req = httpx.Request("POST", "https://example.invalid")
    c, _ = _client([openai.AuthenticationError("bad key", response=httpx.Response(401, request=req), body=None)])
    with pytest.raises(LLMUnavailable) as e:
        c.complete_structured("main", "s", [], Out, "t", 10, 0.0)
    assert "API key" in e.value.message


def test_inline_schema_has_no_refs():
    s = inline_schema(Nested)
    assert "$ref" not in json.dumps(s) and "$defs" not in s
    assert s["properties"]["items"]["items"]["properties"]["score"]["type"] == "integer"
