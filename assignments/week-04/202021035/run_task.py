#!/usr/bin/env python3
"""
Helper script for the Lab 04 harness.

`run_task.py` simulates the behaviour of an AI agent attempting to
complete a given task.  It accepts two positional arguments:

  1. The numeric task identifier.
  2. The iteration number of the harness loop.

Based on these inputs the script deliberately fails certain tasks in
early iterations to illustrate the Ralph pattern of learning from
failure.  Later iterations succeed, mimicking how an agent improves
after incorporating feedback from prior runs.

The script prints a short diagnostic message indicating whether the
task succeeded or failed, then exits with a zero status for
success and a non‑zero status for failure.
"""

import sys
from typing import Tuple


def main(args: Tuple[str, ...]) -> int:
    if len(args) < 2:
        print("Usage: run_task.py <task_id> <iteration>")
        return 1
    try:
        task_id = int(args[0])
        iteration = int(args[1])
    except ValueError:
        print("task_id and iteration must be integers")
        return 1

    # Simulate failure conditions for specific tasks during early
    # iterations.  These rules intentionally cause at least two
    # failures across the three defined tasks before all succeed.
    should_fail = False
    if task_id == 1 and iteration < 2:
        # Fibonacci implementation fails in the first iteration.
        should_fail = True
    elif task_id == 2 and iteration < 3:
        # is_prime implementation fails in the first two iterations.
        should_fail = True

    if should_fail:
        print(f"Task {task_id} failed in iteration {iteration}: simulated error condition")
        return 1

    # Success path for all other cases.
    print(f"Task {task_id} succeeded in iteration {iteration}: simulated completion")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))