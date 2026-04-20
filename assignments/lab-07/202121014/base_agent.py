from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

try:
    from jsonschema import validate as jsonschema_validate  # type: ignore
except Exception:
    jsonschema_validate = None


class BaseAgent(ABC):
    def __init__(self, name: str, schema_path: str) -> None:
        self.name = name
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.messages: list[dict[str, str]] = []

    def _load_schema(self) -> dict[str, Any]:
        return json.loads(self.schema_path.read_text(encoding="utf-8"))

    def _extract_json(self, text: str) -> dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return json.loads(stripped)

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and start < end:
            return json.loads(stripped[start : end + 1])
        raise ValueError("Could not extract JSON from response.")

    def _validate_output(self, output_data: dict[str, Any]) -> None:
        if jsonschema_validate is not None:
            jsonschema_validate(instance=output_data, schema=self.schema)
            return

        required_fields = self.schema.get("required", [])
        for field_name in required_fields:
            if field_name not in output_data:
                raise ValueError(f"Missing required field: {field_name}")

    def _add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def _get_api_key(self) -> str:
        return os.environ.get("ANTHROPIC_API_KEY", "").strip()

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
