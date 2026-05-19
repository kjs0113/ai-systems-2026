"""
DraftArtifact Schema Definition

Builder Agent가 생성하는 초안 아티팩트
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime


class Section(BaseModel):
    """문서 섹션"""
    section_id: str = Field(..., description="섹션 식별자")
    heading: str = Field(..., description="섹션 제목")
    body: str = Field(..., description="섹션 본문")
    subsections: List['Section'] = Field(default_factory=list, description="하위 섹션 목록")
    
    class Config:
        json_schema_extra = {
            "example": {
                "section_id": "section_001",
                "heading": "개요",
                "body": "본 보고서는...",
                "subsections": []
            }
        }


class CoverageItem(BaseModel):
    """요구사항 커버리지 항목"""
    requirement: str = Field(..., description="요구사항")
    covered: bool = Field(..., description="충족 여부")
    evidence: str = Field(..., description="근거/증거")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requirement": "피드백 분류",
                "covered": True,
                "evidence": "section_002에서 5개 카테고리로 분류 완료"
            }
        }


class DraftContent(BaseModel):
    """초안 콘텐츠"""
    title: str = Field(..., description="문서 제목")
    sections: List[Section] = Field(..., description="섹션 목록")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class DraftArtifact(BaseModel):
    """초안 아티팩트"""
    artifact_type: str = Field(default="draft", description="아티팩트 타입")
    version: str = Field(default="1.0", description="스키마 버전")
    task_id: str = Field(..., description="작업 고유 식별자")
    content: DraftContent = Field(..., description="초안 콘텐츠")
    coverage_map: List[CoverageItem] = Field(..., description="요구사항 커버리지 맵")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="품질 점수 (0.0 ~ 1.0)")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="생성 시각 (ISO 8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "artifact_type": "draft",
                "version": "1.0",
                "task_id": "task_20260419_001",
                "content": {
                    "title": "고객 피드백 분석 보고서",
                    "sections": [
                        {
                            "section_id": "section_001",
                            "heading": "개요",
                            "body": "본 보고서는 2025년 하반기 고객 피드백을 분석합니다.",
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
                        "covered": True,
                        "evidence": "section_002에서 완료"
                    }
                ],
                "quality_score": 0.85,
                "created_at": "2026-04-19T12:15:00Z"
            }
        }
    
    def calculate_coverage_rate(self) -> float:
        """요구사항 충족률 계산"""
        if not self.coverage_map:
            return 0.0
        covered_count = sum(1 for item in self.coverage_map if item.covered)
        return covered_count / len(self.coverage_map)
    
    def has_required_sections(self, required: List[str]) -> bool:
        """필수 섹션 존재 여부 확인"""
        section_ids = {section.section_id for section in self.content.sections}
        return all(req in section_ids for req in required)
