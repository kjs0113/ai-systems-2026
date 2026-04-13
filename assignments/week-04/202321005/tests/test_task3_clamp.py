from src.calculator import clamp


def test_clamp_inside():
    assert clamp(5.0, 0.0, 10.0) == 5.0


def test_clamp_below():
    assert clamp(-3.0, 0.0, 10.0) == 0.0


def test_clamp_above():
    assert clamp(99.0, 0.0, 10.0) == 10.0
