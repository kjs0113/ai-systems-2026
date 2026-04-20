# Lab-06 Prompt Improvement and A/B Test

## Overview

This directory contains a small Lab-06 workflow for analyzing the bundled `harness.log`, extracting repeated failure patterns, and comparing two prompt versions against those patterns.

Files:
- `log_analyzer.py`: classifies recurring log error patterns and writes `error_report.md`
- `prompt_v1.md`: baseline prompt
- `prompt_v2.md`: improved prompt based on observed failures
- `ab_test.py`: compares the two prompts and writes `ab_results.json`
- `harness.log`: bundled reference log used by this lab only
- `error_report.md`: generated markdown report
- `ab_results.json`: generated A/B comparison result

## How To Run

```bash
python ab_test.py
```

This command:
- analyzes the local `harness.log`
- refreshes `error_report.md`
- compares `prompt_v1.md` and `prompt_v2.md`
- writes `ab_results.json`

You can also run the analyzer separately:

```bash
python log_analyzer.py
```

## Error Patterns Found

The analyzer classifies the log into the assignment categories:
- `syntax`: corrupted text or mojibake that makes matching fragile
- `logic`: real failing test behavior such as wrong exception handling
- `timeout`: long-running or timeout signals
- `api`: tool router failures and patch verification failures
- `other`: warnings and miscellaneous non-blocking issues

Based on the bundled `harness.log`, the dominant issues are `logic`, `api`, `syntax`, and `other`. `timeout` is configured but not prominent in the observed run.

## V2 Improvements Over V1

- V1 is generic and only says to fix the failing code with minimal changes.
- V2 starts with `pytest tests/ -q --tb=short` so the latest failure is confirmed before editing.
- V2 limits reading scope to failing test related files instead of scanning broadly.
- V2 adds an explicit read order: instructions first, then source and tests, then failure confirmation.
- V2 tells the agent how to recover when `apply_patch` fails because the file contents do not match.
- V2 handles corrupted or non-ASCII text more safely by preferring smaller rewrites over brittle matching.
- V2 preserves exact exception type and message behavior, which directly matches the observed test sensitivity in the log.
- V2 separates warnings from primary failures so the repair loop stays focused.
- V2 adds an escalation rule to write `fix_plan.md` after the same error repeats twice.
- V2 requires `DONE.md` after completion.

## A/B Result Interpretation

`ab_results.json` stores per-variant results with:
- `variant`
- `iterations`
- `success`
- `duration_sec`
- `final_test_output`

The current interpretation is:
- `prompt_v1` behaves like a baseline and needs more retries because it lacks explicit retry and containment guidance.
- `prompt_v2` is the winner because it succeeds with fewer iterations and a shorter total duration while producing a passing final test output.

Generated outputs intentionally store relative filenames such as `harness.log` and `error_report.md` instead of local absolute paths, so the submission stays portable.

## Why V2 Wins

- It validates the failure first with a concrete pytest command.
- It narrows file reads to the failing area, reducing unnecessary edits.
- It keeps the repair minimal while still handling repeated patch failures and corrupted text.
- It includes an explicit fallback rule after repeated identical errors.
- It defines the completion artifact (`DONE.md`) clearly, so the workflow is less ambiguous.

## Additional Improvement Proposals

- `prompt_v3` could require quoting the exact failing test name and error line before any edit.
- `prompt_v3` could require a one-line root cause statement before the first patch attempt.
- `prompt_v3` could separate retry policies for logic failures vs. patch/API failures.
- `prompt_v3` could require logging the chosen repair strategy after each failed iteration.
- `prompt_v3` could add a stronger stop condition when warnings are unrelated to the failing behavior.
