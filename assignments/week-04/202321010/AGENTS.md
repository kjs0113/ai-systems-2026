# AGENTS.md — Ralph Loop 누적 학습 기록

이 파일은 `harness.sh`가 각 루프 반복마다 자동으로 업데이트하는 학습 저장소입니다.
실패 원인과 적용된 수정 전략이 누적되어, 이후 반복에서 같은 실패를 반복하지 않도록 합니다.

---

## 초기 규칙 (Rules v1.0 — 루프 시작 전 설정)

루프를 시작하기 전에 알려진 실패 패턴과 대응 전략을 미리 기록합니다.

1. **Schema rule:** JSON 결과 파일은 반드시 `{"task_id": {"improved": bool, ...}}` 형식 준수
2. **Guard rule:** 코드 패치 후 반드시 AST 또는 grep으로 방어 분기 삽입 여부 검증
3. **GC rule:** 3회 반복마다 컨텍스트 창을 정리하여 오래된 오류 노이즈 제거
4. **Backpressure rule:** 연속 실패 시 지수 백오프(2^n초, 최대 32초)로 재시도 간격 제어
5. **Stuck rule:** 연속 3회 실패 시 태스크를 더 작은 단위로 분할하여 재시도

---

*이하 항목은 harness.sh가 루프 실행 중 자동으로 추가합니다.*

## Iteration 1 — FAILURE [2026-04-13T15:51:56]
**Task:** `optimize_sort`
**이전 연속 실패 횟수:** 0
**Error:**
```
VALIDATION FAILED for task optimize_sort
```

**Root cause (Iteration 1):**
- `autoresearch.py` schema-v0는 `improved` 키를 결과 딕셔너리에 포함하지 않음
- VALIDATE: `d.get('optimize_sort',{}).get('improved')` → `None` (falsy) → `sys.exit(1)`
- 즉, 코드가 실행되고 speedup도 계산되지만, 결과 직렬화 시 `improved` 필드 누락

**Stage-1 repair action (context_window.txt 참조: 이전 FAIL 기록 수 확인):**
- `autoresearch.py`를 v0.5(partial-fix)로 교체
- v0.5는 `improved` 키를 포함하지만 값이 항상 `False` (실제 비교 로직 없음)
- **다음 단계 전략:** v0.5 실행 후 `improved=False`로 여전히 실패 → v1.1(full-fix) 교체 예정
**Repair applied:** `bash tasks/broken/repair_optimize_sort.sh`

## Iteration 2 — FAILURE [2026-04-13T15:51:58]
**Task:** `optimize_sort`
**이전 연속 실패 횟수:** 1
**Error:**
```
VALIDATION FAILED for task optimize_sort
VALIDATION FAILED for task optimize_sort
```

**Root cause (Iteration 2) — context_window.txt 참조하여 진단:**
- Iteration 1 학습: `improved` 키가 아예 없었음 → stage-1로 v0.5 설치
- 이번 실패 원인: `improved` 값이 `False` → VALIDATE `sys.exit(0 if False else 1)` → 여전히 실패
- 즉, stage-1은 schema 위치를 파악한 것이고, 실제 최적화 비교 로직이 없었음

**Stage-2 repair action (이전 학습 적용):**
- Iteration 1 학습 "schema-v0에 improved 키 없음" → Iteration 2 확인 "improved=False 확인"
- **두 반복의 학습을 결합**: autoresearch.py를 schema-v1.1 (improved 키 보장 + 실제 timsort 비교)로 교체
- loop_results.json 초기화하여 v1.1이 새 결과를 올바르게 작성하도록 함

**Context window 활용:** 이전 FAIL 기록 수(1)를 읽어 stage-2 실행 결정
**Repair applied:** `bash tasks/broken/repair_optimize_sort.sh`

## Iteration 3 — SUCCESS [2026-04-13T15:52:02]
**Task:** `optimize_sort`
**이전 실패 횟수:** 2
**Result:** 2회 실패 후 REPAIR 반영 → 성공 (학습 적용 확인).
**학습 반영 증거:**
- context_window.txt에서 이전 FAIL 반복 [1,2] 확인
- 각 반복의 실패 원인 분석 → repair 스크립트가 context 참조하여 단계적 REPAIR 적용
- 최종 REPAIR 결과가 이번 VALIDATE 통과에 직접 반영됨
**Learning locked in:** 수정 사항 검증 완료. 다음 태스크로 진행.

## Iteration 4 — FAILURE [2026-04-13T15:52:02]
**Task:** `fix_divide_zero`
**이전 연속 실패 횟수:** 0
**Error:**
```
----------------------------------------------------------------------
Ran 5 tests in 0.000s

FAILED (failures=1)
CMD FAILED (exit 1) for task fix_divide_zero
```

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
**Repair applied:** `bash tasks/broken/repair_fix_divide_zero.sh`

## Iteration 5 — SUCCESS [2026-04-13T15:52:04]
**Task:** `fix_divide_zero`
**이전 실패 횟수:** 1
**Result:** 1회 실패 후 REPAIR 반영 → 성공 (학습 적용 확인).
**학습 반영 증거:**
- context_window.txt에서 이전 FAIL 반복 [4] 확인
- 각 반복의 실패 원인 분석 → repair 스크립트가 context 참조하여 단계적 REPAIR 적용
- 최종 REPAIR 결과가 이번 VALIDATE 통과에 직접 반영됨
**Learning locked in:** 수정 사항 검증 완료. 다음 태스크로 진행.

## Iteration 6 — SUCCESS [2026-04-13T15:52:05]
**Task:** `generate_metrics_report`
**이전 실패 횟수:** 0
**Result:** 첫 시도 성공.
**Learning locked in:** 수정 사항 검증 완료. 다음 태스크로 진행.

## Iteration 7 — SUCCESS [2026-04-13T15:52:05]
**Task:** `autoresearch_demo`
**이전 실패 횟수:** 0
**Result:** 첫 시도 성공.
**Learning locked in:** 수정 사항 검증 완료. 다음 태스크로 진행.

## Iteration 8 — SUCCESS [2026-04-13T15:52:05]
**Task:** `worktree_analysis`
**이전 실패 횟수:** 0
**Result:** 첫 시도 성공.
**Learning locked in:** 수정 사항 검증 완료. 다음 태스크로 진행.
