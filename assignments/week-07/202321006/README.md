# Week 07: Multi-Agent SDLC Design
Student ID: 202321006

## 1. Project Overview
This project defines a structured multi-agent pipeline for the Software Development Life Cycle (SDLC), shifting from natural language communication to deterministic, artifact-based handoffs.

## 2. Included Artifacts
- `architecture_diagram.md`: 5-phase gated pipeline with defined roles.
- `dag_analysis.md`: Task dependency decomposition and tiered parallelization strategy.
- `verification_gates.md`: Quality checklists for each phase transition.
- `error_recovery_strategies.md`: Mitigation plans for 3 common failure scenarios.
- `schemas/`:
    - `requirement.json`: Schema for product requirements.
    - `task.json`: Schema for individual developer tasks.
    - `pipeline_state.json`: Schema for global state tracking.
    - `lesson.json`: Schema for knowledge capture.

## 3. Compliance Checklist
- [x] **No .pyc files**: `.gitignore` updated with `__pycache__/` and `*.pyc`.
- [x] **Isolated modification**: Only `assignments/week-07/202321006/` was changed.
- [x] **English filenames**: All files use NFD-safe English names.
- [x] **No Docs intrusion**: Assignment files are kept within the student's folder.
- [x] **Diff validation**: Verified with `git diff --stat origin/main`.
