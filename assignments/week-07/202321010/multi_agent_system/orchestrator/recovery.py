"""
Error Recovery Strategy Module

3가지 주요 에러 시나리오에 대한 복구 전략 구현
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class RecoveryAction(Enum):
    """복구 액션 타입"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    MANUAL = "manual"
    FALLBACK = "fallback"


class RecoveryResult:
    """복구 결과"""
    
    def __init__(self, success: bool, action: RecoveryAction, message: str):
        self.success = success
        self.action = action
        self.message = message
        self.timestamp = datetime.utcnow().isoformat()
        self.retry_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "action": self.action.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count
        }


class ErrorRecoveryStrategy:
    """에러 복구 전략 기본 클래스"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.recovery_history: list = []
    
    def handle_error(self, error_type: str, context: Dict[str, Any]) -> RecoveryResult:
        """
        에러 처리
        
        Args:
            error_type: 에러 타입
            context: 에러 컨텍스트
            
        Returns:
            RecoveryResult: 복구 결과
        """
        if error_type == "schema_mismatch":
            return self._handle_schema_mismatch(context)
        elif error_type == "context_conflict":
            return self._handle_context_conflict(context)
        elif error_type == "gate_failure":
            return self._handle_gate_failure(context)
        else:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.MANUAL,
                message=f"Unknown error type: {error_type}"
            )
    
    def _handle_schema_mismatch(self, context: Dict[str, Any]) -> RecoveryResult:
        """
        시나리오 1: 스키마 불일치 처리
        
        상황:
        - Builder가 DraftArtifact 생성 시 필수 필드 누락
        - JSON 파싱 실패
        - 타입 오류 발생
        
        복구 전략:
        - 해당 산출물 reject
        - validation error log 생성
        - Builder Agent에 자동 수정 프롬프트 전달
        - 최대 N회 재시도
        - 실패 지속 시 fallback 템플릿 사용
        """
        retry_count = context.get("retry_count", 0)
        error_details = context.get("error_details", "")
        
        # 재시도 횟수 초과
        if retry_count >= self.max_retries:
            self._log_recovery("schema_mismatch", "fallback", context)
            return RecoveryResult(
                success=True,
                action=RecoveryAction.FALLBACK,
                message=f"Max retries exceeded. Using fallback template. "
                       f"Original error: {error_details}"
            )
        
        # 동일 오류 2회 반복 시 프롬프트 강화
        if retry_count >= 2:
            context["prompt_hardening"] = True
            self._log_recovery("schema_mismatch", "retry_with_hardening", context)
            return RecoveryResult(
                success=True,
                action=RecoveryAction.RETRY,
                message=f"Retrying with prompt hardening (attempt {retry_count + 1}/{self.max_retries})"
            )
        
        # 일반 재시도
        self._log_recovery("schema_mismatch", "retry", context)
        result = RecoveryResult(
            success=True,
            action=RecoveryAction.RETRY,
            message=f"Retrying artifact generation (attempt {retry_count + 1}/{self.max_retries})"
        )
        result.retry_count = retry_count + 1
        
        return result
    
    def _handle_context_conflict(self, context: Dict[str, Any]) -> RecoveryResult:
        """
        시나리오 2: 상충된 컨텍스트 처리
        
        상황:
        - Context Agent가 서로 모순되는 제약을 수집
        - 예: "길이는 짧게" / "반드시 상세하게"
        
        복구 전략:
        - 충돌 항목을 conflict_flags에 기록
        - 우선순위 정책 적용 (시스템 정책 > 사용자 정책 > 기본 정책)
        - 해소 가능한 충돌은 자동 조정
        - 해소 불가 시 Planner로 되돌려 재계획
        """
        conflict_items = context.get("conflict_items", [])
        priority_policy = context.get("priority_policy", "system")
        
        if not conflict_items:
            return RecoveryResult(
                success=False,
                action=RecoveryAction.MANUAL,
                message="No conflict items provided"
            )
        
        # 우선순위 정책 적용
        resolved_conflicts = self._apply_priority_policy(conflict_items, priority_policy)
        
        # 모든 충돌 해소됨
        if resolved_conflicts["unresolved_count"] == 0:
            self._log_recovery("context_conflict", "resolved", context)
            return RecoveryResult(
                success=True,
                action=RecoveryAction.RETRY,
                message=f"All {len(conflict_items)} conflicts resolved using {priority_policy} policy. "
                       f"Resolutions: {resolved_conflicts['resolutions']}"
            )
        
        # 일부 충돌 미해결
        if resolved_conflicts["unresolved_count"] < len(conflict_items):
            self._log_recovery("context_conflict", "partial", context)
            return RecoveryResult(
                success=True,
                action=RecoveryAction.ROLLBACK,
                message=f"{resolved_conflicts['unresolved_count']} conflicts remain unresolved. "
                       f"Rolling back to Planner for re-planning."
            )
        
        # 모든 충돌 미해결
        self._log_recovery("context_conflict", "failed", context)
        return RecoveryResult(
            success=False,
            action=RecoveryAction.MANUAL,
            message="Unable to resolve conflicts automatically. Manual intervention required."
        )
    
    def _handle_gate_failure(self, context: Dict[str, Any]) -> RecoveryResult:
        """
        시나리오 3: 리뷰 게이트 실패 처리
        
        상황:
        - Reviewer가 high severity issue 발견
        - 예: 요구사항 2개 미반영, 근거 누락, 형식 오류
        
        복구 전략:
        - 실패 원인을 이슈 목록으로 구조화
        - Builder로 수정 루프 전송
        - 수정 범위만 부분 재실행 (incremental patch)
        - 재리뷰 후 통과 시 Finalizer로 진행
        
        장점:
        - 비용 절감
        - 처리 시간 감소
        - 이미 검증된 부분 재사용 가능
        """
        issues = context.get("issues", [])
        gate_name = context.get("gate_name", "unknown")
        severity_counts = context.get("severity_counts", {})
        
        # 크리티컬 이슈 존재 시 전체 재실행
        if severity_counts.get("critical", 0) > 0:
            self._log_recovery("gate_failure", "full_retry", context)
            return RecoveryResult(
                success=True,
                action=RecoveryAction.ROLLBACK,
                message=f"Critical issues found in {gate_name}. Full retry required. "
                       f"Issues: {severity_counts}"
            )
        
        # High severity 이슈만 존재 시 부분 재실행
        if severity_counts.get("high", 0) > 0:
            fixable_issues = self._identify_fixable_issues(issues)
            
            if fixable_issues:
                self._log_recovery("gate_failure", "incremental_fix", context)
                return RecoveryResult(
                    success=True,
                    action=RecoveryAction.RETRY,
                    message=f"Applying incremental fixes for {len(fixable_issues)} issues. "
                           f"Fixable: {', '.join(i.get('issue_id', 'unknown') for i in fixable_issues[:3])}"
                )
        
        # Medium 이하 이슈만 존재 시 조건부 통과
        if severity_counts.get("high", 0) == 0 and severity_counts.get("critical", 0) == 0:
            self._log_recovery("gate_failure", "conditional_pass", context)
            return RecoveryResult(
                success=True,
                action=RecoveryAction.SKIP,
                message=f"Only medium/low issues found. Proceeding with conditional approval. "
                       f"Issues logged for tracking."
            )
        
        # 기타
        return RecoveryResult(
            success=False,
            action=RecoveryAction.MANUAL,
            message=f"Gate {gate_name} failure requires manual review"
        )
    
    def _apply_priority_policy(self, conflicts: list, policy: str) -> Dict:
        """
        우선순위 정책 적용하여 충돌 해소
        """
        resolutions = []
        unresolved = []
        
        for conflict in conflicts:
            # 간단한 규칙 기반 해소
            if "짧게" in conflict and "상세하게" in conflict:
                if policy == "system":
                    resolutions.append({
                        "conflict": conflict,
                        "resolution": "상세 본문 + 요약 상단 제공"
                    })
                else:
                    unresolved.append(conflict)
            else:
                unresolved.append(conflict)
        
        return {
            "resolutions": resolutions,
            "unresolved": unresolved,
            "unresolved_count": len(unresolved)
        }
    
    def _identify_fixable_issues(self, issues: list) -> list:
        """수정 가능한 이슈 식별"""
        fixable = []
        
        for issue in issues:
            # suggested_fix가 있는 이슈는 수정 가능
            if issue.get("suggested_fix") and len(issue.get("suggested_fix", "")) > 5:
                fixable.append(issue)
        
        return fixable
    
    def _log_recovery(self, error_type: str, action: str, context: Dict):
        """복구 이력 기록"""
        self.recovery_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "action": action,
            "context_summary": {
                "retry_count": context.get("retry_count", 0),
                "gate_name": context.get("gate_name", "N/A")
            }
        })
    
    def get_recovery_history(self) -> list:
        """복구 이력 반환"""
        return self.recovery_history
    
    def get_recovery_statistics(self) -> Dict:
        """복구 통계 반환"""
        total = len(self.recovery_history)
        
        if total == 0:
            return {"total": 0, "by_type": {}, "by_action": {}}
        
        by_type = {}
        by_action = {}
        
        for record in self.recovery_history:
            error_type = record["error_type"]
            action = record["action"]
            
            by_type[error_type] = by_type.get(error_type, 0) + 1
            by_action[action] = by_action.get(action, 0) + 1
        
        return {
            "total": total,
            "by_type": by_type,
            "by_action": by_action
        }
