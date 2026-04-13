#!/usr/bin/env python3
"""
autoresearch.py — v0.5 STAGE-1 PARTIAL FIX
stage-1 repair에 의해 설치됨.
'improved' 키는 포함하지만 하드코딩 False — 실제 최적화 비교 미수행.
VALIDATE: d.get('improve') → False (falsy) → sys.exit(1) → 여전히 실패.
이 버전은 "schema 오류는 수정했으나 로직 오류가 남아 있음"을 보여줌.
"""
import argparse, json, os, time, random


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--budget", type=float, default=30.0)
    parser.add_argument("--output", default="loop_results.json")
    args = parser.parse_args()

    random.seed(42)
    data = [random.randint(0, 10_000) for _ in range(1_000)]

    def benchmark(fn, repeat=5):
        times = []
        for _ in range(repeat):
            t0 = time.perf_counter()
            fn(data[:])
            times.append(time.perf_counter() - t0)
        return min(times)

    baseline_sec = benchmark(lambda a: sorted(range(len(a))))  # wrong baseline
    speedup = 1.0  # no actual comparison performed

    existing = {}
    if os.path.exists(args.output):
        try:
            with open(args.output) as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    # PARTIAL FIX: 'improved' 키는 추가했지만 값이 False (최적화 비교 미수행)
    existing[args.task] = {
        "improved": False,          # ← key exists but value wrong; VALIDATE still fails
        "baseline_sec": round(baseline_sec, 6),
        "speedup": speedup,
        "_stage": "v0.5-partial-fix",
    }

    with open(args.output, "w") as f:
        json.dump(existing, f, indent=2)
    print(json.dumps(existing, indent=2))


if __name__ == "__main__":
    main()
