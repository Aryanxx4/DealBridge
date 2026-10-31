"""Helpers for schema-constrained (tool-forced) LLM output."""

from __future__ import annotations

import copy
import json

from pydantic import BaseModel


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


def parse_arguments(raw: str | dict | None, model: type[BaseModel]) -> BaseModel:
    """Validate tool-call arguments (JSON string or dict) against the output model."""
    if raw is None:
        raise ValueError("the model did not call the required tool")
    data = json.loads(raw) if isinstance(raw, str) else raw
    return model.model_validate(data)
