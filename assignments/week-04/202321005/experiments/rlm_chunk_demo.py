#!/usr/bin/env python3
"""Bonus: extractive long-document reduction (RLM-style) using backpressure.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backpressure import rlm_reduce_document  # noqa: E402


def main() -> None:
    sample = Path(__file__).with_name("sample_long_ko.txt").read_text(encoding="utf-8")
    out = rlm_reduce_document(sample, max_chunk_chars=100, keyword="손실")
    print("--- reduced excerpt ---")
    print(out[:1500])


if __name__ == "__main__":
    main()
