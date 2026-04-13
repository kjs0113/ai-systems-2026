# AGENTS.md — accumulated harness / agent learning

This file is **append-only during the Ralph loop**. Each failing iteration adds pytest context so the next agent call (live CLI or mock) can align with what the backpressure layer observed.

## Baseline (iteration 0)

- The repository starts from a deliberately broken `src/calculator.py`.
- Backpressure is enforced by pytest; the harness performs **garbage collection** by restoring `src/calculator.py` from the last good checkpoint after every failure.
- Stuck detection may add `state/task_shard.txt` to force a smaller edit surface when failures repeat.

---

<!-- Below: appended automatically by harness.sh on failures, and on task success. -->

## Loop 1 — task 1 failure
Timestamp: 2026-04-12T23:33:41+09:00

### Pytest tail
```text
.F                                                                       [100%]
=================================== FAILURES ===================================
_______________________________ test_divide_zero _______________________________

    def test_divide_zero():
        with pytest.raises(ValueError, match="0으로 나눌 수 없습니다"):
>           divide(10, 0)

tests/test_task1_divide.py:12: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

a = 10, b = 0

    def divide(a: float, b: float) -> float:
        # Bug: no zero guard (tests expect ValueError)
>       return a / b
               ^^^^^
E       ZeroDivisionError: division by zero

src/calculator.py:8: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_task1_divide.py::test_divide_zero - ZeroDivisionError: divi...
1 failed, 1 passed in 0.01s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Loop 2 — task 1 failure
Timestamp: 2026-04-12T23:33:43+09:00

### Pytest tail
```text
.F                                                                       [100%]
=================================== FAILURES ===================================
_______________________________ test_divide_zero _______________________________

    def test_divide_zero():
        with pytest.raises(ValueError, match="0으로 나눌 수 없습니다"):
>           divide(10, 0)

tests/test_task1_divide.py:12: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

a = 10, b = 0

    def divide(a: float, b: float) -> float:
        # Bug: no zero guard (tests expect ValueError)
>       return a / b
               ^^^^^
E       ZeroDivisionError: division by zero

src/calculator.py:8: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_task1_divide.py::test_divide_zero - ZeroDivisionError: divi...
1 failed, 1 passed in 0.02s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Loop 3 — task 1 failure
Timestamp: 2026-04-12T23:33:46+09:00

### Pytest tail
```text
.F                                                                       [100%]
=================================== FAILURES ===================================
_______________________________ test_divide_zero _______________________________

    def test_divide_zero():
        with pytest.raises(ValueError, match="0으로 나눌 수 없습니다"):
>           divide(10, 0)

tests/test_task1_divide.py:12: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

a = 10, b = 0

    def divide(a: float, b: float) -> float:
        # Bug: no zero guard (tests expect ValueError)
>       return a / b
               ^^^^^
E       ZeroDivisionError: division by zero

src/calculator.py:8: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_task1_divide.py::test_divide_zero - ZeroDivisionError: divi...
1 failed, 1 passed in 0.02s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Task 1 completed at global iteration 4
- Pytest for this stage is green; carry regressions forward.

## Loop 5 — task 2 failure
Timestamp: 2026-04-12T23:33:51+09:00

### Pytest tail
```text
..F                                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_fibonacci_base_and_10 __________________________

    def test_fibonacci_base_and_10():
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
>       assert fibonacci(2) == 1
E       assert 3 == 1
E        +  where 3 = fibonacci(2)

tests/test_task2_fibonacci.py:7: AssertionError
=========================== short test summary info ============================
FAILED tests/test_task2_fibonacci.py::test_fibonacci_base_and_10 - assert 3 == 1
1 failed, 2 passed in 0.02s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Loop 6 — task 2 failure
Timestamp: 2026-04-12T23:33:53+09:00

### Pytest tail
```text
..F                                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_fibonacci_base_and_10 __________________________

    def test_fibonacci_base_and_10():
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
>       assert fibonacci(2) == 1
E       assert 3 == 1
E        +  where 3 = fibonacci(2)

tests/test_task2_fibonacci.py:7: AssertionError
=========================== short test summary info ============================
FAILED tests/test_task2_fibonacci.py::test_fibonacci_base_and_10 - assert 3 == 1
1 failed, 2 passed in 0.02s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Task 2 completed at global iteration 7
- Pytest for this stage is green; carry regressions forward.

## Loop 8 — task 3 failure
Timestamp: 2026-04-12T23:33:57+09:00

### Pytest tail
```text
...FFF                                                                   [100%]
=================================== FAILURES ===================================
______________________________ test_clamp_inside _______________________________

    def test_clamp_inside():
