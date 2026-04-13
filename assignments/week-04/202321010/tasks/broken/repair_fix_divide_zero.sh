#!/usr/bin/env bash
# repair_fix_divide_zero.sh — 단일 단계 repair
#
# 진단: tasks/calculator.py(v0)는 b==0일 때 예외를 발생시키지 않고 0을 반환
#   → test_divide_by_zero: assertRaises(ZeroDivisionError) → AssertionError (예외 미발생)
#   → VALIDATE: 소스에 'ZeroDivisionError'/'if b == 0' 문자열 없음
# 수정: calculator_fixed.py(v1)으로 교체 — if b == 0: raise ZeroDivisionError(...)

set -euo pipefail

cat > .repair_rationale.txt <<'RATIONALE'
**Root cause (fix_divide_zero):**
- `tasks/calculator.py` (v0): `def divide(a, b): return a / b if b else 0`
  - b==0 시 예외 없이 0 반환 — ZeroDivisionError를 숨김
  - `test_divide_by_zero`: `assertRaises(ZeroDivisionError)` → AssertionError (예외 안 뜸)
  - VALIDATE AST 검사: 소스에 `ZeroDivisionError` 또는 `if b == 0` 문자열 없음 → 실패

**Repair action:**
- `tasks/calculator.py` → v1으로 교체
  - `if b == 0: raise ZeroDivisionError("division by zero is not allowed")`
  - 방어 분기 삽입으로 테스트 및 정적 분석 모두 통과 예상

**Guard rule 적용 (Rules v1.0 참조):**
- "코드 패치 후 반드시 AST 또는 grep으로 방어 분기 삽입 여부 검증"
- VALIDATE에서 `ZeroDivisionError` 문자열 grep으로 삽입 확인
RATIONALE

cp tasks/broken/calculator_fixed.py tasks/calculator.py
echo '[repair] tasks/calculator.py → v1 (ZeroDivisionError guard: if b == 0: raise ZeroDivisionError)'
