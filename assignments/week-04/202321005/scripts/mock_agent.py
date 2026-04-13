#!/usr/bin/env python3
"""
Deterministic stand-in for a coding CLI. Simulates slow learning: two no-op
attempts per task, then applies the correct patch on the third try (unless
already fixed on disk after git reset).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "calculator.py"
STATE = ROOT / "state" / "state.json"

CODE_V0 = '''"""Buggy starter implementation — Ralph loop / mock agent will repair."""

from __future__ import annotations


def divide(a: float, b: float) -> float:
    # Bug: no zero guard (tests expect ValueError)
    return a / b


def fibonacci(n: int) -> int:
    # Bug: wrong for n >= 2 (breaks fib(10)==55)
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return n + fibonacci(n - 1)


def clamp(value: float, low: float, high: float) -> float:
    # Bug: not implemented (Task 3)
    raise NotImplementedError("clamp")
'''

CODE_V1 = '''"""After Task 1 — divide fixed."""

from __future__ import annotations


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return a / b


def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return n + fibonacci(n - 1)


def clamp(value: float, low: float, high: float) -> float:
    raise NotImplementedError("clamp")
'''

CODE_V2 = '''"""After Task 2 — fibonacci fixed (iterative)."""

from __future__ import annotations


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return a / b


def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a_i, b_i = 0, 1
    for _ in range(2, n + 1):
        a_i, b_i = b_i, a_i + b_i
    return b_i


def clamp(value: float, low: float, high: float) -> float:
    raise NotImplementedError("clamp")
'''

CODE_V3 = '''"""After Task 3 — clamp added."""

from __future__ import annotations


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return a / b


def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a_i, b_i = 0, 1
    for _ in range(2, n + 1):
        a_i, b_i = b_i, a_i + b_i
    return b_i


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
'''


def load_state() -> dict:
    if not STATE.is_file():
        return {"current_task": 1, "failures_on_task": 0, "global_iteration": 0}
    return json.loads(STATE.read_text(encoding="utf-8"))


def main() -> None:
    st = load_state()
    task = int(st.get("current_task", 1))
    fails = int(st.get("failures_on_task", 0))
    shard = (ROOT / "state" / "task_shard.txt").is_file()

    # Task 1: three failing attempts, then harness enables "stuck split" (shard);
    # on the next call failures_on_task is 3 and shard exists → apply fix.
    # Tasks 2–3: two failures then fix (no shard required).
    if task == 1:
        should_fix = shard and fails >= 3
    else:
        should_fix = fails >= 2

    if task == 1:
        body = CODE_V1 if should_fix else CODE_V0
    elif task == 2:
        body = CODE_V2 if should_fix else CODE_V1
    elif task == 3:
        body = CODE_V3 if should_fix else CODE_V2
    else:
        body = CODE_V3

    SRC.write_text(body, encoding="utf-8")
    action = "apply_fix" if should_fix else "noop_explore"
    print(f"[mock_agent] task={task} failures_on_task={fails} shard={shard} action={action}", file=sys.stderr)


if __name__ == "__main__":
    main()
