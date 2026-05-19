# 아티팩트 JSON 스키마 상세 문서

5가지 아티팩트의 상세 스키마 정의

## 개요

모든 에이전트는 표준화된 JSON 아티팩트를 통해 통신합니다. 각 아티팩트는 Pydantic 모델로 정의되어 타입 안정성과 자동 검증을 제공합니다.

---

## 1. PlanArtifact

### 목적
Planner Agent가 생성하는 작업 계획 아티팩트

### 스키마

```json
{
  "artifact_type": "plan",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "goal": "고객 피드백 분석 보고서 작성",
  "success_criteria": [
    "모든 피드백 항목이 분류됨",
    "핵심 인사이트가 도출됨",
    "실행 가능한 권장사항이 제시됨"
  ],
  "steps": [
    {
      "step_id": "step_planning",
      "description": "요구사항 분석 및 계획 수립",
      "depends_on": [],
      "owner_agent": "planner"
    },
    {
      "step_id": "step_context",
      "description": "배경 맥락 및 제약사항 수집",
      "depends_on": ["step_planning"],
      "owner_agent": "context"
    }
  ],
  "constraints": [
    "보고서 길이는 10페이지 이내",
    "개인정보 포함 금지"
  ],
  "created_at": "2026-04-19T12:00:00Z"
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|-----|------|------|------|
| artifact_type | string | ✅ | 고정값: "plan" |
| version | string | ✅ | 스키마 버전 |
| task_id | string | ✅ | 작업 고유 식별자 |
| goal | string | ✅ | 최종 목표 설명 |
| success_criteria | string[] | ✅ | 성공 기준 목록 |
| steps | PlanStep[] | ✅ | 작업 단계 목록 |
| constraints | string[] | ❌ | 제약사항 목록 |
| created_at | string | ✅ | 생성 시각 (ISO 8601) |

### PlanStep 스키마

```json
{
  "step_id": "step_001",
  "description": "단계 설명",
  "depends_on": ["step_000"],
  "owner_agent": "agent_name"
}
```

### 검증 규칙

- `goal` 길이 >= 10자
- `success_criteria` 최소 1개 이상
- `steps` 최소 1개 이상
- DAG 순환 참조 없음 (`validate_dag()` 통과)

### Pydantic 모델

```python
class PlanArtifact(BaseModel):
    artifact_type: str = "plan"
    version: str = "1.0"
    task_id: str
    goal: str
    success_criteria: List[str]
    steps: List[PlanStep]
    constraints: List[str] = []
    created_at: str = Field(default_factory=datetime.utcnow)
    
    def validate_dag(self) -> bool:
        """DAG 순환 참조 검증"""
        # 구현...
