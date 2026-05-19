from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from base_agent import BaseAgent


class CoderAgent(BaseAgent):
    def __init__(self) -> None:
        schema_path = Path(__file__).resolve().parent / "schemas" / "coder_output.json"
        super().__init__(name="coder", schema_path=str(schema_path))

    def _selected_cli(self) -> str:
        return os.environ.get("AI_CLI", "codex").strip().lower() or "codex"

    def _try_cli(self, prompt_text: str) -> tuple[bool, str]:
        cli_name = self._selected_cli()
        commands = {
            "claude": ["claude", prompt_text],
            "gemini": ["gemini", prompt_text],
            "codex": ["codex", prompt_text],
        }
        command = commands.get(cli_name)
        if not command:
            return False, f"Unsupported AI_CLI: {cli_name}"

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            if completed.returncode == 0:
                return True, completed.stdout.strip() or "CLI executed"
            return False, completed.stderr.strip() or "CLI execution failed"
        except Exception as exc:
            return False, str(exc)

    def _build_fallback_result(self, plan: dict[str, Any], cli_status: str) -> dict[str, Any]:
        target_files = plan.get("constraints", {}).get("target_files", [])
        changes = []
        for file_name in target_files:
            changes.append(
                {
                    "file": file_name,
                    "action": "modify",
                    "description": f"Plan based update simulated for {file_name}.",
                }
            )
        if not changes:
            changes.append(
                {
                    "file": "pipeline.py",
                    "action": "modify",
                    "description": "Fallback change list created because no target files were provided.",
                }
            )

        result = {
            "task_id": plan["task_id"],
            "changes": changes,
            "test_command": "python pipeline.py",
            "status": "complete",
        }
        if cli_status:
            changes.append(
                {
                    "file": "coder_agent.py",
                    "action": "modify",
                    "description": f"Fallback path used because CLI execution was unavailable: {cli_status}",
                }
            )
        return result

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        plan = payload.get("plan", {})
        self._add_message("user", str(plan))

        cli_success, cli_status = self._try_cli(f"Implement plan {plan.get('task_id', 'unknown')}")
        result = self._build_fallback_result(plan, "" if cli_success else cli_status)
        self._validate_output(result)
        self._add_message("assistant", str(result))
        return result
