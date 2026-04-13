def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return a / b


def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
