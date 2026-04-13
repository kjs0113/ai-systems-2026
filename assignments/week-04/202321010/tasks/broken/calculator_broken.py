"""calculator.py — v0 BROKEN
버그: 0 나누기 시 예외를 발생시키지 않고 0을 반환.
test_divide_by_zero: assertRaises(ZeroDivisionError) → FAIL (예외 없음)
VALIDATE: 'ZeroDivisionError'/'if b == 0' 문자열 부재 → FAIL
"""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    # BUG: b==0 일 때 예외 발생 대신 0 반환 — ZeroDivisionError 숨김
    return a / b if b else 0

