import pytest
from src.calculator import divide, fibonacci

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_zero():
    with pytest.raises(ValueError, match="0으로 나눌 수 없습니다"):
        divide(10, 0)

def test_fibonacci():
    assert fibonacci(10) == 55
    assert fibonacci(0) == 0