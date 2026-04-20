# 검증 게이트 체크리스트

Phase별 상세 검증 기준

## Gate 1: Planning Validation

### 체크리스트

- [ ] **요구사항이 모두 식별되었는가**
  - 목표(goal) 필드가 비어있지 않음
  - 목표 설명이 10자 이상

- [ ] **성공 기준이 명시되었는가**
  - success_criteria 배열에 2개 이상 항목 존재
  - 각 기준이 측정 가능한 형태

- [ ] **단계 간 의존성이 정의되었는가**
  - 모든 단계(steps)에 owner_agent 지정
  - depends_on 관계가 명확함

- [ ] **실행 불가능한 작업이 포함되지 않았는가**
  - DAG에 순환 참조 없음 (validate_dag() = true)
  - 모든 의존성 노드가 존재함

- [ ] **출력 아티팩트 형식이 정의되었는가**
  - PlanArtifact 스키마 준수
  - 필수 필드 모두 존재

### 통과 조건

```
필수 요구사항 누락 = 0건
단계 의존성 cycle = 없음
성공 기준 수 >= 2
```

### 구현

```python
class PlanningGate(BaseGate):
    def validate(self, artifact: PlanArtifact) -> ValidationResult:
        # 1. 목표 정의 확인
        # 2. 성공 기준 확인
        # 3. 단계 정의 확인
        # 4. DAG 순환 참조 확인
        # 5. 각 단계의 소유자 확인
        # 6. 제약사항 확인
```

---

## Gate 2: Context Validation

### 체크리스트

- [ ] **필수 컨텍스트가 수집되었는가**
  - assumptions 목록 존재
  - references 최소 1개 이상

- [ ] **제약사항이 문서화되었는가**
  - constraints 필드에 명시적 제약 기록
  - 각 제약의 출처 추적 가능

- [ ] **상충하는 정보가 식별되었는가**
  - conflict_flags 검사
  - 충돌 항목 명시적 기록

- [ ] **출처/근거가 기록되었는가**
  - 각 reference에 source_id 존재
  - confidence 값 기록 (0.0 ~ 1.0)

- [ ] **open question이 남아 있는가**
  - open_questions 수 <= 3
  - 크리티컬 질문은 0개

### 통과 조건

```
critical missing context = 없음
unresolved conflict = 없음 또는 명시적 플래그 존재
참조 자료 신뢰도 >= 0.5
```

### 구현

```python
class ContextGate(BaseGate):
    def validate(self, artifact: ContextArtifact) -> ValidationResult:
        # 1. 기본 가정 확인
        # 2. 참조 자료 확인
        # 3. 제약사항 확인
        # 4. 충돌 플래그 확인
        # 5. 미해결 질문 확인
        # 6. 크리티컬 이슈 확인
```

---

## Gate 3: Draft Validation

### 체크리스트

- [ ] **DraftArtifact 스키마를 만족하는가**
  - 필수 필드 존재: content, coverage_map
  - 타입 일치 (Pydantic 검증)

- [ ] **모든 요구사항이 coverage map에 반영되었는가**
  - coverage_rate >= 80%
  - 각 요구사항에 evidence 기록

- [ ] **섹션 구조가 완전한가**
  - 필수 섹션 존재: sec_intro, sec_conclusion
  - 각 섹션에 heading, body 존재

- [ ] **필수 필드가 비어 있지 않은가**
  - title 길이 > 0
  - 모든 section body 길이 >= 10

- [ ] **금지된 내용/형식 오류가 없는가**
  - 총 콘텐츠 길이 >= 300자
  - quality_score >= 0.7

### 통과 조건

```
schema valid = true
requirement coverage >= 95%
quality_score >= 0.7
```

### 구현

```python
class DraftGate(BaseGate):
    def validate(self, artifact: DraftArtifact) -> ValidationResult:
        # 1. 기본 필드 확인
        # 2. 커버리지 확인
        # 3. 필수 섹션 확인
        # 4. 품질 점수 확인
        # 5. 콘텐츠 길이 확인
        # 6. 각 섹션의 완성도 확인
```

---

## Gate 4: Review Validation

### 체크리스트

- [ ] **high severity issue가 남아 있는가**
  - critical issue 수 = 0
  - high issue 수 <= 허용 기준

- [ ] **리뷰 코멘트가 actionable 한가**
  - 모든 issue에 suggested_fix 존재
  - suggested_fix 길이 >= 5

- [ ] **검토 기준별 pass/fail이 기록되었는가**
  - check_results 배열 존재
  - 각 체크에 passed 상태 명시

- [ ] **false alarm 가능성이 과도하지 않은가**
  - overall_quality >= 0.6
  - 실패한 체크 수 < 총 체크의 50%

### 통과 조건

```
high severity issue = 0건
medium issue <= 허용 기준
overall_quality >= 0.6
```

### 구현

```python
class ReviewGate(BaseGate):
    def validate(self, artifact: ReviewArtifact) -> ValidationResult:
        # 1. 검토 상태 확인
        # 2. 체크 결과 확인
        # 3. 크리티컬 이슈 확인
        # 4. 블로킹 이슈 확인
        # 5. 품질 점수 확인
        # 6. 이슈 액션 가능성 확인
        # 7. 승인 가능 여부 확인
```

---

## Gate 5: Release Validation

### 체크리스트

- [ ] **모든 필수 게이트 통과 기록이 있는가**
  - audit_trail에 planning, review, finalization 존재
  - 각 단계의 status 기록

- [ ] **최종 메타데이터가 기록되었는가**
  - metadata에 finalized_at 존재
  - quality_score, coverage_rate 기록

- [ ] **산출물 버전이 고정되었는가**
  - version 필드 존재
  - artifact_type = "final"

- [ ] **재현 가능한 실행 이력이 있는가**
  - audit_trail 길이 >= 3
  - 각 로그에 timestamp 기록

- [ ] **실패/수정 로그가 보존되었는가**
  - 실패 단계 로그 존재 시 명시
  - 복구 이력 기록

### 통과 조건

```
releaseable = true
audit trail complete = true
필수 메타데이터 존재 = true
```

### 구현

```python
class ReleaseGate(BaseGate):
    def validate(self, artifact: FinalArtifact) -> ValidationResult:
        # 1. 배포 가능 플래그 확인
        # 2. 최종 콘텐츠 확인
        # 3. 감사 추적 확인
        # 4. 메타데이터 확인
        # 5. 승인 노트 확인
        # 6. 버전 정보 확인
        # 7. 타임스탬프 확인
```

---

## ValidationResult 구조

```python
class ValidationResult:
    passed: bool              # 통과 여부
    gate_name: str            # 게이트 이름
    errors: List[str]         # 에러 목록
    warnings: List[str]       # 경고 목록
    timestamp: str            # 검증 시각
```

## 게이트 실패 시 처리

```
Gate 실패
    ↓
[Severity 분석]
    ↓
Critical/High → Recovery Strategy
    ↓
Medium/Low → 조건부 통과 또는 경고
```

## 커스터마이징

각 게이트는 초기화 시 임계값 설정 가능:

```python
draft_gate = DraftGate(
    min_coverage=0.8,    # 최소 커버리지
    min_quality=0.7       # 최소 품질 점수
)
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-04-19
