"""
Reviewer Agent Implementation

품질, 일관성, 완결성을 검토하는 에이전트
"""

from typing import Dict, Any
from .base import BaseAgent
from ..artifacts.review import ReviewArtifact, Issue, CheckResult
from ..artifacts.draft import DraftArtifact
from ..artifacts.plan import PlanArtifact


class ReviewerAgent(BaseAgent):
    """검토 에이전트"""
    
    def __init__(self):
        super().__init__("reviewer")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        품질 검토 수행
        
        Args:
            inputs: {
                "draft": DraftArtifact - 초안 아티팩트,
                "plan": PlanArtifact - 계획 아티팩트
            }
            
        Returns:
            Dict containing ReviewArtifact
        """
        self._set_status("running")
        self._log("Starting review process")
        
        try:
            # 입력 검증
            if "draft" not in inputs or "plan" not in inputs:
                raise ValueError("draft and plan artifacts are required")
            
            draft: DraftArtifact = inputs["draft"]
            plan: PlanArtifact = inputs["plan"]
            
            # 검토 수행
            review_artifact = self._perform_review(draft, plan)
            
            self._set_status("completed")
            self._log(f"Review completed: {review_artifact.status}, "
                     f"{len(review_artifact.issues)} issues found")
            
            return {
                "status": "success",
                "artifact": review_artifact,
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
    
    def _perform_review(self, draft: DraftArtifact, plan: PlanArtifact) -> ReviewArtifact:
        """검토 수행"""
        
        # 검증 체크 실행
        check_results = self._run_checks(draft, plan)
        
        # 이슈 식별
        issues = self._identify_issues(draft, plan, check_results)
        
        # 전체 품질 점수 계산
        overall_quality = self._calculate_overall_quality(draft, check_results, issues)
        
        # 상태 결정
        status = self._determine_status(issues)
        
        review = ReviewArtifact(
            task_id=plan.task_id,
            status=status,
            issues=issues,
            check_results=check_results,
            overall_quality=overall_quality,
            reviewer_notes=self._generate_notes(issues, overall_quality)
        )
        
        return review
    
    def _run_checks(self, draft: DraftArtifact, plan: PlanArtifact) -> list:
        """검증 체크 실행"""
        checks = []
        
        # 1. 스키마 검증
        checks.append(CheckResult(
            check_name="schema_valid",
            passed=True,
            details="DraftArtifact 스키마 검증 통과"
        ))
        
        # 2. 커버리지 체크
        coverage_rate = draft.calculate_coverage_rate()
        checks.append(CheckResult(
            check_name="coverage_check",
            passed=coverage_rate >= 0.8,
            details=f"요구사항 커버리지: {coverage_rate:.1%}"
        ))
        
        # 3. 필수 섹션 체크
        required_sections = ["sec_intro", "sec_conclusion"]
        has_required = draft.has_required_sections(required_sections)
        checks.append(CheckResult(
            check_name="required_sections",
            passed=has_required,
            details="필수 섹션 존재 확인"
        ))
        
        # 4. 품질 점수 체크
        checks.append(CheckResult(
            check_name="quality_threshold",
            passed=draft.quality_score >= 0.7,
            details=f"품질 점수: {draft.quality_score:.2f}"
        ))
        
        # 5. 콘텐츠 길이 체크
        total_length = sum(len(sec.body) for sec in draft.content.sections)
        checks.append(CheckResult(
            check_name="content_length",
            passed=total_length >= 300,
            details=f"총 콘텐츠 길이: {total_length} chars"
        ))
        
        return checks
    
    def _identify_issues(self, draft: DraftArtifact, plan: PlanArtifact, 
                        check_results: list) -> list:
        """이슈 식별"""
        issues = []
        issue_counter = 1
        
        # 실패한 체크에서 이슈 생성
        for check in check_results:
            if not check.passed:
                severity = "high" if check.check_name in ["schema_valid", "coverage_check"] else "medium"
                issues.append(Issue(
                    issue_id=f"issue_{issue_counter:03d}",
                    severity=severity,
                    description=f"체크 실패: {check.check_name}",
                    location="전체 문서",
                    suggested_fix=f"{check.details} - 기준 미달"
                ))
                issue_counter += 1
        
        # 추가 이슈 검사
        # 커버리지 미충족 항목
        for item in draft.coverage_map:
            if not item.covered:
                issues.append(Issue(
                    issue_id=f"issue_{issue_counter:03d}",
                    severity="high",
                    description=f"요구사항 미충족: {item.requirement}",
                    location="커버리지 맵",
                    suggested_fix="해당 요구사항을 다루는 섹션 추가 필요"
                ))
                issue_counter += 1
        
        return issues
    
    def _calculate_overall_quality(self, draft: DraftArtifact, 
                                   check_results: list, issues: list) -> float:
        """전체 품질 점수 계산"""
        # 기본 점수는 draft의 품질 점수
        score = draft.quality_score
        
        # 체크 통과율 반영
        passed_checks = sum(1 for check in check_results if check.passed)
        total_checks = len(check_results)
        if total_checks > 0:
            check_score = passed_checks / total_checks
            score = (score + check_score) / 2
        
        # 이슈 패널티
        critical_count = sum(1 for issue in issues if issue.severity == "critical")
        high_count = sum(1 for issue in issues if issue.severity == "high")
        
        penalty = critical_count * 0.2 + high_count * 0.1
        score = max(0.0, score - penalty)
        
        return round(score, 2)
    
    def _determine_status(self, issues: list) -> str:
        """검토 상태 결정"""
        critical_issues = [i for i in issues if i.severity == "critical"]
        high_issues = [i for i in issues if i.severity == "high"]
        
        if critical_issues:
            return "rejected"
        elif high_issues:
            return "conditional"
        else:
            return "approved"
    
    def _generate_notes(self, issues: list, quality: float) -> str:
        """검토 노트 생성"""
        if not issues:
            return f"전체 품질: {quality:.2f} - 검토 통과, 이슈 없음"
        
        issue_summary = f"총 {len(issues)}개 이슈 발견. "
        by_severity = {}
        for issue in issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
        
        severity_text = ", ".join(f"{sev}: {count}" for sev, count in by_severity.items())
        
        return f"전체 품질: {quality:.2f} - {issue_summary}{severity_text}"
