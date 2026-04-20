"""
FinalArtifact Schema Definition

Finalizer Agent가 생성하는 최종 산출물 아티팩트
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class ExecutionLog(BaseModel):
    """실행 로그 항목"""
    stage: str = Field(..., description="단계명")
    status: str = Field(..., description="상태")
    timestamp: str = Field(..., description="실행 시각")
    details: str = Field(default="", description="상세 내용")


class FinalArtifact(BaseModel):
    """최종 산출물 아티팩트"""
    artifact_type: str = Field(default="final", description="아티팩트 타입")
    version: str = Field(default="1.0", description="스키마 버전")
    task_id: str = Field(..., description="작업 고유 식별자")
    final_content: Dict[str, Any] = Field(..., description="최종 콘텐츠")
    releaseable: bool = Field(..., description="배포 가능 여부")
    audit_trail: List[ExecutionLog] = Field(..., description="감사 추적 로그")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    approval_notes: str = Field(default="", description="승인 노트")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="생성 시각 (ISO 8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "final",
                "version": "1.0",
                "task_id": "task_20260419_001",
                "final_content": {
                    "title": "고객 피드백 분석 보고서 (최종)",
                    "format": "pdf",
                    "size_bytes": 524288
                },
                "releaseable": True,
                "audit_trail": [
                    {
                        "stage": "planning",
                        "status": "passed",
                        "timestamp": "2026-04-19T12:00:00Z",
                        "details": "계획 수립 완료"
                    }
                ],
                "metadata": {
                    "total_duration_seconds": 1500,
                    "retry_count": 0,
                    "quality_score": 0.89
                },
                "approval_notes": "모든 검증 통과, 배포 승인",
                "created_at": "2026-04-19T12:30:00Z"
            }
        }
