"""
Finalizer Agent Implementation

최종 산출물을 패키징하고 승인하는 에이전트
"""

from typing import Dict, Any
from .base import BaseAgent
from ..artifacts.final import FinalArtifact, ExecutionLog
from ..artifacts.draft import DraftArtifact
from ..artifacts.review import ReviewArtifact


class FinalizerAgent(BaseAgent):
    """최종화 에이전트"""
    
    def __init__(self):
        super().__init__("finalizer")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        최종 산출물 생성
        
        Args:
            inputs: {
                "draft": DraftArtifact - 초안 아티팩트,
                "review": ReviewArtifact - 검토 아티팩트,
                "audit_trail": List[ExecutionLog] - 감사 추적 (선택)
            }
            
        Returns:
            Dict containing FinalArtifact
        """
        self._set_status("running")
        self._log("Starting finalization")
        
        try:
            # 입력 검증
            if "draft" not in inputs or "review" not in inputs:
                raise ValueError("draft and review artifacts are required")
            
            draft: DraftArtifact = inputs["draft"]
            review: ReviewArtifact = inputs["review"]
            audit_trail = inputs.get("audit_trail", [])
            
            # 최종화 수행
            final_artifact = self._finalize(draft, review, audit_trail)
            
            self._set_status("completed")
            self._log(f"Finalization completed: releaseable={final_artifact.releaseable}")
            
            return {
                "status": "success",
                "artifact": final_artifact,
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
    
    def _finalize(self, draft: DraftArtifact, review: ReviewArtifact, 
                  audit_trail: list) -> FinalArtifact:
        """최종 산출물 생성"""
        
        # 배포 가능 여부 결정
        releaseable = self._determine_releaseable(review)
        
        # 최종 콘텐츠 패키징
        final_content = self._package_content(draft, review)
        
        # 감사 추적 로그 완성
        complete_audit_trail = self._complete_audit_trail(audit_trail, review)
        
        # 메타데이터 생성
        metadata = self._generate_metadata(draft, review)
        
        # 승인 노트 생성
        approval_notes = self._generate_approval_notes(review, releaseable)
        
        final = FinalArtifact(
            task_id=draft.task_id,
            final_content=final_content,
            releaseable=releaseable,
            audit_trail=complete_audit_trail,
            metadata=metadata,
            approval_notes=approval_notes
        )
        
        return final
    
    def _determine_releaseable(self, review: ReviewArtifact) -> bool:
        """배포 가능 여부 결정"""
        # 승인되었거나 조건부 승인 + 크리티컬 이슈 없음
        if review.status == "approved":
            return True
        
        if review.status == "conditional":
            blocking_issues = review.get_blocking_issues()
            return len(blocking_issues) == 0
        
        return False
    
    def _package_content(self, draft: DraftArtifact, review: ReviewArtifact) -> dict:
        """최종 콘텐츠 패키징"""
        content = {
            "title": draft.content.title.replace("초안", "최종"),
            "sections": [
                {
                    "id": sec.section_id,
                    "heading": sec.heading,
                    "body": sec.body
                }
                for sec in draft.content.sections
            ],
            "metadata": draft.content.metadata,
            "quality_metrics": {
                "draft_quality": draft.quality_score,
                "review_quality": review.overall_quality,
                "coverage_rate": draft.calculate_coverage_rate()
            }
        }
        
        return content
    
    def _complete_audit_trail(self, partial_trail: list, review: ReviewArtifact) -> list:
        """감사 추적 로그 완성"""
        # 기존 로그 복사
        complete_trail = partial_trail.copy() if partial_trail else []
        
        # 최종 검토 로그 추가
        complete_trail.append(ExecutionLog(
            stage="review",
            status=review.status,
            timestamp=review.created_at,
            details=f"Issues: {len(review.issues)}, Quality: {review.overall_quality}"
        ))
        
        # 최종화 로그 추가
        from datetime import datetime
        complete_trail.append(ExecutionLog(
            stage="finalization",
            status="completed",
            timestamp=datetime.utcnow().isoformat(),
            details="최종 산출물 패키징 완료"
        ))
        
        return complete_trail
    
    def _generate_metadata(self, draft: DraftArtifact, review: ReviewArtifact) -> dict:
        """메타데이터 생성"""
        from datetime import datetime
        
        metadata = {
            "finalized_at": datetime.utcnow().isoformat(),
            "draft_version": draft.version,
            "review_status": review.status,
            "total_issues": len(review.issues),
            "critical_issues": len(review.get_critical_issues()),
            "final_quality_score": (draft.quality_score + review.overall_quality) / 2,
            "section_count": len(draft.content.sections),
            "coverage_rate": draft.calculate_coverage_rate()
        }
        
        return metadata
    
    def _generate_approval_notes(self, review: ReviewArtifact, releaseable: bool) -> str:
        """승인 노트 생성"""
        if releaseable:
            if review.status == "approved":
                return "모든 검증 통과, 배포 승인"
            else:
                return f"조건부 승인: {review.reviewer_notes}. 크리티컬 이슈 없음, 배포 가능"
        else:
            critical_count = len(review.get_critical_issues())
            return f"배포 불가: {critical_count}개의 크리티컬 이슈 해결 필요. {review.reviewer_notes}"
