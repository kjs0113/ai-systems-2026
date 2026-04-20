"""
Context Gate

맥락 수집 단계 검증 게이트
"""

from .base_gate import BaseGate, ValidationResult
from ..artifacts.context import ContextArtifact


class ContextGate(BaseGate):
    """맥락 검증 게이트"""
    
    def __init__(self):
        super().__init__("context_gate")
        self.checklist = [
            "필수 컨텍스트가 수집되었는가",
            "제약사항이 문서화되었는가",
            "상충하는 정보가 식별되었는가",
            "출처/근거가 기록되었는가",
            "open question이 남아 있는가"
        ]
    
    def validate(self, artifact: ContextArtifact) -> ValidationResult:
        """
        맥락 아티팩트 검증
        
        검증 항목:
        - 가정 정의됨
        - 참조 자료 존재
        - 충돌 플래그 처리
        - 미해결 질문 관리
        """
        result = ValidationResult(passed=True, gate_name=self.name)
        
        # 1. 기본 가정 확인
        if not artifact.assumptions or len(artifact.assumptions) == 0:
            result.add_warning("기본 가정이 명시되지 않음")
        
        # 2. 참조 자료 확인
        if not artifact.references or len(artifact.references) == 0:
            result.add_warning("참조 자료가 없습니다")
        else:
            # 신뢰도 확인
            low_confidence_refs = [
                ref for ref in artifact.references 
                if ref.confidence < 0.5
            ]
            if low_confidence_refs:
                result.add_warning(
                    f"{len(low_confidence_refs)}개의 참조 자료가 낮은 신뢰도(<0.5)를 가짐"
                )
        
        # 3. 제약사항 확인
        if not artifact.constraints or len(artifact.constraints) == 0:
            result.add_warning("제약사항이 명시되지 않음")
        
        # 4. 충돌 플래그 확인
        if artifact.conflict_flags and len(artifact.conflict_flags) > 0:
            result.add_error(
                f"{len(artifact.conflict_flags)}개의 충돌이 감지됨: " +
                ", ".join(artifact.conflict_flags[:2])
            )
        
        # 5. 미해결 질문 확인
        if artifact.open_questions and len(artifact.open_questions) > 3:
            result.add_warning(
                f"미해결 질문이 {len(artifact.open_questions)}개로 과다합니다"
            )
        
        # 6. 크리티컬 이슈 확인
        if artifact.has_critical_issues():
            result.add_error("크리티컬 컨텍스트 이슈가 존재함")
        
        return result
