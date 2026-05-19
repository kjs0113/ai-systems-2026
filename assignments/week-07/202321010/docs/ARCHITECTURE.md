# 아키텍처 상세 문서

## 1. 개요

본 시스템은 **5단계 파이프라인형 멀티에이전트 아키텍처**로 설계되었습니다. 각 에이전트는 명확한 단일 책임을 가지며, 표준화된 JSON 아티팩트를 통해 통신합니다.

## 2. 설계 원칙

### 2.1 핵심 원칙

1. **Artifact-Centric Communication**: 에이전트 간 직접 함수 호출이 아닌 표준 아티팩트 교환
2. **Gate-Based Quality Control**: 각 단계마다 검증 게이트를 통과해야 진행
3. **DAG-Based Execution**: 의존성 그래프로 실행 순서 관리
4. **Recovery-First Design**: 에러 발생 시 자동 복구 메커니즘

### 2.2 아키텍처 레이어

```
┌─────────────────────────────────────────────┐
│           Orchestration Layer               │
│  (DAG, Executor, Recovery Strategy)         │
├─────────────────────────────────────────────┤
│           Agent Layer                       │
│  (Planner, Context, Builder, Reviewer...)   │
├─────────────────────────────────────────────┤
│           Gate Layer                        │
│  (Validation Gates)                         │
├─────────────────────────────────────────────┤
│           Artifact Layer                    │
│  (JSON Schema Definitions)                  │
└─────────────────────────────────────────────┘
```

## 3. 5단계 파이프라인 상세

### 3.1 Stage 1: Planner Agent

**역할**:
- 요구사항 해석
- 작업 단계 정의
- 성공 기준 도출
- 필요한 입출력 아티팩트 명세

**입력**:
- `requirements`: 사용자 요구사항 (string)
- `constraints`: 제약사항 목록 (list, optional)
- `task_id`: 작업 ID (string, optional)

**출력**:
- `PlanArtifact`: 작업 계획 아티팩트

**실패 조건**:
- 모호한 요구사항
- 누락된 성공 기준
- 실행 불가능한 계획

**구현 위치**: `agents/planner.py`

---

### 3.2 Stage 2: Context Agent

**역할**:
- 실행에 필요한 배경 맥락 수집
- 입력 자료 정제
- 제약사항 명문화
- 충돌 감지

**입력**:
- `plan`: PlanArtifact
- `additional_context`: 추가 컨텍스트 (dict, optional)

**출력**:
- `ContextArtifact`: 배경 맥락 아티팩트

**실패 조건**:
- 필수 컨텍스트 누락
- 출처 불명 데이터
- 상충되는 제약

**구현 위치**: `agents/context.py`

---

### 3.3 Stage 3: Builder Agent

**역할**:
- 실제 초안/결과물 생성
- 구조화된 산출물 작성
- 계획/컨텍스트 반영

**입력**:
- `plan`: PlanArtifact
- `context`: ContextArtifact

**출력**:
- `DraftArtifact`: 초안 아티팩트

**실패 조건**:
- 스키마 미준수
- 요구사항 일부 미반영
- 품질 기준 미달

**구현 위치**: `agents/builder.py`

---

### 3.4 Stage 4: Reviewer Agent

**역할**:
- 정합성, 완결성, 품질 검토
- 결함 식별
- 수정 지시 생성

**입력**:
- `draft`: DraftArtifact
- `plan`: PlanArtifact

**출력**:
- `ReviewArtifact`: 검토 아티팩트

**실패 조건**:
- 검토 기준 불명확
- false positive 과다
- 핵심 결함 미탐지

**구현 위치**: `agents/reviewer.py`

---

### 3.5 Stage 5: Finalizer Agent

**역할**:
- 리뷰 반영 여부 최종 확인
- 배포용 포맷 변환
- 최종 승인 상태 기록

**입력**:
- `draft`: DraftArtifact
- `review`: ReviewArtifact
- `audit_trail`: 감사 추적 로그 (list, optional)

**출력**:
- `FinalArtifact`: 최종 산출물 아티팩트

**실패 조건**:
- 미해결 이슈 존재
- 승인 기준 미충족
- 최종 메타데이터 누락

**구현 위치**: `agents/finalizer.py`

---

## 4. 의존성 DAG 설계

### 4.1 기본 DAG 구조

