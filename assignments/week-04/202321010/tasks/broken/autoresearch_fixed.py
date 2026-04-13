#!/usr/bin/env python3
"""
autoresearch.py — v1 FIXED
schema v1.1: 'improved' 키 포함. REPAIR에 의해 복원되는 버전.
이 파일은 tasks/broken/autoresearch_fixed.py로 보관되며,
harness.sh의 REPAIR 단계에서 autoresearch.py를 이 버전으로 교체합니다.
"""

import argparse
import json
import os
import time
import statistics
from typing import Callable, Any


def bubble_sort(arr: list) -> list:
    a = arr[:]
    n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


def insertion_sort(arr: list) -> list:
    a = arr[:]
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def timsort(arr: list) -> list:
    return sorted(arr)


SORT_CANDIDATES: list[tuple[str, Callable]] = [
    ("bubble_sort",    bubble_sort),
    ("insertion_sort", insertion_sort),
    ("timsort",        timsort),
]


def benchmark(func: Callable, data: list, repeat: int = 5) -> float:
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        func(data[:])
        times.append(time.perf_counter() - t0)
    return min(times)


def task_optimize_sort(budget: float) -> dict:
    import random
    random.seed(42)
    N = 1000
    data = [random.randint(0, 10_000) for _ in range(N)]

    deadline = time.time() + budget
    results: dict[str, Any] = {"improved": False}  # FIX: 'improved' 키 항상 포함

    baseline_name, baseline_fn = SORT_CANDIDATES[0]
    print(f"[autoresearch] Iteration 1/∞ — testing {baseline_name} baseline...")
    baseline_sec = benchmark(baseline_fn, data)
    print(f"  baseline time (n={N}): {baseline_sec:.4f}s")
    results["baseline_name"] = baseline_name
    results["baseline_sec"] = round(baseline_sec, 6)

    best_sec = baseline_sec
    iteration = 2

    for candidate_name, candidate_fn in SORT_CANDIDATES[1:]:
        if time.time() >= deadline:
            print("[autoresearch] Budget exhausted.")
            break
        print(f"[autoresearch] Iteration {iteration}/∞ — applying {candidate_name}...")
        cand_sec = benchmark(candidate_fn, data)
        print(f"  optimized time (n={N}): {cand_sec:.6f}s")
        if cand_sec < best_sec:
            best_sec = cand_sec
            results["improved"] = True
            speedup = round(baseline_sec / cand_sec, 1)
            print(f"[autoresearch] Speedup: {speedup}x — threshold met.")
            results["speedup"] = speedup
            results["optimized_name"] = candidate_name
            results["optimized_sec"] = round(best_sec, 6)
        iteration += 1

    return results


def task_long_doc(budget: float) -> dict:
    import re
    from collections import Counter
    import random

    deadline = time.time() + budget
    words_pool = ["function", "class", "return", "import", "def", "for", "while",
                  "if", "else", "try", "except", "with", "yield", "lambda", "async",
                  "await", "type", "list", "dict", "tuple", "set", "str", "int"]
    random.seed(0)
    document = " ".join(random.choice(words_pool) for _ in range(5_000))
    chunks = [document[i:i+500] for i in range(0, len(document), 500)]

    accumulated: Counter = Counter()
    idx = 0
    for idx, chunk in enumerate(chunks):
        if time.time() >= deadline:
            break
        tokens = re.findall(r'\w+', chunk.lower())
        accumulated.update(Counter(tokens))
        if (idx + 1) % 3 == 0:
            threshold = max(1, len(accumulated) // 20)
            for k in [k for k, v in accumulated.items() if v < threshold]:
                del accumulated[k]

    top10 = accumulated.most_common(10)
    return {
        "improved": True,
        "top10_words": [{"word": w, "count": c} for w, c in top10],
        "chunks_processed": idx + 1,
    }


TASK_REGISTRY: dict[str, Callable[[float], dict]] = {
    "optimize_sort": task_optimize_sort,
    "long_doc":      task_long_doc,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True,
                        choices=list(TASK_REGISTRY.keys()) + ["all"])
    parser.add_argument("--budget", type=float, default=30.0)
    parser.add_argument("--output", default="loop_results.json")
    args = parser.parse_args()

    tasks_to_run = list(TASK_REGISTRY.keys()) if args.task == "all" else [args.task]
    existing: dict = {}
    if os.path.exists(args.output):
        try:
            with open(args.output) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}

    per_task_budget = args.budget / len(tasks_to_run)
    for task_name in tasks_to_run:
        print(f"\n=== autoresearch.py ===")
        print(f"[autoresearch] Starting task: {task_name} | budget: {per_task_budget:.1f}s")
        existing[task_name] = TASK_REGISTRY[task_name](per_task_budget)

    with open(args.output, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"\n[autoresearch] Writing results to {args.output}...")
    print(json.dumps(existing, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