>       assert clamp(5.0, 0.0, 10.0) == 5.0
               ^^^^^^^^^^^^^^^^^^^^^

tests/test_task3_clamp.py:5: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = 5.0, low = 0.0, high = 10.0

    def clamp(value: float, low: float, high: float) -> float:
>       raise NotImplementedError("clamp")
E       NotImplementedError: clamp

src/calculator.py:24: NotImplementedError
_______________________________ test_clamp_below _______________________________

    def test_clamp_below():
>       assert clamp(-3.0, 0.0, 10.0) == 0.0
               ^^^^^^^^^^^^^^^^^^^^^^

tests/test_task3_clamp.py:9: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = -3.0, low = 0.0, high = 10.0

    def clamp(value: float, low: float, high: float) -> float:
>       raise NotImplementedError("clamp")
E       NotImplementedError: clamp

src/calculator.py:24: NotImplementedError
_______________________________ test_clamp_above _______________________________

    def test_clamp_above():
>       assert clamp(99.0, 0.0, 10.0) == 10.0
               ^^^^^^^^^^^^^^^^^^^^^^

tests/test_task3_clamp.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = 99.0, low = 0.0, high = 10.0

    def clamp(value: float, low: float, high: float) -> float:
>       raise NotImplementedError("clamp")
E       NotImplementedError: clamp

src/calculator.py:24: NotImplementedError
=========================== short test summary info ============================
FAILED tests/test_task3_clamp.py::test_clamp_inside - NotImplementedError: clamp
FAILED tests/test_task3_clamp.py::test_clamp_below - NotImplementedError: clamp
FAILED tests/test_task3_clamp.py::test_clamp_above - NotImplementedError: clamp
3 failed, 3 passed in 0.02s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Loop 9 — task 3 failure
Timestamp: 2026-04-12T23:33:59+09:00

### Pytest tail
```text
...FFF                                                                   [100%]
=================================== FAILURES ===================================
______________________________ test_clamp_inside _______________________________

    def test_clamp_inside():
>       assert clamp(5.0, 0.0, 10.0) == 5.0
               ^^^^^^^^^^^^^^^^^^^^^

tests/test_task3_clamp.py:5: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = 5.0, low = 0.0, high = 10.0

    def clamp(value: float, low: float, high: float) -> float:
>       raise NotImplementedError("clamp")
E       NotImplementedError: clamp

src/calculator.py:24: NotImplementedError
_______________________________ test_clamp_below _______________________________

    def test_clamp_below():
>       assert clamp(-3.0, 0.0, 10.0) == 0.0
               ^^^^^^^^^^^^^^^^^^^^^^

tests/test_task3_clamp.py:9: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = -3.0, low = 0.0, high = 10.0

    def clamp(value: float, low: float, high: float) -> float:
>       raise NotImplementedError("clamp")
E       NotImplementedError: clamp

src/calculator.py:24: NotImplementedError
_______________________________ test_clamp_above _______________________________

    def test_clamp_above():
>       assert clamp(99.0, 0.0, 10.0) == 10.0
               ^^^^^^^^^^^^^^^^^^^^^^

tests/test_task3_clamp.py:13: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

value = 99.0, low = 0.0, high = 10.0

    def clamp(value: float, low: float, high: float) -> float:
>       raise NotImplementedError("clamp")
E       NotImplementedError: clamp

src/calculator.py:24: NotImplementedError
=========================== short test summary info ============================
FAILED tests/test_task3_clamp.py::test_clamp_inside - NotImplementedError: clamp
FAILED tests/test_task3_clamp.py::test_clamp_below - NotImplementedError: clamp
FAILED tests/test_task3_clamp.py::test_clamp_above - NotImplementedError: clamp
3 failed, 3 passed in 0.02s
```

### Takeaway for next attempt
- Re-read failing assertion names and match them to a single function change.
- Keep edits minimal; do not modify files under tests/.

## Task 3 completed at global iteration 10
- Pytest for this stage is green; carry regressions forward.