```
        [UserInput]
             |
             v
        [Planner]
             |
             +--------+
             |        |
             v        v
        [Context] [Planner Output]
             |        |
             +--------+
                  |
                  v
             [Builder]
                  |
                  v
             [Reviewer]
                  |
                  v
             [Finalizer]
                  |
                  v
             [Output]
```

### 4.2 확장 가능 DAG (병렬화)

```
                      [Planner]
                          |
            +-------------+-------------+
            |             |             |
            v             v             v
       [Context]   [Policy Check]  [Data Prep]
            |             |             |
            +-------------+-------------+
                          |
                          v
                     [Builder]
                          |
                          v
                     [Reviewer]
                          |
                          v
                     [Finalizer]
```

### 4.3 Tier 분석

**Tier 0**: User Input
- 초기화 및 메타데이터 설정

**Tier 1**: Planner
- 시작점, 단독 실행
- 병렬화 불가능 (다른 노드 의존 없음)

**Tier 2**: Context + Policy + Data (병렬 가능)
- Planner 결과만 필요
- 서로 독립적
- **병렬화 효율 최대**

**Tier 3**: Builder
- Tier 2의 모든 결과 필요
- 병렬화 불가능

**Tier 4**: Reviewer
- Builder 결과 필요
- 순차 실행

**Tier 5**: Finalizer
- Reviewer 결과 필요
- 순차 실행

### 4.4 병렬화 효율 계산

```
병렬화 효율 = 1 - (병렬 실행 시간 / 순차 실행 시간)

기본 파이프라인: 0% (모두 순차)
확장 파이프라인: ~30% (Tier 2 병렬화)
```

## 5. 검증 게이트 아키텍처

### 5.1 Gate 설계 패턴

```python
class BaseGate:
    def validate(artifact) -> ValidationResult:
        - 체크리스트 항목 검증
        - 에러/경고 수집
        - 통과/실패 판정
        return ValidationResult
```

### 5.2 Gate 체인

```
Agent → Artifact → Gate → [Pass/Fail]
                            |
                   Pass: 다음 Stage
                   Fail: Recovery Strategy
```

### 5.3 게이트별 책임

| Gate | 검증 대상 | 핵심 체크 |
|------|----------|----------|
| Planning | PlanArtifact | DAG 순환, 필수 필드, 성공 기준 |
| Context | ContextArtifact | 충돌 감지, 참조 신뢰도, 미해결 질문 |
| Draft | DraftArtifact | 커버리지, 품질 점수, 섹션 완성도 |
| Review | ReviewArtifact | 크리티컬 이슈, 체크 통과율, 품질 |
| Release | FinalArtifact | 배포 플래그, 감사 추적, 메타데이터 |

## 6. 오케스트레이터 설계

### 6.1 ExecutionContext

```python
class ExecutionContext:
    - task_id: 작업 ID
    - artifacts: 단계별 아티팩트 저장소
    - logs: 실행 로그
    - gate_results: 게이트 검증 결과
    - start_time, end_time: 실행 시간
```

### 6.2 Orchestrator 실행 흐름

```
1. Context 초기화
2. For each stage in DAG:
    a. Agent 실행
    b. Artifact 생성
    c. Context에 저장
    d. Gate 검증
    e. 통과 → 다음 단계
       실패 → Recovery 또는 중단
3. 실행 완료
4. 결과 반환
```

### 6.3 에러 처리 흐름

```
Agent 실행
    ↓
[에러 발생?]
    ↓ Yes
Recovery Strategy
    ↓
[복구 가능?]
    ↓ Yes: Retry
    ↓ No: Fail
```

## 7. 에러 복구 아키텍처

### 7.1 복구 액션 타입

```python
RecoveryAction:
    - RETRY: 재시도
    - ROLLBACK: 이전 단계로 되돌리기
    - SKIP: 건너뛰기
    - MANUAL: 수동 개입 필요
    - FALLBACK: 대체 방법 사용
```

### 7.2 복구 결정 트리

```
에러 발생
    |
    +-- 재시도 가능? (retry_count < max)
    |       |
    |       +-- Yes: RETRY
    |       +-- No: FALLBACK or MANUAL
    |
    +-- 부분 수정 가능?
    |       |
    |       +-- Yes: INCREMENTAL PATCH
    |       +-- No: FULL ROLLBACK
    |
    +-- Critical?
            |
            +-- Yes: ROLLBACK
            +-- No: SKIP (conditional pass)
```

