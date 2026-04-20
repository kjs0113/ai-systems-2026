"""
Planning Gate

계획 단계 검증 게이트
"""

from .base_gate import BaseGate, ValidationResult
from ..artifacts.plan import PlanArtifact


class PlanningGate(BaseGate):
    """계획 검증 게이트"""
    
    def __init__(self):
        super().__init__("planning_gate")
        self.checklist = [
            "요구사항이 모두 식별되었는가",
            "성공 기준이 명시되었는가",
            "단계 간 의존성이 정의되었는가",
            "실행 불가능한 작업이 포함되지 않았는가",
            "출력 아티팩트 형식이 정의되었는가"
        ]
    
    def validate(self, artifact: PlanArtifact) -> ValidationResult:
        """
        계획 아티팩트 검증
        
        검증 항목:
        - 필수 필드 존재
        - 성공 기준 정의됨
        - 단계 의존성 순환 없음
        - 최소 단계 수
        """
        result = ValidationResult(passed=True, gate_name=self.name)
        
        # 1. 목표 정의 확인
        if not artifact.goal or len(artifact.goal.strip()) < 10:
            result.add_error("목표가 명확하게 정의되지 않음")
        
        # 2. 성공 기준 확인
        if not artifact.success_criteria or len(artifact.success_criteria) == 0:
            result.add_error("성공 기준이 정의되지 않음")
        elif len(artifact.success_criteria) < 2:
            result.add_warning("성공 기준이 2개 미만입니다")
        
        # 3. 단계 정의 확인
        if not artifact.steps or len(artifact.steps) == 0:
            result.add_error("작업 단계가 정의되지 않음")
        elif len(artifact.steps) < 3:
            result.add_warning("작업 단계가 3개 미만입니다")
        
        # 4. DAG 순환 참조 확인
        if not artifact.validate_dag():
            result.add_error("단계 의존성에 순환 참조가 존재함")
        
        # 5. 각 단계의 소유자 확인
        for step in artifact.steps:
            if not step.owner_agent:
                result.add_error(f"단계 '{step.step_id}'의 소유자가 지정되지 않음")
        
        # 6. 제약사항 확인
        if len(artifact.constraints) == 0:
            result.add_warning("제약사항이 명시되지 않았습니다")
        
        return result
