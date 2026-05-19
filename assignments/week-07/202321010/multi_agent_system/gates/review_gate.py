"""
Review Gate

검토 단계 검증 게이트
"""

from .base_gate import BaseGate, ValidationResult
from ..artifacts.review import ReviewArtifact


class ReviewGate(BaseGate):
    """검토 검증 게이트"""
    
    def __init__(self):
        super().__init__("review_gate")
        self.checklist = [
            "high severity issue가 남아 있는가",
            "리뷰 코멘트가 actionable 한가",
            "검토 기준별 pass/fail이 기록되었는가",
            "false alarm 가능성이 과도하지 않은가"
        ]
    
    def validate(self, artifact: ReviewArtifact) -> ValidationResult:
        """
        검토 아티팩트 검증
        
        검증 항목:
        - 검토 완료 여부
        - 크리티컬 이슈 처리
        - 체크 결과 존재
        - 승인 가능 여부
        """
        result = ValidationResult(passed=True, gate_name=self.name)
        
        # 1. 검토 상태 확인
        if artifact.status not in ["approved", "rejected", "conditional"]:
            result.add_error(f"유효하지 않은 검토 상태: {artifact.status}")
        
        # 2. 체크 결과 확인
        if not artifact.check_results or len(artifact.check_results) == 0:
            result.add_error("검증 체크 결과가 없음")
        else:
            failed_checks = [
                check for check in artifact.check_results 
                if not check.passed
            ]
            if failed_checks:
                result.add_warning(
                    f"{len(failed_checks)}개의 체크가 실패함: " +
                    ", ".join(c.check_name for c in failed_checks[:3])
                )
        
        # 3. 크리티컬 이슈 확인
        critical_issues = artifact.get_critical_issues()
        if critical_issues and len(critical_issues) > 0:
            if artifact.status == "approved":
                result.add_error(
                    "승인 상태이지만 크리티컬 이슈가 존재함"
                )
            result.add_warning(
                f"{len(critical_issues)}개의 크리티컬 이슈 존재"
            )
        
        # 4. 블로킹 이슈 확인
        blocking_issues = artifact.get_blocking_issues()
        if blocking_issues and len(blocking_issues) > 0:
            result.add_error(
                f"{len(blocking_issues)}개의 블로킹 이슈가 해결되지 않음"
            )
        
        # 5. 품질 점수 확인
        if artifact.overall_quality < 0.6:
            result.add_error(
                f"전체 품질 점수 미달: {artifact.overall_quality:.2f}"
            )
        elif artifact.overall_quality < 0.75:
            result.add_warning(
                f"품질 점수: {artifact.overall_quality:.2f} (권장: 0.75 이상)"
            )
        
        # 6. 이슈 액션 가능성 확인
        if artifact.issues:
            issues_without_fix = [
                issue for issue in artifact.issues 
                if not issue.suggested_fix or len(issue.suggested_fix.strip()) < 5
            ]
            if issues_without_fix:
                result.add_warning(
                    f"{len(issues_without_fix)}개의 이슈에 수정 제안이 없음"
                )
        
        # 7. 승인 가능 여부 확인
        if not artifact.is_acceptable():
            result.add_warning("현재 상태로는 승인 불가")
        
        return result
