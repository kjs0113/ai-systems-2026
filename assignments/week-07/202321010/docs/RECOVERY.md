# 에러 복구 전략 문서

3가지 주요 시나리오별 상세 복구 전략

## 개요

멀티에이전트 시스템에서 발생할 수 있는 주요 에러 시나리오와 각각의 복구 전략을 정의합니다.

### 복구 액션 타입

```python
RecoveryAction:
    - RETRY: 재시도
    - ROLLBACK: 이전 단계로 되돌리기
    - SKIP: 건너뛰기 (조건부 승인)
    - MANUAL: 수동 개입 필요
    - FALLBACK: 대체 방법 사용
```

---

## 시나리오 1: 스키마 불일치

### 상황

Builder Agent가 DraftArtifact를 생성했으나:
- 필수 필드 누락 (예: `content` 필드 없음)
- JSON 파싱 실패
- 타입 오류 (예: `quality_score`가 문자열)

### 탐지

```python
# Pydantic validation error
try:
    artifact = DraftArtifact(**data)
except ValidationError as e:
    # 스키마 불일치 감지
    trigger_recovery("schema_mismatch", context={
        "error_details": str(e),
        "retry_count": 0
    })
```

### 복구 전략

#### Phase 1: 초기 재시도 (retry_count < 2)

```
액션: RETRY
조건: retry_count < 2
방법:
  1. 에러 로그 생성
  2. Builder Agent에 재생성 요청
  3. 에러 상세 내용을 프롬프트에 포함
```

**코드 예시**:
```python
if retry_count < 2:
    return RecoveryResult(
        success=True,
        action=RecoveryAction.RETRY,
        message=f"Retrying (attempt {retry_count + 1}/3)"
    )
```

#### Phase 2: 프롬프트 강화 (retry_count >= 2)

```
액션: RETRY with Hardening
조건: 동일 오류 2회 반복
방법:
  1. 프롬프트에 명시적 스키마 정의 추가
  2. 예시 JSON 포함
  3. 검증 규칙 강조
```

**코드 예시**:
```python
if retry_count >= 2:
    context["prompt_hardening"] = True
    context["schema_example"] = get_schema_example()
    return RecoveryResult(
        success=True,
        action=RecoveryAction.RETRY,
        message="Retrying with enhanced prompt"
    )
```

#### Phase 3: Fallback 템플릿 (retry_count >= 3)

```
액션: FALLBACK
조건: 최대 재시도 횟수 초과
방법:
  1. 사전 정의된 템플릿 사용
  2. 사용 가능한 필드만 채움
  3. 품질 점수 낮게 설정
```

**코드 예시**:
```python
if retry_count >= max_retries:
    fallback_artifact = create_fallback_draft(partial_data)
    return RecoveryResult(
        success=True,
        action=RecoveryAction.FALLBACK,
        message="Using fallback template"
    )
```

### 장점

- ✅ 비용 절감: 불필요한 재생성 방지
- ✅ 점진적 개선: 프롬프트 강화로 성공률 증가
- ✅ 안전망: Fallback으로 완전 실패 방지

### 정책

| retry_count | 액션 | 비고 |
|------------|------|------|
| 0-1 | RETRY | 일반 재시도 |
| 2 | RETRY + Hardening | 프롬프트 강화 |
| 3+ | FALLBACK | 템플릿 사용 |

---

## 시나리오 2: 상충된 컨텍스트

### 상황

Context Agent가 서로 모순되는 제약을 수집:
- "길이는 짧게" vs "반드시 상세하게"
- "빠르게 완성" vs "정밀하게 검토"
- "간단하게 작성" vs "복잡한 분석 포함"

### 탐지

```python
# Conflict detector in ContextGate
if "짧게" in constraints and "상세하게" in constraints:
    context.conflict_flags.append("길이 충돌")
    
if len(context.conflict_flags) > 0:
    trigger_recovery("context_conflict", {
        "conflict_items": context.conflict_flags,
        "priority_policy": "system"
    })
```

### 복구 전략

#### Phase 1: 우선순위 정책 적용

```
우선순위: 시스템 정책 > 사용자 정책 > 기본 정책

시스템 정책:
  - 보안/규정 관련 제약 우선
  - 기술적 제약 우선
  
사용자 정책:
  - 명시적 요구사항 우선
  - 최근 요청 우선
  
기본 정책:
  - 품질 우선
  - 완성도 우선
```

**코드 예시**:
```python
def apply_priority_policy(conflicts, policy):
    if policy == "system":
        # 시스템 규칙 우선
        resolution = resolve_by_system_rules(conflicts)
    elif policy == "user":
        # 사용자 선호도 우선
        resolution = resolve_by_user_preference(conflicts)
    else:
        # 기본 규칙
        resolution = resolve_by_default(conflicts)
    
    return resolution
```

#### Phase 2: 자동 조정

```
충돌: "짧게" + "상세하게"
해결: 
  - 본문은 상세하게 작성
  - 상단에 3줄 요약 제공
  - 구조화된 섹션으로 가독성 확보
```

