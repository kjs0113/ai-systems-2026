"""test_calculator.py — calculator.py 단위 테스트"""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tasks.calculator import add, subtract, multiply, divide


class TestCalculator(unittest.TestCase):

    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)

    def test_subtract(self):
        self.assertEqual(subtract(10, 4), 6)

    def test_multiply(self):
        self.assertEqual(multiply(3, 4), 12)

    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            divide(10, 0)

    def test_divide_normal(self):
        self.assertAlmostEqual(divide(10, 4), 2.5)


if __name__ == "__main__":
    unittest.main()
