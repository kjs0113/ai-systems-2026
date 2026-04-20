"""
ReviewArtifact Schema Definition

Reviewer Agent가 생성하는 검토 아티팩트
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


class Issue(BaseModel):
    """검토 이슈"""
    issue_id: str = Field(..., description="이슈 식별자")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="심각도")
    description: str = Field(..., description="이슈 설명")
    location: str = Field(..., description="이슈 위치 (섹션/라인)")
    suggested_fix: str = Field(..., description="권장 수정 사항")
    
    class Config:
        json_schema_extra = {
            "example": {
                "issue_id": "issue_001",
                "severity": "high",
                "description": "요구사항 '권장사항 제시'가 누락됨",
                "location": "전체 문서",
                "suggested_fix": "결론 섹션에 실행 가능한 권장사항 추가"
            }
        }


class CheckResult(BaseModel):
    """검증 체크 결과"""
    check_name: str = Field(..., description="검사 항목 이름")
    passed: bool = Field(..., description="통과 여부")
    details: str = Field(..., description="상세 내용")
    
    class Config:
        json_schema_extra = {
            "example": {
                "check_name": "schema_valid",
                "passed": True,
                "details": "스키마 검증 통과"
            }
        }


class ReviewArtifact(BaseModel):
    """검토 아티팩트"""
    artifact_type: str = Field(default="review", description="아티팩트 타입")
    version: str = Field(default="1.0", description="스키마 버전")
    task_id: str = Field(..., description="작업 고유 식별자")
    status: Literal["approved", "rejected", "conditional"] = Field(..., description="검토 상태")
    issues: List[Issue] = Field(default_factory=list, description="발견된 이슈 목록")
    check_results: List[CheckResult] = Field(..., description="검증 체크 결과 목록")
    overall_quality: float = Field(..., ge=0.0, le=1.0, description="전체 품질 점수")
    reviewer_notes: str = Field(default="", description="검토자 노트")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="생성 시각 (ISO 8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
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
                        "passed": True,
                        "details": "스키마 검증 완료"
                    },
                    {
                        "check_name": "coverage_check",
                        "passed": True,
                        "details": "요구사항 커버리지 95%"
                    }
                ],
                "overall_quality": 0.82,
                "reviewer_notes": "전반적으로 양호하나 일부 보완 필요",
                "created_at": "2026-04-19T12:25:00Z"
            }
        }
    
    def get_critical_issues(self) -> List[Issue]:
        """크리티컬 이슈 목록 반환"""
        return [issue for issue in self.issues if issue.severity in ["high", "critical"]]
    
    def get_blocking_issues(self) -> List[Issue]:
        """블로킹 이슈 목록 반환 (critical만)"""
        return [issue for issue in self.issues if issue.severity == "critical"]
    
    def is_acceptable(self) -> bool:
        """승인 가능 여부"""
        return self.status == "approved" or (
            self.status == "conditional" and len(self.get_blocking_issues()) == 0
        )
