"""calculator.py — v1 FIXED: ZeroDivisionError guard 추가.
harness.sh REPAIR 단계에서 tasks/calculator.py를 이 버전으로 교체합니다.
"""


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("division by zero is not allowed")
    return a / b