```

---

## 2. ContextArtifact

### 목적
Context Agent가 생성하는 배경 맥락 아티팩트

### 스키마

```json
{
  "artifact_type": "context",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "assumptions": [
    "모든 피드백은 영어로 작성됨",
    "최근 6개월 데이터만 분석"
  ],
  "constraints": [
    "개인정보 보호법 준수",
    "처리 시간 1시간 이내"
  ],
  "references": [
    {
      "source_id": "feedback_db",
      "summary": "고객 피드백 데이터베이스",
      "confidence": 0.95
    },
    {
      "source_id": "guidelines",
      "summary": "분석 가이드라인 문서",
      "confidence": 0.90
    }
  ],
  "open_questions": [
    "익명 피드백 처리 방법은?"
  ],
  "conflict_flags": [],
  "created_at": "2026-04-19T12:05:00Z"
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|-----|------|------|------|
| artifact_type | string | ✅ | 고정값: "context" |
| version | string | ✅ | 스키마 버전 |
| task_id | string | ✅ | 작업 고유 식별자 |
| assumptions | string[] | ❌ | 기본 가정 목록 |
| constraints | string[] | ❌ | 제약사항 목록 |
| references | Reference[] | ❌ | 참조 자료 목록 |
| open_questions | string[] | ❌ | 미해결 질문 목록 |
| conflict_flags | string[] | ❌ | 충돌 감지 플래그 |
| created_at | string | ✅ | 생성 시각 |

### Reference 스키마

```json
{
  "source_id": "doc_001",
  "summary": "출처 요약",
  "confidence": 0.92
}
```

### 검증 규칙

- `references` 각 항목의 `confidence` 범위: 0.0 ~ 1.0
- `conflict_flags` 비어있어야 함 (충돌 없음)
- `open_questions` 수 <= 3 (권장)

---

## 3. DraftArtifact

### 목적
Builder Agent가 생성하는 초안 아티팩트

### 스키마

```json
{
  "artifact_type": "draft",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "content": {
    "title": "고객 피드백 분석 보고서",
    "sections": [
      {
        "section_id": "sec_intro",
        "heading": "1. 개요",
        "body": "본 보고서는 2025년 하반기 고객 피드백을 분석합니다...",
        "subsections": []
      },
      {
        "section_id": "sec_analysis",
        "heading": "2. 분석",
        "body": "상세 분석 내용...",
        "subsections": []
      }
    ],
    "metadata": {
      "author": "builder_agent",
      "word_count": 3500
    }
  },
  "coverage_map": [
    {
      "requirement": "피드백 분류",
      "covered": true,
      "evidence": "section_002에서 5개 카테고리로 분류 완료"
    },
    {
      "requirement": "인사이트 도출",
      "covered": true,
      "evidence": "section_003에서 3개 주요 인사이트 제시"
    }
  ],
  "quality_score": 0.85,
  "created_at": "2026-04-19T12:15:00Z"
}
```

### Section 스키마

```json
{
  "section_id": "sec_001",
  "heading": "섹션 제목",
  "body": "섹션 본문",
  "subsections": []
}
```

### CoverageItem 스키마

```json
{
  "requirement": "요구사항 설명",
  "covered": true,
  "evidence": "충족 근거"
}
```

### 검증 규칙

- `content.title` 비어있지 않음
- `content.sections` 최소 1개 이상
- 필수 섹션 존재: `sec_intro`, `sec_conclusion`
- `coverage_map` 각 항목에 `evidence` 존재
- `quality_score` 범위: 0.0 ~ 1.0

### 메서드

```python
def calculate_coverage_rate(self) -> float:
    """요구사항 충족률 계산"""
    covered = sum(1 for item in coverage_map if item.covered)
    return covered / len(coverage_map)

def has_required_sections(self, required: List[str]) -> bool:
    """필수 섹션 존재 확인"""
    section_ids = {sec.section_id for sec in sections}
    return all(req in section_ids for req in required)
```

---

## 4. ReviewArtifact

### 목적
Reviewer Agent가 생성하는 검토 아티팩트

### 스키마

```json
{
  "artifact_type": "review",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "status": "conditional",
  "issues": [
    {
      "issue_id": "issue_001",
      "severity": "medium",
      "description": "일부 데이터 출처 미명시",
      "location": "section_003",
      "suggested_fix": "각 통계치에 출처 추가"
    }
  ],
  "check_results": [
    {
      "check_name": "schema_valid",
      "passed": true,
      "details": "스키마 검증 완료"
    },
    {
      "check_name": "coverage_check",
      "passed": true,
      "details": "요구사항 커버리지 95%"
    }
  ],
  "overall_quality": 0.82,
  "reviewer_notes": "전반적으로 양호하나 일부 보완 필요",
  "created_at": "2026-04-19T12:25:00Z"
}
```

### Issue 스키마

```json
{
  "issue_id": "issue_001",
  "severity": "high",
  "description": "이슈 설명",
  "location": "위치",
  "suggested_fix": "수정 제안"
}
```

- **severity**: `"low"` | `"medium"` | `"high"` | `"critical"`

### CheckResult 스키마

```json
{
  "check_name": "check_name",
  "passed": true,
  "details": "상세 내용"
}
```

### 검증 규칙

- `status`: `"approved"` | `"rejected"` | `"conditional"`
- `overall_quality` 범위: 0.0 ~ 1.0
- `issues` 각 항목에 `suggested_fix` 권장

### 메서드

```python
def get_critical_issues(self) -> List[Issue]:
    """크리티컬 이슈 반환"""
    return [i for i in issues if i.severity in ["high", "critical"]]

def is_acceptable(self) -> bool:
    """승인 가능 여부"""
    return status == "approved" or (
        status == "conditional" and len(get_blocking_issues()) == 0
    )
```

---

## 5. FinalArtifact

### 목적
Finalizer Agent가 생성하는 최종 산출물 아티팩트

### 스키마

```json
{
  "artifact_type": "final",
  "version": "1.0",
  "task_id": "task_20260419_001",
  "final_content": {
    "title": "고객 피드백 분석 보고서 (최종)",
    "sections": [...],
    "metadata": {
      "finalized_at": "2026-04-19T12:30:00Z",
      "word_count": 3500
    },
    "quality_metrics": {
      "draft_quality": 0.85,
      "review_quality": 0.82,
      "coverage_rate": 1.0
    }
  },
  "releaseable": true,
  "audit_trail": [
    {
      "stage": "planning",
      "status": "passed",
      "timestamp": "2026-04-19T12:00:00Z",
      "details": "계획 수립 완료"
    },
    {
      "stage": "review",
      "status": "conditional",
      "timestamp": "2026-04-19T12:25:00Z",
      "details": "Issues: 1, Quality: 0.82"
    }
  ],
  "metadata": {
    "total_duration_seconds": 1500,
    "retry_count": 0,
    "quality_score": 0.89,
    "total_issues": 1,
    "critical_issues": 0
  },
  "approval_notes": "모든 검증 통과, 배포 승인",
  "created_at": "2026-04-19T12:30:00Z"
}
```

### ExecutionLog 스키마

```json
{
  "stage": "단계명",
  "status": "상태",
  "timestamp": "2026-04-19T12:00:00Z",
  "details": "상세 내용"
}
```

### 검증 규칙

- `releaseable` = `true` (배포 가능)
- `audit_trail` 최소 3개 로그 (planning, review, finalization)
- `metadata` 필수 필드: `finalized_at`, `quality_score`

---

## 스키마 버전 관리

| Version | 날짜 | 변경사항 |
|---------|------|---------|
| 1.0 | 2026-04-19 | 초기 스키마 정의 |

## 확장 가능성

새로운 아티팩트 추가 시:
1. `artifacts/` 폴더에 새 파일 생성
2. Pydantic BaseModel 상속
3. 공통 필드 포함: `artifact_type`, `version`, `task_id`, `created_at`

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-04-19
