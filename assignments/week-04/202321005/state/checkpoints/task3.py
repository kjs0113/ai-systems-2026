"""After Task 3 — clamp added."""

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
