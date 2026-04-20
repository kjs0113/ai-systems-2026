"""
Release Gate

최종 배포 검증 게이트
"""

from .base_gate import BaseGate, ValidationResult
from ..artifacts.final import FinalArtifact


class ReleaseGate(BaseGate):
    """배포 검증 게이트"""
    
    def __init__(self):
        super().__init__("release_gate")
        self.checklist = [
            "모든 필수 게이트 통과 기록이 있는가",
            "최종 메타데이터가 기록되었는가",
            "산출물 버전이 고정되었는가",
            "재현 가능한 실행 이력이 있는가",
            "실패/수정 로그가 보존되었는가"
        ]
    
    def validate(self, artifact: FinalArtifact) -> ValidationResult:
        """
        최종 산출물 검증
        
        검증 항목:
        - 배포 가능 플래그
        - 감사 추적 완성도
        - 메타데이터 존재
        - 필수 단계 완료
        """
        result = ValidationResult(passed=True, gate_name=self.name)
        
        # 1. 배포 가능 플래그 확인
        if not artifact.releaseable:
            result.add_error("배포 불가 상태로 표시됨")
        
        # 2. 최종 콘텐츠 확인
        if not artifact.final_content or len(artifact.final_content) == 0:
            result.add_error("최종 콘텐츠가 없음")
        else:
            if "title" not in artifact.final_content:
                result.add_warning("최종 콘텐츠에 제목이 없음")
            if "sections" not in artifact.final_content:
                result.add_warning("최종 콘텐츠에 섹션 정보가 없음")
        
        # 3. 감사 추적 확인
        if not artifact.audit_trail or len(artifact.audit_trail) == 0:
            result.add_error("감사 추적 로그가 없음")
        else:
            # 필수 단계 확인
            required_stages = ["planning", "review", "finalization"]
            logged_stages = {log.stage for log in artifact.audit_trail}
            missing_stages = [
                stage for stage in required_stages 
                if stage not in logged_stages
            ]
            if missing_stages:
                result.add_warning(
                    f"감사 로그에 누락된 단계: {', '.join(missing_stages)}"
                )
            
            # 실패 단계 확인
            failed_stages = [
                log for log in artifact.audit_trail 
                if log.status in ["failed", "rejected"]
            ]
            if failed_stages:
                result.add_warning(
                    f"{len(failed_stages)}개의 단계가 실패/거부 상태"
                )
        
        # 4. 메타데이터 확인
        if not artifact.metadata or len(artifact.metadata) == 0:
            result.add_warning("메타데이터가 비어있음")
        else:
            # 필수 메타데이터 필드
            recommended_fields = [
                "finalized_at", "final_quality_score", "total_issues"
            ]
            missing_fields = [
                field for field in recommended_fields 
                if field not in artifact.metadata
            ]
            if missing_fields:
                result.add_warning(
                    f"권장 메타데이터 누락: {', '.join(missing_fields)}"
                )
        
        # 5. 승인 노트 확인
        if not artifact.approval_notes or len(artifact.approval_notes.strip()) < 5:
            result.add_warning("승인 노트가 없거나 너무 짧음")
        
        # 6. 버전 정보 확인
        if not artifact.version:
            result.add_error("버전 정보가 없음")
        
        # 7. 타임스탬프 확인
        if not artifact.created_at:
            result.add_error("생성 시각 정보가 없음")
        
        return result
