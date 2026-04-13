#!/usr/bin/env python3
"""
autoresearch.py — v0 BROKEN
버그: JSON 출력 스키마에 'improved' 키가 누락됨.
VALIDATE 단계에서 KeyError / falsy 반환으로 실패 유발.
"""
import argparse
import json
import os
import time
import random


def bubble_sort(arr):
    a = arr[:]
    n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


def timsort(arr):
    return sorted(arr)


def benchmark(fn, data, repeat=5):
    times = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(data[:])
        times.append(time.perf_counter() - t0)
    return min(times)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--budget", type=float, default=30.0)
    parser.add_argument("--output", default="loop_results.json")
    args = parser.parse_args()

    random.seed(42)
    data = [random.randint(0, 10_000) for _ in range(1_000)]

    baseline_sec = benchmark(bubble_sort, data)
    optimized_sec = benchmark(timsort, data)
    speedup = round(baseline_sec / optimized_sec, 1)

    existing = {}
    if os.path.exists(args.output):
        try:
            with open(args.output) as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    # BUG: 'improved' 키 의도적으로 누락 — VALIDATE sys.exit(1) 유발
    existing[args.task] = {
        "baseline_sec": round(baseline_sec, 6),
        "optimized_sec": round(optimized_sec, 6),
        "speedup": speedup,
        # "improved": True   ← schema v0에서 누락된 필드
    }

    with open(args.output, "w") as f:
        json.dump(existing, f, indent=2)
    print(json.dumps(existing, indent=2))


if __name__ == "__main__":
    main()
