import pytest
from generated_code import Calculator

def test_add_success():
    calc = Calculator()
    assert calc.add(10, 20) == 30

def test_add_error():
    calc = Calculator()
    with pytest.raises(ValueError, match="결과값이 100을 초과할 수 없습니다."):
        calc.add(60, 50)
