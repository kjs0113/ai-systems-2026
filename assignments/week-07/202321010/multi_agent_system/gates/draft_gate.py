"""
Draft Gate

초안 생성 단계 검증 게이트
"""

from .base_gate import BaseGate, ValidationResult
from ..artifacts.draft import DraftArtifact


class DraftGate(BaseGate):
    """초안 검증 게이트"""
    
    def __init__(self, min_coverage: float = 0.8, min_quality: float = 0.7):
        super().__init__("draft_gate")
        self.min_coverage = min_coverage
        self.min_quality = min_quality
        self.checklist = [
            "DraftArtifact 스키마를 만족하는가",
            "모든 요구사항이 coverage map에 반영되었는가",
            "섹션 구조가 완전한가",
            "필수 필드가 비어 있지 않은가",
            "금지된 내용/형식 오류가 없는가"
        ]
    
    def validate(self, artifact: DraftArtifact) -> ValidationResult:
        """
        초안 아티팩트 검증
        
        검증 항목:
        - 스키마 유효성
        - 요구사항 커버리지
        - 필수 섹션 존재
        - 품질 점수
        - 콘텐츠 완성도
        """
        result = ValidationResult(passed=True, gate_name=self.name)
        
        # 1. 기본 필드 확인
        if not artifact.content or not artifact.content.title:
            result.add_error("콘텐츠 제목이 없음")
        
        if not artifact.content.sections or len(artifact.content.sections) == 0:
            result.add_error("섹션이 없음")
        
        # 2. 커버리지 확인
        if not artifact.coverage_map or len(artifact.coverage_map) == 0:
            result.add_error("요구사항 커버리지 맵이 없음")
        else:
            coverage_rate = artifact.calculate_coverage_rate()
            if coverage_rate < self.min_coverage:
                result.add_error(
                    f"요구사항 커버리지 부족: {coverage_rate:.1%} < {self.min_coverage:.1%}"
                )
            elif coverage_rate < 0.9:
                result.add_warning(
                    f"요구사항 커버리지: {coverage_rate:.1%} (권장: 90% 이상)"
                )
        
        # 3. 필수 섹션 확인
        required_sections = ["sec_intro", "sec_conclusion"]
        if artifact.content.sections:
            section_ids = {sec.section_id for sec in artifact.content.sections}
            missing_sections = [sid for sid in required_sections if sid not in section_ids]
            if missing_sections:
                result.add_error(
                    f"필수 섹션 누락: {', '.join(missing_sections)}"
                )
        
        # 4. 품질 점수 확인
        if artifact.quality_score < self.min_quality:
            result.add_error(
                f"품질 점수 미달: {artifact.quality_score:.2f} < {self.min_quality:.2f}"
            )
        elif artifact.quality_score < 0.8:
            result.add_warning(
                f"품질 점수: {artifact.quality_score:.2f} (권장: 0.8 이상)"
            )
        
        # 5. 콘텐츠 길이 확인
        if artifact.content.sections:
            total_length = sum(len(sec.body) for sec in artifact.content.sections)
            if total_length < 300:
                result.add_error(f"콘텐츠가 너무 짧음: {total_length} chars")
            elif total_length < 500:
                result.add_warning(f"콘텐츠 길이: {total_length} chars (권장: 500 이상)")
        
        # 6. 각 섹션의 완성도 확인
        if artifact.content.sections:
            empty_sections = [
                sec.section_id for sec in artifact.content.sections 
                if not sec.body or len(sec.body.strip()) < 10
            ]
            if empty_sections:
                result.add_error(
                    f"빈 섹션 존재: {', '.join(empty_sections)}"
                )
        
        return result
