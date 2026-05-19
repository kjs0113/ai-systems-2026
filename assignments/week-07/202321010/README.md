# 5단계 멀티에이전트 시스템

AI 시스템 과제 - Week 07

## 📋 개요

본 프로젝트는 **5단계 파이프라인형 멀티에이전트 아키텍처**를 구현한 시스템입니다. 각 에이전트는 표준 JSON 아티팩트를 통해 통신하며, 각 단계마다 검증 게이트를 통과해야 다음 단계로 진행할 수 있습니다.

### ✨ 주요 특징

- ✅ **5단계 파이프라인**: Planner → Context → Builder → Reviewer → Finalizer
- ✅ **JSON 아티팩트 기반 통신**: 4개 이상의 표준 스키마 정의
- ✅ **DAG 기반 실행 관리**: 의존성 그래프와 병렬화 tier 분석
- ✅ **검증 게이트**: Phase별 5개의 게이트 체크리스트
- ✅ **에러 복구 전략**: 3가지 시나리오별 자동 복구 메커니즘

## 🏗️ 시스템 아키텍처

```
[User Input]
    ↓
┌─────────────────┐
│ Planner Agent   │ → PlanArtifact
└─────────────────┘
    ↓
[Gate 1: Planning Validation]
    ↓
┌─────────────────┐
│ Context Agent   │ → ContextArtifact
└─────────────────┘
    ↓
[Gate 2: Context Validation]
    ↓
┌─────────────────┐
│ Builder Agent   │ → DraftArtifact
└─────────────────┘
    ↓
[Gate 3: Draft Validation]
    ↓
┌─────────────────┐
│ Reviewer Agent  │ → ReviewArtifact
└─────────────────┘
    ↓
[Gate 4: Review Validation]
    ↓
┌─────────────────┐
│ Finalizer Agent │ → FinalArtifact
└─────────────────┘
    ↓
[Gate 5: Release Validation]
    ↓
[Final Output]
```

## 📁 프로젝트 구조

```
202321010/
├── multi_agent_system/
│   ├── agents/              # 에이전트 모듈
│   │   ├── base.py          # Base Agent 추상 클래스
│   │   ├── planner.py       # 계획 수립 에이전트
│   │   ├── context.py       # 맥락 수집 에이전트
│   │   ├── builder.py       # 초안 생성 에이전트
│   │   ├── reviewer.py      # 검토 에이전트
│   │   └── finalizer.py     # 최종화 에이전트
│   │
│   ├── artifacts/           # 아티팩트 스키마
│   │   ├── plan.py          # PlanArtifact
│   │   ├── context.py       # ContextArtifact
│   │   ├── draft.py         # DraftArtifact
│   │   ├── review.py        # ReviewArtifact
│   │   └── final.py         # FinalArtifact
│   │
│   ├── gates/               # 검증 게이트
│   │   ├── base_gate.py     # Base Gate 클래스
│   │   ├── planning_gate.py # 계획 검증
│   │   ├── context_gate.py  # 맥락 검증
│   │   ├── draft_gate.py    # 초안 검증
│   │   ├── review_gate.py   # 검토 검증
│   │   └── release_gate.py  # 배포 검증
│   │
│   ├── orchestrator/        # 실행 관리
│   │   ├── dag.py           # DAG 구현
│   │   ├── executor.py      # Orchestrator
│   │   └── recovery.py      # 에러 복구 전략
│   │
│   └── tests/               # 테스트
│       └── test_system.py
│
├── docs/                    # 문서
│   ├── ARCHITECTURE.md      # 아키텍처 상세 문서
│   ├── ARTIFACTS.md         # 아티팩트 스키마 상세
│   ├── GATES.md             # 게이트 체크리스트
│   └── RECOVERY.md          # 에러 복구 전략
│
├── main.py                  # 메인 실행 파일
├── requirements.txt         # 의존성
└── README.md               # 본 문서
```

## 🚀 실행 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 시스템 실행

```bash
python main.py
```

### 3. 테스트 실행

```bash
python -m multi_agent_system.tests.test_system
```

## 📊 DAG 및 병렬화 Tier

### Tier 구조

| Tier | 노드 | 병렬화 가능 | 설명 |
|------|------|------------|------|
| 0 | Planner | ✗ | 시작점, 단독 실행 |
| 1 | Context | ✗ | Planner 의존 |
| 2 | Builder | ✗ | Planner + Context 의존 |
| 3 | Reviewer | ✗ | Builder 의존 |
| 4 | Finalizer | ✗ | Reviewer 의존 |

