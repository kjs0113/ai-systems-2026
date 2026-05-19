from __future__ import annotations

import json
from pathlib import Path

from coder_agent import CoderAgent
from planner_agent import PlannerAgent


def build_codebase_summary(base_dir: Path) -> str:
    files = sorted(path.name for path in base_dir.iterdir() if path.is_file())
    return ", ".join(files)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    planner = PlannerAgent()
    planner_input = {
        "objective": "Design and run a simple Planner to Coder multi-agent pipeline.",
        "codebase_summary": build_codebase_summary(base_dir),
    }
    plan = planner.run(planner_input)

    coder = CoderAgent()
    coder_result = coder.run({"plan": plan})

    print("=== Planner Result ===")
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    print()
    print("=== Coder Result ===")
    print(json.dumps(coder_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
