"""
Builder Agent Implementation

실제 초안/결과물을 생성하는 에이전트
"""

from typing import Dict, Any
from .base import BaseAgent
from ..artifacts.draft import DraftArtifact, DraftContent, Section, CoverageItem
from ..artifacts.plan import PlanArtifact
from ..artifacts.context import ContextArtifact


class BuilderAgent(BaseAgent):
    """초안 생성 에이전트"""
    
    def __init__(self):
        super().__init__("builder")
    
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        초안 생성
        
        Args:
            inputs: {
                "plan": PlanArtifact - 계획 아티팩트,
                "context": ContextArtifact - 맥락 아티팩트
            }
            
        Returns:
            Dict containing DraftArtifact
        """
        self._set_status("running")
        self._log("Starting draft generation")
        
        try:
            # 입력 검증
            if "plan" not in inputs or "context" not in inputs:
                raise ValueError("plan and context artifacts are required")
            
            plan: PlanArtifact = inputs["plan"]
            context: ContextArtifact = inputs["context"]
            
            # 초안 생성
            draft_artifact = self._build_draft(plan, context)
            
            # 커버리지 검증
            coverage_rate = draft_artifact.calculate_coverage_rate()
            self._log(f"Coverage rate: {coverage_rate:.2%}")
            
            if coverage_rate < 0.8:
                self._log("Warning: Coverage rate below 80%", level="warning")
            
            self._set_status("completed")
            self._log(f"Draft generated with {len(draft_artifact.content.sections)} sections")
            
            return {
                "status": "success",
                "artifact": draft_artifact,
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
    
    def _build_draft(self, plan: PlanArtifact, context: ContextArtifact) -> DraftArtifact:
        """초안 아티팩트 생성"""
        
        # 콘텐츠 생성
        content = self._generate_content(plan, context)
        
        # 커버리지 맵 생성
        coverage_map = self._create_coverage_map(plan)
        
        # 품질 점수 계산
        quality_score = self._calculate_quality_score(content, coverage_map)
        
        draft = DraftArtifact(
            task_id=plan.task_id,
            content=content,
            coverage_map=coverage_map,
            quality_score=quality_score
        )
        
        return draft
    
    def _generate_content(self, plan: PlanArtifact, context: ContextArtifact) -> DraftContent:
        """실제 콘텐츠 생성 (실제로는 LLM 생성)"""
        
        sections = [
            Section(
                section_id="sec_intro",
                heading="1. 개요",
                body=f"본 문서는 '{plan.goal}'를 목표로 작성되었습니다. "
                     f"수집된 참조 자료는 총 {len(context.references)}개입니다. "
                     f"본 분석은 다음과 같은 성공 기준을 충족하기 위해 수행되었습니다: "
                     f"{', '.join(plan.success_criteria[:2])}. "
                     f"분석 과정에서는 여러 가정과 제약사항을 고려하였으며, "
                     f"각 단계별로 철저한 검증을 거쳤습니다."
            ),
            Section(
                section_id="sec_analysis",
                heading="2. 분석",
                body="상세 분석 내용이 여기에 포함됩니다. "
                     "데이터 처리 및 인사이트 도출 과정을 설명합니다. "
                     "수집된 데이터는 여러 차원에서 검토되었으며, "
                     "각 카테고리별로 분류하여 패턴을 분석하였습니다. "
                     "통계적 방법론을 활용하여 주요 트렌드를 식별하고, "
                     "이를 바탕으로 실질적인 인사이트를 도출하였습니다. "
                     "분석 결과는 다음 섹션에서 상세히 다룹니다."
            ),
            Section(
                section_id="sec_findings",
                heading="3. 주요 발견사항",
                body="핵심 발견사항과 패턴을 정리합니다. "
                     "첫째, 데이터에서 반복적으로 나타나는 특정 패턴을 확인하였습니다. "
                     "둘째, 예상하지 못한 흥미로운 상관관계를 발견하였습니다. "
                     "셋째, 개선이 필요한 여러 영역을 식별하였습니다. "
                     "이러한 발견사항들은 향후 전략 수립에 중요한 기초 자료로 활용될 수 있습니다. "
                     "각 발견사항은 데이터 분석을 통해 검증되었으며, 신뢰할 수 있는 결과입니다."
            ),
            Section(
                section_id="sec_recommendations",
                heading="4. 권장사항",
                body="실행 가능한 권장사항을 제시합니다. "
                     "분석 결과를 바탕으로 다음과 같은 구체적인 행동 계획을 제안합니다. "
                     "첫째, 단기적으로 즉시 실행 가능한 개선 방안을 마련합니다. "
                     "둘째, 중장기적 관점에서 지속 가능한 변화를 위한 로드맵을 수립합니다. "
                     "셋째, 각 권장사항의 우선순위를 정하고 실행 계획을 구체화합니다. "
                     "이러한 권장사항들은 조직의 목표 달성에 기여할 것입니다."
            ),
            Section(
                section_id="sec_conclusion",
                heading="5. 결론",
                body=f"본 보고서는 다음과 같은 성공 기준을 달성하였습니다: "
                     f"{', '.join(plan.success_criteria[:2])}. "
                     f"분석을 통해 도출된 인사이트와 권장사항은 실질적인 가치를 제공합니다. "
                     f"향후 지속적인 모니터링과 피드백을 통해 개선해 나갈 것을 권장합니다. "
                     f"본 분석이 의사결정에 유용한 정보로 활용되기를 기대합니다."
            )
        ]
        
        content = DraftContent(
            title=f"{plan.goal} - 초안",
            sections=sections,
            metadata={
                "section_count": len(sections),
                "estimated_words": 2500
            }
        )
        
        return content
    
    def _create_coverage_map(self, plan: PlanArtifact) -> list:
        """요구사항 커버리지 맵 생성"""
        coverage_items = []
        
        for idx, criterion in enumerate(plan.success_criteria):
            coverage_items.append(
                CoverageItem(
                    requirement=criterion,
                    covered=True,  # 실제로는 검증 필요
                    evidence=f"섹션 {idx + 2}에서 다룸"
                )
            )
        
        return coverage_items
    
    def _calculate_quality_score(self, content: DraftContent, coverage_map: list) -> float:
        """품질 점수 계산"""
        # 간단한 휴리스틱
        score = 0.0
        
        # 섹션 수
        if len(content.sections) >= 4:
            score += 0.3
        
        # 커버리지
        covered = sum(1 for item in coverage_map if item.covered)
        if coverage_map:
            score += 0.4 * (covered / len(coverage_map))
        
        # 콘텐츠 길이
        total_body_length = sum(len(sec.body) for sec in content.sections)
        if total_body_length > 500:
            score += 0.3
        
        return min(score, 1.0)
