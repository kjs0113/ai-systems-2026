"""
ContextArtifact Schema Definition

Context Agent가 생성하는 배경 맥락 아티팩트
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class Reference(BaseModel):
    """참조 자료 정보"""
    source_id: str = Field(..., description="출처 식별자")
    summary: str = Field(..., description="출처 요약")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0.0 ~ 1.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "doc_001",
                "summary": "2025년 고객 만족도 조사 결과",
                "confidence": 0.92
            }
        }


class ContextArtifact(BaseModel):
    """배경 맥락 아티팩트"""
    artifact_type: str = Field(default="context", description="아티팩트 타입")
    version: str = Field(default="1.0", description="스키마 버전")
    task_id: str = Field(..., description="작업 고유 식별자")
    assumptions: List[str] = Field(default_factory=list, description="가정 목록")
    constraints: List[str] = Field(default_factory=list, description="제약사항 목록")
    references: List[Reference] = Field(default_factory=list, description="참조 자료 목록")
    open_questions: List[str] = Field(default_factory=list, description="미해결 질문 목록")
    conflict_flags: List[str] = Field(default_factory=list, description="충돌 감지 플래그")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="생성 시각 (ISO 8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
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
                    }
                ],
                "open_questions": [
                    "익명 피드백 처리 방법은?"
                ],
                "conflict_flags": [],
                "created_at": "2026-04-19T12:05:00Z"
            }
        }
    
    def has_critical_issues(self) -> bool:
        """크리티컬 이슈 존재 여부"""
        return len(self.conflict_flags) > 0 or len(self.open_questions) > 3
