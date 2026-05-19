"""
Context Agent Implementation

배경 맥락, 제약사항, 참조 자료를 수집하는 에이전트
"""

from typing import Dict, Any
from .base import BaseAgent
from ..artifacts.context import ContextArtifact, Reference
from ..artifacts.plan import PlanArtifact


class ContextAgent(BaseAgent):
    """맥락 수집 에이전트"""
    
    def __init__(self):
        super().__init__("context")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        배경 맥락 수집
        
        Args:
            inputs: {
                "plan": PlanArtifact - 계획 아티팩트,
                "additional_context": Dict (선택)
            }
            
        Returns:
            Dict containing ContextArtifact
        """
        self._set_status("running")
        self._log("Starting context collection")
        
        try:
            # 입력 검증
            if "plan" not in inputs:
                raise ValueError("plan artifact is required")
            
            plan: PlanArtifact = inputs["plan"]
            additional_context = inputs.get("additional_context", {})
            
            # 맥락 수집
            context_artifact = self._collect_context(plan, additional_context)
            
            # 충돌 검사
            self._detect_conflicts(context_artifact)
            
            self._set_status("completed")
            self._log(f"Context collected: {len(context_artifact.references)} references")
            
            return {
                "status": "success",
                "artifact": context_artifact,
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
    
    def _collect_context(self, plan: PlanArtifact, additional: dict) -> ContextArtifact:
        """맥락 정보 수집"""
        
        # 가정 수립
        assumptions = self._establish_assumptions(plan)
        
        # 참조 자료 수집
        references = self._gather_references(plan)
        
        # 미해결 질문 식별
        open_questions = self._identify_open_questions(plan)
        
        context = ContextArtifact(
            task_id=plan.task_id,
            assumptions=assumptions,
            constraints=plan.constraints,
            references=references,
            open_questions=open_questions
        )
        
        return context
    
    def _establish_assumptions(self, plan: PlanArtifact) -> list:
        """기본 가정 수립"""
        assumptions = [
            "모든 입력 데이터는 유효함",
            "처리 환경은 안정적임",
            f"목표: {plan.goal}"
        ]
        return assumptions
    
    def _gather_references(self, plan: PlanArtifact) -> list:
        """참조 자료 수집 (실제로는 DB, API 호출 등)"""
        references = [
            Reference(
                source_id="internal_docs",
                summary="내부 문서 및 가이드라인",
                confidence=0.9
            ),
            Reference(
                source_id="best_practices",
                summary="업계 모범 사례",
                confidence=0.85
            )
        ]
        return references
    
    def _identify_open_questions(self, plan: PlanArtifact) -> list:
        """미해결 질문 식별"""
        questions = []
        
        # 제약사항이 부족한 경우
        if len(plan.constraints) < 2:
            questions.append("추가적인 제약사항이 필요한가?")
        
        return questions
    
    def _detect_conflicts(self, context: ContextArtifact):
        """제약사항 충돌 감지"""
        # 간단한 충돌 패턴 검사
        constraints_lower = [c.lower() for c in context.constraints]
        
        conflict_patterns = [
            ("짧게", "상세하게"),
            ("빠르게", "정밀하게"),
            ("간단하게", "복잡하게")
        ]
        
        for pattern1, pattern2 in conflict_patterns:
            has_first = any(pattern1 in c for c in constraints_lower)
            has_second = any(pattern2 in c for c in constraints_lower)
            
            if has_first and has_second:
                context.conflict_flags.append(
                    f"충돌 감지: '{pattern1}'와 '{pattern2}' 동시 요구"
                )