### 병렬화 분석

- **총 노드 수**: 5개
- **총 Tier 수**: 5개
- **병렬화 효율**: 현재 순차 실행 (확장 가능 구조)

> **확장 가능성**: Context 단계 이후에 Policy Checker, Data Validator 등을 병렬로 추가 가능

## 🎯 아티팩트 스키마

### 1. PlanArtifact

```json
{
  "artifact_type": "plan",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "goal": "고객 피드백 분석 보고서 작성",
  "success_criteria": ["기준1", "기준2"],
  "steps": [
    {
      "step_id": "step_001",
      "description": "계획 수립",
      "depends_on": [],
      "owner_agent": "planner"
    }
  ],
  "constraints": ["제약1", "제약2"],
  "created_at": "2026-04-19T12:00:00Z"
}
```

### 2. ContextArtifact

```json
{
  "artifact_type": "context",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "assumptions": ["가정1", "가정2"],
  "constraints": ["제약1"],
  "references": [
    {
      "source_id": "ref_001",
      "summary": "참조 자료",
      "confidence": 0.92
    }
  ],
  "open_questions": [],
  "conflict_flags": [],
  "created_at": "2026-04-19T12:05:00Z"
}
```

### 3. DraftArtifact

```json
{
  "artifact_type": "draft",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "content": {
    "title": "보고서 제목",
    "sections": [...]
  },
  "coverage_map": [
    {
      "requirement": "요구사항1",
      "covered": true,
      "evidence": "section_002에서 완료"
    }
  ],
  "quality_score": 0.85,
  "created_at": "2026-04-19T12:15:00Z"
}
```

### 4. ReviewArtifact

```json
{
  "artifact_type": "review",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "status": "approved",
  "issues": [],
  "check_results": [
    {
      "check_name": "schema_valid",
      "passed": true,
      "details": "스키마 검증 통과"
    }
  ],
  "overall_quality": 0.89,
  "created_at": "2026-04-19T12:25:00Z"
}
```

상세 스키마는 [ARTIFACTS.md](docs/ARTIFACTS.md) 참조

## 🚪 검증 게이트

### Phase별 체크리스트

| Gate | 주요 체크 항목 | 통과 조건 |
|------|---------------|-----------|
| **Planning Gate** | 목표 정의, 성공 기준, DAG 유효성 | 필수 요구사항 누락 0건, 순환 없음 |
| **Context Gate** | 참조 자료, 충돌 감지, 미해결 질문 | Critical missing context 없음 |
| **Draft Gate** | 스키마, 커버리지, 품질 점수 | 커버리지 ≥ 80%, 품질 ≥ 0.7 |
| **Review Gate** | 크리티컬 이슈, 체크 결과 | High severity issue 0건 |
| **Release Gate** | 배포 플래그, 감사 추적, 메타데이터 | releaseable = true |

상세 체크리스트는 [GATES.md](docs/GATES.md) 참조

## 🔧 에러 복구 전략

### 시나리오 1: 스키마 불일치

**상황**: Builder가 필수 필드를 누락하여 스키마 검증 실패

**탐지**: Pydantic validation error

**복구 전략**:
1. 재시도 횟수 < 3회 → 자동 재생성
2. 재시도 2회 이상 → 프롬프트 강화
3. 최대 재시도 초과 → fallback 템플릿 사용

### 시나리오 2: 컨텍스트 충돌

**상황**: "짧게" vs "상세하게" 같은 모순된 제약 발견

**탐지**: Conflict detector 규칙 매칭

**복구 전략**:
1. 우선순위 정책 적용 (시스템 > 사용자 > 기본)
2. 자동 조정 가능 → 조정 후 진행
3. 해소 불가 → Planner로 rollback

### 시나리오 3: 게이트 실패

**상황**: Reviewer가 high severity issue 발견

**탐지**: ReviewArtifact status = rejected

**복구 전략**:
1. Critical 이슈 → 전체 재실행
2. High 이슈만 → 부분 수정 (incremental patch)
3. Medium 이하 → 조건부 승인

상세 전략은 [RECOVERY.md](docs/RECOVERY.md) 참조

## 📈 실행 결과 예시

### Case 1: 정상 입력 (최적 조건)

