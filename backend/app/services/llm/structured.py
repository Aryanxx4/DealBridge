"""Helpers for schema-constrained (tool-forced) LLM output."""

from __future__ import annotations

import copy
import json

from pydantic import BaseModel, ValidationError


def inline_schema(model: type[BaseModel]) -> dict:
    """Pydantic JSON schema with $defs/$ref inlined (some OpenAI-compatible endpoints reject $ref)."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                name = node["$ref"].split("/")[-1]
                return resolve(copy.deepcopy(defs[name]))
            return {k: resolve(v) for k, v in node.items() if k != "title"}
        if isinstance(node, list):
            return [resolve(x) for x in node]
        return node

    return resolve(schema)


_CONTAINER_ERRORS = {"list_type", "dict_type", "model_type", "model_attributes_type"}


def _decode_stringified_containers(data, errors: list[dict]) -> bool:
    """Some models send a nested list or object as a JSON string. Decode only the
    fields the validator rejected for that reason. Returns True if anything changed."""
    changed = False
    for err in errors:
        if err.get("type") not in _CONTAINER_ERRORS or not isinstance(err.get("input"), str):
            continue
        text = err["input"].strip()
        if not text.startswith(("[", "{")):
            continue
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            continue
        *path, last = err["loc"]
        parent = data
        try:
            for key in path:
                parent = parent[key]
            if parent[last] == err["input"]:
                parent[last] = decoded
                changed = True
        except (KeyError, IndexError, TypeError):
            continue
    return changed


def parse_arguments(raw: str | dict | None, model: type[BaseModel]) -> BaseModel:
    """Validate tool-call arguments (JSON string or dict) against the output model."""
    if raw is None:
        raise ValueError("the model did not call the required tool")
    data = json.loads(raw) if isinstance(raw, str) else copy.deepcopy(raw)
    for _ in range(3):  # nested stringified containers may need a few passes
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            if not _decode_stringified_containers(data, exc.errors()):
                raise
    return model.model_validate(data)
