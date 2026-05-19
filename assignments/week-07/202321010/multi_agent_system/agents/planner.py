"""
Planner Agent Implementation

요구사항을 해석하고 작업 계획을 생성하는 에이전트
"""

from typing import Dict, Any
from .base import BaseAgent
from ..artifacts.plan import PlanArtifact, PlanStep
from datetime import datetime


class PlannerAgent(BaseAgent):
    """계획 수립 에이전트"""
    
    def __init__(self):
        super().__init__("planner")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 계획 생성
        
        Args:
            inputs: {
                "requirements": str - 사용자 요구사항,
                "constraints": List[str] - 제약사항 (선택),
                "task_id": str - 작업 ID (선택)
            }
            
        Returns:
            Dict containing PlanArtifact
        """
        self._set_status("running")
        self._log("Starting plan generation")
        
        try:
            # 입력 검증
            if "requirements" not in inputs:
                raise ValueError("requirements field is required")
            
            requirements = inputs["requirements"]
            constraints = inputs.get("constraints", [])
            task_id = inputs.get("task_id", f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
            
            # 계획 생성
            plan_artifact = self._create_plan(task_id, requirements, constraints)
            
            # DAG 검증
            if not plan_artifact.validate_dag():
                raise ValueError("Generated plan contains circular dependencies")
            
            self._set_status("completed")
            self._log(f"Plan generated successfully with {len(plan_artifact.steps)} steps")
            
            return {
                "status": "success",
                "artifact": plan_artifact,
                "agent": self.name
            }
            
        except Exception as e:
            self._add_error(str(e))
            self._set_status("failed")
            return {
                "status": "failed",
                "error": str(e),
                "agent": self.name
            }
    
    def _create_plan(self, task_id: str, requirements: str, constraints: list) -> PlanArtifact:
        """계획 아티팩트 생성 (실제로는 LLM 호출 등)"""
        
        # 요구사항 분석 (간단한 예시)
        goal = self._extract_goal(requirements)
        success_criteria = self._extract_success_criteria(requirements)
        steps = self._generate_steps(requirements)
        
        plan = PlanArtifact(
            task_id=task_id,
            goal=goal,
            success_criteria=success_criteria,
            steps=steps,
            constraints=constraints
        )
        
        return plan
    
    def _extract_goal(self, requirements: str) -> str:
        """요구사항에서 목표 추출"""
        # 실제로는 NLP 처리
        return requirements.split('.')[0] if requirements else "Undefined goal"
    
    def _extract_success_criteria(self, requirements: str) -> list:
        """성공 기준 추출"""
        # 실제로는 더 정교한 분석
        criteria = [
            "모든 요구사항이 충족됨",
            "품질 기준을 만족함",
            "검증 테스트를 통과함"
        ]
        return criteria
    
    def _generate_steps(self, requirements: str) -> list:
        """작업 단계 생성"""
        # 표준 5단계 파이프라인
        steps = [
            PlanStep(
                step_id="step_planning",
                description="요구사항 분석 및 계획 수립",
                depends_on=[],
                owner_agent="planner"
            ),
            PlanStep(
                step_id="step_context",
                description="배경 맥락 및 제약사항 수집",
                depends_on=["step_planning"],
                owner_agent="context"
            ),
            PlanStep(
                step_id="step_build",
                description="초안 생성",
                depends_on=["step_planning", "step_context"],
                owner_agent="builder"
            ),
            PlanStep(
                step_id="step_review",
                description="품질 검토 및 검증",
                depends_on=["step_build"],
                owner_agent="reviewer"
            ),
            PlanStep(
                step_id="step_finalize",
                description="최종 산출물 패키징",
                depends_on=["step_review"],
                owner_agent="finalizer"
            )
        ]
        return steps
