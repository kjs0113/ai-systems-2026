"""After Task 1 — divide fixed."""

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
