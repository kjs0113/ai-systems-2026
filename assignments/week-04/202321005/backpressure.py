#!/usr/bin/env python3
"""
Backpressure helpers: stall detection, progress probe, autoresearch (bonus),
and a tiny RLM-style chunk reducer (bonus).
"""

from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def check_progress(log_file: str = "loop_log.txt") -> dict[str, Any]:
    """Summarize recent harness output for stall / health signals."""
    path = Path(log_file)
    if not path.is_file():
        return {
            "total_iterations": 0,
            "last_10_lines": [],
            "is_stalled": False,
        }
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    iterations = [ln for ln in lines if "이터레이션" in ln or "iteration" in ln.lower()]
    return {
        "total_iterations": len(iterations),
        "last_10_lines": lines[-10:],
        "is_stalled": detect_stall(lines),
    }


def detect_stall(lines: list[str], window: int = 40) -> bool:
    """True if the same failure line repeats many times (no new signal)."""
    recent = lines[-window:]
    error_lines = [
        ln
        for ln in recent
        if any(k in ln for k in ("FAILED", "ERROR", "AssertionError", "미통과"))
    ]
    if len(error_lines) < 4:
        return False
    norm = [re.sub(r"\d+", "#", ln) for ln in error_lines]
    counts: dict[str, int] = {}
    for ln in norm:
        counts[ln] = counts.get(ln, 0) + 1
    top = max(counts.values())
    return top >= 4


def autoresearch_optimize(
    score_fn: Callable[[float], float],
    low: float,
    high: float,
    budget_sec: float = 2.0,
    samples: int = 200,
) -> tuple[float, float]:
    """
    Bonus: micro autoresearch — random search within a fixed wall-clock budget.
    Minimizes score_fn(x).  No gradients; mirrors "test-time search" over actions.
    """
    rng = random.Random(42)
    deadline = time.perf_counter() + budget_sec
    best_x = 0.5 * (low + high)
    best_s = score_fn(best_x)
    trials = 0
    while time.perf_counter() < deadline and trials < samples:
        x = low + (high - low) * rng.random()
        s = score_fn(x)
        trials += 1
        if s < best_s:
            best_s, best_x = s, x
    return best_x, best_s


@dataclass
class ChunkAnswer:
    chunk_id: int
    summary: str
    confidence: float


def rlm_reduce_document(
    text: str,
    max_chunk_chars: int = 120,
    keyword: str = "손실",
) -> str:
    """
    Bonus: Recursive-style reduction without an LLM — extractive "reasoning".
    Splits long text, scores chunks by keyword overlap + length prior,
    merges top chunks (RLM spirit: partition → local read → aggregate).
    """
    text = text.strip()
    if not text:
        return ""
    chunks: list[str] = []
    for i in range(0, len(text), max_chunk_chars):
        chunks.append(text[i : i + max_chunk_chars])

    scored: list[tuple[float, int, str]] = []
    for i, ch in enumerate(chunks):
        hits = ch.lower().count(keyword.lower())
        score = hits * 2.0 + min(len(ch), max_chunk_chars) * 0.01
        scored.append((score, i, ch))
    scored.sort(reverse=True)
    top = [c for _, _, c in scored[:3]]
    merged = "\n---\n".join(top)
    return merged[:2000]


def write_metrics_json(path: str, row: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: list[Any] = []
    if p.is_file():
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                payload = []
        except json.JSONDecodeError:
            payload = []
    payload.append(row)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_stall = sub.add_parser("stall-check", help="Exit 1 if stalled")
    p_stall.add_argument("--log", default="loop_log.txt")

    p_demo = sub.add_parser("autoresearch-demo", help="Demo bounded random search")
    args = ap.parse_args()
    if args.cmd == "stall-check":
        stalled = check_progress(args.log)["is_stalled"]
        raise SystemExit(1 if stalled else 0)
    if args.cmd == "autoresearch-demo":

        def quad(y: float) -> float:
            return (y - 0.37) ** 2

        x, s = autoresearch_optimize(quad, 0.0, 1.0, budget_sec=0.5)
        print(f"best_x={x:.4f} best_score={s:.6f}")