## 8. 확장성 및 향후 개선

### 8.1 확장 포인트

1. **추가 에이전트**: Policy Checker, Data Validator 등
2. **커스텀 게이트**: 도메인별 검증 규칙
3. **병렬 실행**: asyncio 기반 비동기 처리
4. **LLM 통합**: 실제 AI 모델 연동

### 8.2 성능 최적화

- **캐싱**: 아티팩트 캐싱으로 재실행 최소화
- **스트리밍**: 대용량 콘텐츠 스트리밍 처리
- **분산 실행**: 여러 머신에 에이전트 분산

### 8.3 현재 한계점

#### 기술적 한계

- **순차 실행**: 병렬화 구조는 준비되었으나 실제 구현은 순차적
- **템플릿 기반**: 실제 LLM이 아닌 하드코딩된 콘텐츠 생성
- **단일 머신**: 분산 처리 미지원

#### 검증 범위 한계

본 시스템은 다음 조건 하에서 검증되었습니다:

1. **명확한 입력**: 구조화되고 모호성이 제거된 요구사항
2. **제한된 규모**: 소규모 텍스트 처리 (< 10KB)
3. **Controlled Environment**: 단위 테스트 환경

#### 미검증 시나리오

- 동시 다중 작업 처리 (concurrency)
- 네트워크 장애 및 타임아웃
- 대용량 데이터 처리 (>10MB)
- 극단적 입력 (빈 문자열, 특수문자 등)
- 다국어 처리 및 인코딩 이슈

### 8.4 성능 지표 정의

- **성공률**: 유효한 FinalArtifact 생성 비율 (스키마 검증 통과 기준)
- **품질 점수**: ReviewAgent 체크리스트 통과 비율
- **커버리지**: PlanArtifact 요구사항 대비 DraftArtifact 반영 비율
- **실행 시간**: 전체 파이프라인 처리 시간 (초 단위)

**중요**: 본 문서에 제시된 100% 성공률은 최적 조건(upper-bound) 하에서 측정된 것이며,  
실제 프로덕션 환경에서는 다양한 edge case에 따라 성능 변동이 예상됩니다.*: 병렬화 구조는 준비되었으나 실제 구현은 순차적
- **템플릿 기반**: 실제 LLM이 아닌 하드코딩된 콘텐츠 생성
- **단일 머신**: 분산 처리 미지원

#### 검증 범위 한계

본 시스템은 다음 조건 하에서 검증되었습니다:

1. **명확한 입력**: 구조화되고 모호성이 제거된 요구사항
2. **제한된 규모**: 소규모 텍스트 처리 (< 10KB)
3. **Controlled Environment**: 단위 테스트 환경

#### 미검증 시나리오

- 동시 다중 작업 처리 (concurrency)
- 네트워크 장애 및 타임아웃
- 대용량 데이터 처리 (>10MB)
- 극단적 입력 (빈 문자열, 특수문자 등)
- 다국어 처리 및 인코딩 이슈

### 8.4 성능 지표 정의

- **성공률**: 유효한 FinalArtifact 생성 비율 (스키마 검증 통과 기준)
- **품질 점수**: ReviewAgent 체크리스트 통과 비율
- **커버리지**: PlanArtifact 요구사항 대비 DraftArtifact 반영 비율
- **실행 시간**: 전체 파이프라인 처리 시간 (초 단위)

**중요**: 본 문서에 제시된 100% 성공률은 최적 조건(upper-bound) 하에서 측정된 것이며,  
실제 프로덕션 환경에서는 다양한 edge case에 따라 성능 변동이 예상됩니다.

## 9. 구현 기술

| 컴포넌트 | 기술 | 용도 |
|---------|------|------|
| 스키마 검증 | Pydantic | 아티팩트 JSON 스키마 |
| DAG 관리 | NetworkX | 의존성 그래프 |
| 비동기 | asyncio | 병렬 실행 준비 |
| 테스트 | unittest | 단위 테스트 |

## 10. 디버깅 및 모니터링

### 10.1 로깅

- 각 에이전트의 `execution_log`
- ExecutionContext의 `logs`
- Gate 검증 결과

### 10.2 감사 추적

- 모든 단계의 실행 기록
- 아티팩트 버전 관리
- 에러 및 복구 이력

### 10.3 메트릭

- 실행 시간
- 재시도 횟수
- 품질 점수
- 커버리지율

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-04-19