**코드 예시**:
```python
if "짧게" in conflict and "상세하게" in conflict:
    resolutions.append({
        "conflict": conflict,
        "resolution": "상세 본문 + 상단 요약 제공",
        "implementation": {
            "summary_lines": 3,
            "detailed_body": True,
            "structured_sections": True
        }
    })
```

#### Phase 3: Rollback to Planner

```
액션: ROLLBACK
조건: 충돌 자동 해소 불가
방법:
  1. 충돌 항목을 구조화하여 Planner에 전달
  2. Planner가 요구사항 재해석
  3. 명확한 우선순위와 함께 재계획
```

**코드 예시**:
```python
if unresolved_count > 0:
    return RecoveryResult(
        success=True,
        action=RecoveryAction.ROLLBACK,
        message=f"Rolling back to Planner. "
                f"{unresolved_count} conflicts unresolved."
    )
```

### 장점

- ✅ 명확한 우선순위: 일관된 정책 적용
- ✅ 자동 해소: 대부분의 충돌 자동 처리
- ✅ 사용자 개입 최소화: Rollback은 최후 수단

### 정책

| 충돌 수 | 해소 가능 | 액션 |
|--------|----------|------|
| 1-2 | 100% | RETRY (자동 조정) |
| 1-2 | 부분 | ROLLBACK |
| 3+ | - | MANUAL |

---

## 시나리오 3: 리뷰 게이트 실패

### 상황

Reviewer Agent가 high severity issue 발견:
- 요구사항 2개 미반영
- 근거/출처 누락
- 형식 오류
- 품질 기준 미달

### 탐지

```python
# ReviewGate validation
review_result = reviewer.run(inputs)
review_artifact = review_result["artifact"]

if review_artifact.status == "rejected":
    trigger_recovery("gate_failure", {
        "issues": review_artifact.issues,
        "gate_name": "review_gate",
        "severity_counts": count_by_severity(review_artifact.issues)
    })
```

### 복구 전략

#### Phase 1: 심각도 분석

```
Critical (심각도 최상):
  - 필수 요구사항 미충족
  - 규정 위반
  → 액션: ROLLBACK (전체 재실행)

High (심각도 상):
  - 주요 기능 누락
  - 품질 기준 미달
  → 액션: RETRY (부분 수정)

Medium/Low:
  - 개선 여지
  - 사소한 오류
  → 액션: SKIP (조건부 승인)
```

#### Phase 2: 부분 재실행 (Incremental Patch)

```
방법:
  1. 수정 가능한 이슈 식별
     - suggested_fix가 명확한 이슈
     - 특정 섹션에 국한된 이슈
  
  2. 수정 범위만 재생성
     - 전체 문서가 아닌 해당 섹션만
     - 이미 검증된 부분은 유지
  
  3. 재검토
     - 수정 부분만 재리뷰
     - 전체 일관성 확인
```

**코드 예시**:
```python
def identify_fixable_issues(issues):
    fixable = []
    for issue in issues:
        if (issue.suggested_fix and 
            len(issue.suggested_fix) > 5 and
            issue.location != "전체 문서"):
            fixable.append(issue)
    return fixable

if severity_counts.get("high", 0) > 0:
    fixable = identify_fixable_issues(issues)
    if fixable:
        return RecoveryResult(
            success=True,
            action=RecoveryAction.RETRY,
            message=f"Applying incremental fixes for "
                    f"{len(fixable)} issues"
        )
```

#### Phase 3: 조건부 승인

```
조건:
  - Critical issue = 0
  - High issue = 0
  - Medium/Low만 존재

액션: SKIP (다음 단계 진행)

방법:
  1. 이슈를 로그에 기록
  2. 최종 메타데이터에 경고 표시
  3. 승인 노트에 조건 명시
```

**코드 예시**:
```python
if (severity_counts.get("critical", 0) == 0 and
    severity_counts.get("high", 0) == 0):
    return RecoveryResult(
        success=True,
        action=RecoveryAction.SKIP,
        message="Conditional approval with logged issues"
    )
```

### 장점

- ✅ **비용 절감**: 전체가 아닌 부분만 재생성
- ✅ **시간 단축**: 이미 검증된 부분 재사용
- ✅ **품질 유지**: 수정 후 재검토로 품질 보장

### 정책

| Severity | Count | 액션 |
|----------|-------|------|
| Critical | > 0 | ROLLBACK (전체) |
| High | > 0 | RETRY (부분) |
| Medium | > 0 | SKIP (조건부) |
| Low | any | SKIP |

---

## 복구 전략 비교

| 시나리오 | 주요 액션 | 최대 재시도 | Fallback |
|---------|----------|------------|----------|
| 스키마 불일치 | RETRY → FALLBACK | 3회 | 템플릿 |
| 컨텍스트 충돌 | 정책 적용 → ROLLBACK | 1회 | Planner |
| 게이트 실패 | 부분 수정 → ROLLBACK | 2회 | 조건부 승인 |

## 복구 통계 추적

```python
class ErrorRecoveryStrategy:
    def get_recovery_statistics(self):
        return {
            "total": 총 복구 시도,
            "by_type": {
                "schema_mismatch": 3,
                "context_conflict": 1,
                "gate_failure": 2
            },
            "by_action": {
                "retry": 4,
                "fallback": 1,
                "rollback": 1
            }
        }
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-04-19
