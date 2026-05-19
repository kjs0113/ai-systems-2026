from __future__ import annotations

from pathlib import Path
from typing import Any

from base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self) -> None:
        schema_path = Path(__file__).resolve().parent / "schemas" / "planner_output.json"
        super().__init__(name="planner", schema_path=str(schema_path))

    def _build_fallback_plan(self, objective: str, codebase_summary: str) -> dict[str, Any]:
        target_files = []
        if "base_agent.py" in codebase_summary:
            target_files.append("base_agent.py")
        if "planner_agent.py" in codebase_summary:
            target_files.append("planner_agent.py")
        if "coder_agent.py" in codebase_summary:
            target_files.append("coder_agent.py")
        if not target_files:
            target_files = ["pipeline.py", "planner_agent.py", "coder_agent.py"]

        return {
            "task_id": "task-0001",
            "objective": objective,
            "subtasks": [
                {
                    "id": "subtask-1",
                    "description": "관련 파일과 현재 코드 구조를 조사한다.",
                    "assignee": "researcher",
                    "depends_on": [],
                },
                {
                    "id": "subtask-2",
                    "description": "필요한 코드 파일을 작성하거나 수정한다.",
                    "assignee": "coder",
                    "depends_on": ["subtask-1"],
                },
                {
                    "id": "subtask-3",
                    "description": "실행 명령과 테스트 가능 여부를 점검한다.",
                    "assignee": "qa",
                    "depends_on": ["subtask-2"],
                },
                {
                    "id": "subtask-4",
                    "description": "최종 산출물과 제한 사항을 검토한다.",
                    "assignee": "reviewer",
                    "depends_on": ["subtask-3"],
                },
            ],
            "constraints": {
                "max_iterations": 3,
                "forbidden_packages": ["unapproved-external-packages"],
                "target_files": target_files,
            },
        }

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        objective = str(payload.get("objective", "")).strip()
        codebase_summary = str(payload.get("codebase_summary", "")).strip()

        self._add_message("user", f"objective={objective}")
        self._add_message("user", f"codebase_summary={codebase_summary}")

        plan = self._build_fallback_plan(objective, codebase_summary)
        self._validate_output(plan)
        self._add_message("assistant", str(plan))
        return plan
