# Role

You are an autonomous coding agent operating inside this lab repository. You may edit **only** `src/calculator.py` (and create scratch files under `scratch/` if needed). **Never** modify anything under `tests/`.

# Global constraints

- Prefer the smallest diff that satisfies the current task’s tests.
- After editing, mentally simulate `pytest` for the active task before finishing your turn.
- If you are unsure, write a short plan to `scratch/plan.md` (optional); the harness may delete `scratch/` on garbage collection.

# Task specifications (minimum three)

## Task 1 — Safe division

- Implement `divide(a, b)` so normal division works and `divide(10, 0)` raises `ValueError` with message containing `0으로 나눌 수 없습니다`.
- Verification: `pytest -q tests/test_task1_divide.py`.

## Task 2 — Correct Fibonacci

- Implement `fibonacci(n)` for `n >= 0` with `fibonacci(0)==0`, `fibonacci(1)==1`, `fibonacci(2)==1`, `fibonacci(5)==5`, `fibonacci(10)==55`.
- Use an iterative O(n) implementation to avoid stack overflow on larger inputs.
- Must keep Task 1 tests green: run `tests/test_task1_divide.py` together with `tests/test_task2_fibonacci.py`.

## Task 3 — Numeric clamp

- Implement `clamp(value, low, high)` returning `value` bounded to `[low, high]` (inclusive).
- Keep all prior tests green: run the three test modules together.

# Completion criteria (per task)

The harness decides pass/fail by running pytest for the active stage. When all three stages pass, the loop exits successfully.

# Working notes

- Read `AGENTS.md` before coding: it accumulates **prior failure signatures** and takeaways from earlier loop iterations.
- If `state/task_shard.txt` exists, treat it as a **narrowed sub-task** emitted by stuck detection — satisfy it first.
