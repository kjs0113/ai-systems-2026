"""
PlanArtifact Schema Definition

Planner Agent가 생성하는 작업 계획 아티팩트
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class PlanStep(BaseModel):
    """작업 단계 정의"""
    step_id: str = Field(..., description="단계 고유 식별자")
    description: str = Field(..., description="단계 설명")
    depends_on: List[str] = Field(default_factory=list, description="의존하는 단계 ID 목록")
    owner_agent: str = Field(..., description="담당 에이전트 이름")
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_id": "step_001",
                "description": "요구사항 분석 및 초기 계획 수립",
                "depends_on": [],
                "owner_agent": "planner"
            }
        }


class PlanArtifact(BaseModel):
    """작업 계획 아티팩트"""
    artifact_type: str = Field(default="plan", description="아티팩트 타입")
    version: str = Field(default="1.0", description="스키마 버전")
    task_id: str = Field(..., description="작업 고유 식별자")
    goal: str = Field(..., description="최종 목표")
    success_criteria: List[str] = Field(..., description="성공 기준 목록")
    steps: List[PlanStep] = Field(..., description="작업 단계 목록")
    constraints: List[str] = Field(default_factory=list, description="제약사항 목록")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="생성 시각 (ISO 8601)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
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
                        "step_id": "step_001",
                        "description": "계획 수립",
                        "depends_on": [],
                        "owner_agent": "planner"
                    }
                ],
                "constraints": [
                    "보고서 길이는 10페이지 이내",
                    "개인정보 포함 금지"
                ],
                "created_at": "2026-04-19T12:00:00Z"
            }
        }
    
    def validate_dag(self) -> bool:
        """단계 간 의존성이 순환하지 않는지 검증"""
        step_ids = {step.step_id for step in self.steps}
        
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    return False
        
        # 간단한 순환 참조 검사
        visited = set()
        
        def has_cycle(step_id: str, path: set) -> bool:
            if step_id in path:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            path.add(step_id)
            
            step = next((s for s in self.steps if s.step_id == step_id), None)
            if step:
                for dep in step.depends_on:
                    if has_cycle(dep, path.copy()):
                        return True
            
            return False
        
        for step in self.steps:
            if has_cycle(step.step_id, set()):
                return False
        
        return True