```
======================================================================
Case 1: 정상 입력 시나리오
======================================================================

📥 초기 입력:
  - 요구사항: 고객 피드백을 분석하여 인사이트를 도출...
  - 제약사항: 3개

🚀 시스템 실행 시작...

======================================================================
📋 실행 결과
======================================================================

✅ 상태: 성공
📌 작업 ID: task_20260419_213045
⏱️  실행 시간: 0.02초

📦 최종 산출물:
  - 배포 가능: True
  - 제목: 고객 피드백 분석 보고서 (최종)
  - 섹션 수: 5
  - 품질 점수: 1.00
  - 커버리지: 100.0%

📌 결과 해석

본 결과는 다음 조건 하에서 도출되었습니다:
  ✓ 입력 요구사항이 명확하게 정의된 단일 시나리오
  ✓ 아티팩트 스키마 검증이 Pydantic으로 강하게 적용된 환경
  ✓ 제한된 테스트 케이스 (controlled environment)

따라서 해당 결과는 시스템의 최적 조건 하 성능(upper-bound performance)을
나타내며, 다양한 edge case 및 불완전 입력에 대해서는 추가 검증이 필요합니다.
```

### Case 2: 오류 입력 (검증 시나리오)

```
======================================================================
Case 2: 오류 입력 시나리오 (모호한 요구사항)
======================================================================

📥 초기 입력 (의도적 오류):
  - 요구사항: 뭔가 좋은 거 ⚠️ (모호함)
  - 제약사항: ['짧게', '상세하게'] ⚠️ (상충)

======================================================================
📋 실행 결과
======================================================================

❌ 상태: 실패
📌 작업 ID: task_20260419_213050
❗ 실패 단계: planner
💬 에러: Gate 'planning' validation failed

📌 실패 원인 분석:
  - 입력 품질이 낮아 Planning Gate에서 검증 실패
  - 모호한 목표 정의로 인한 성공 기준 도출 불가
  - 복구 전략 실행: Planner 재실행 또는 수동 개입 필요
```

## 🛠️ 기술 스택

- **Python**: 3.8+
- **Pydantic**: 아티팩트 스키마 검증
- **NetworkX**: DAG 모델링 및 분석
- **Unittest**: 단위 테스트

## 📚 문서

- [아키텍처 상세](docs/ARCHITECTURE.md)
- [아티팩트 스키마](docs/ARTIFACTS.md)
- [게이트 체크리스트](docs/GATES.md)
- [에러 복구 전략](docs/RECOVERY.md)

## 🎓 과제 요구사항 충족

| 요구사항 | 충족 여부 | 구현 위치 |
|---------|----------|----------|
| 5단계 멀티에이전트 다이어그램 | ✅ | README, ARCHITECTURE.md |
| 아티팩트 JSON 스키마 (최소 3종) | ✅ | artifacts/ (5종 구현) |
| 의존성 DAG 및 병렬화 tier | ✅ | orchestrator/dag.py |
| 검증 게이트 체크리스트 | ✅ | gates/, GATES.md |
| 에러 복구 전략 (3 시나리오) | ✅ | orchestrator/recovery.py |

## ⚠️ 시스템 한계 및 검증 조건

### 성능 지표 정의

- **성공률**: 유효한 FinalArtifact 생성 비율 (스키마 검증 통과 기준)
- **품질 점수**: ReviewAgent 기준 체크리스트 통과 비율
- **커버리지**: PlanArtifact 요구사항 대비 DraftArtifact 반영 비율

### 검증 환경

본 시스템은 다음 조건 하에서 검증되었습니다:

1. **명확한 입력**: 요구사항이 구조화되고 모호성이 제거된 상태
2. **강한 스키마 검증**: Pydantic 기반 타입 체킹 및 필드 검증
3. **제한된 시나리오**: Controlled environment에서의 단위 테스트

### 알려진 한계점

- **순차 실행**: 현재 병렬화 구조는 준비되었으나 순차 실행만 구현됨
- **LLM 미통합**: 실제 언어 모델이 아닌 템플릿 기반 콘텐츠 생성
- **Edge Case**: 극단적 입력 (빈 문자열, 특수문자 등)에 대한 추가 검증 필요
- **확장성**: 단일 머신 실행, 대용량 처리 미검증

### 추가 검증 필요 영역

- 동시 다중 작업 처리 (concurrency)
- 네트워크 장애 시나리오
- 대용량 데이터 (>10MB) 처리
- 다국어 입력 처리

## 👤 작성자

- 학번: 202321010
- 과제: AI Systems Week 07
- 날짜: 2026-04-19

## 📄 라이선스

교육 목적의 과제 프로젝트
