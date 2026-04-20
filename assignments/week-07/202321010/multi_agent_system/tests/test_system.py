"""
Unit Tests for Multi-Agent System

주요 컴포넌트에 대한 단위 테스트
"""

import unittest
from multi_agent_system.artifacts.plan import PlanArtifact, PlanStep
from multi_agent_system.artifacts.context import ContextArtifact, Reference
from multi_agent_system.artifacts.draft import DraftArtifact, DraftContent, Section, CoverageItem
from multi_agent_system.artifacts.review import ReviewArtifact, Issue, CheckResult

from multi_agent_system.agents.planner import PlannerAgent
from multi_agent_system.gates.planning_gate import PlanningGate
from multi_agent_system.gates.draft_gate import DraftGate

from multi_agent_system.orchestrator.dag import AgentDAG
from multi_agent_system.orchestrator.recovery import ErrorRecoveryStrategy


class TestArtifacts(unittest.TestCase):
    """아티팩트 테스트"""
    
    def test_plan_artifact_creation(self):
        """PlanArtifact 생성 테스트"""
        plan = PlanArtifact(
            task_id="test_001",
            goal="테스트 목표",
            success_criteria=["기준1", "기준2"],
            steps=[
                PlanStep(
                    step_id="s1",
                    description="단계1",
                    depends_on=[],
                    owner_agent="agent1"
                )
            ]
        )
        
        self.assertEqual(plan.task_id, "test_001")
        self.assertEqual(len(plan.steps), 1)
        self.assertTrue(plan.validate_dag())
    
    def test_draft_coverage_calculation(self):
        """DraftArtifact 커버리지 계산 테스트"""
        draft = DraftArtifact(
            task_id="test_002",
            content=DraftContent(
                title="테스트",
                sections=[Section(section_id="s1", heading="제목", body="내용")]
            ),
            coverage_map=[
                CoverageItem(requirement="r1", covered=True, evidence="e1"),
                CoverageItem(requirement="r2", covered=False, evidence="e2"),
                CoverageItem(requirement="r3", covered=True, evidence="e3")
            ]
        )
        
        coverage = draft.calculate_coverage_rate()
        self.assertAlmostEqual(coverage, 2/3, places=2)


class TestAgents(unittest.TestCase):
    """에이전트 테스트"""
    
    def test_planner_agent(self):
        """Planner Agent 테스트"""
        planner = PlannerAgent()
        
        inputs = {
            "requirements": "테스트 요구사항을 처리하시오.",
            "constraints": ["제약1", "제약2"]
        }
        
        result = planner.run(inputs)
        
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["artifact"])
        self.assertIsInstance(result["artifact"], PlanArtifact)


class TestGates(unittest.TestCase):
    """게이트 테스트"""
    
    def test_planning_gate(self):
        """Planning Gate 테스트"""
        gate = PlanningGate()
        
        # 유효한 계획
        valid_plan = PlanArtifact(
            task_id="test_003",
            goal="명확한 목표 설명입니다",
            success_criteria=["기준1", "기준2"],
            steps=[
                PlanStep(step_id="s1", description="d1", depends_on=[], owner_agent="a1"),
                PlanStep(step_id="s2", description="d2", depends_on=["s1"], owner_agent="a2")
            ]
        )
        
        result = gate.validate(valid_plan)
        self.assertTrue(result.passed)
    
    def test_draft_gate(self):
        """Draft Gate 테스트"""
        gate = DraftGate(min_coverage=0.5, min_quality=0.5)
        
        draft = DraftArtifact(
            task_id="test_004",
            content=DraftContent(
                title="테스트 문서",
                sections=[
                    Section(section_id="sec_intro", heading="개요", body="충분한 길이의 본문 내용입니다. " * 20),
                    Section(section_id="sec_conclusion", heading="결론", body="결론 내용입니다. " * 20)
                ]
            ),
            coverage_map=[
                CoverageItem(requirement="r1", covered=True, evidence="e1")
            ],
            quality_score=0.8
        )
        
        result = gate.validate(draft)
        self.assertTrue(result.passed)



class TestDAG(unittest.TestCase):
    """DAG 테스트"""
    
    def test_dag_creation(self):
        """DAG 생성 테스트"""
        dag = AgentDAG()
        dag.build_standard_pipeline()
        
        self.assertGreater(dag.graph.number_of_nodes(), 0)
        self.assertTrue(dag.validate()[0])
    
    def test_tier_computation(self):
        """Tier 계산 테스트"""
        dag = AgentDAG()
        dag.build_standard_pipeline()
        
        tiers = dag.get_execution_order()
        self.assertGreater(len(tiers), 0)
        
        # 첫 번째 tier에는 planner가 있어야 함
        self.assertIn("planner", tiers[0])
    
    def test_parallelization_analysis(self):
        """병렬화 분석 테스트"""
        dag = AgentDAG()
        dag.build_standard_pipeline()
        
        analysis = dag.get_parallelization_analysis()
        
        self.assertIn("total_nodes", analysis)
        self.assertIn("total_tiers", analysis)
        self.assertIn("parallelization_efficiency", analysis)


class TestRecovery(unittest.TestCase):
    """복구 전략 테스트"""
    
    def test_schema_mismatch_recovery(self):
        """스키마 불일치 복구 테스트"""
        recovery = ErrorRecoveryStrategy(max_retries=3)
        
        # 첫 번째 시도
        result1 = recovery.handle_error("schema_mismatch", {"retry_count": 0})
        self.assertTrue(result1.success)
        self.assertEqual(result1.action.value, "retry")
        
        # 최대 재시도 초과
        result2 = recovery.handle_error("schema_mismatch", {"retry_count": 3})
        self.assertTrue(result2.success)
        self.assertEqual(result2.action.value, "fallback")
    
    def test_context_conflict_recovery(self):
        """컨텍스트 충돌 복구 테스트"""
        recovery = ErrorRecoveryStrategy()
        
        result = recovery.handle_error("context_conflict", {
            "conflict_items": ["짧게", "상세하게"],
            "priority_policy": "system"
        })
        
        self.assertIsNotNone(result)
    
    def test_gate_failure_recovery(self):
        """게이트 실패 복구 테스트"""
        recovery = ErrorRecoveryStrategy()
        
        result = recovery.handle_error("gate_failure", {
            "issues": [
                {"issue_id": "i1", "severity": "high", "suggested_fix": "수정"}
            ],
            "gate_name": "test_gate",
            "severity_counts": {"high": 1}
        })
        
        self.assertIsNotNone(result)


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestArtifacts))
    suite.addTests(loader.loadTestsFromTestCase(TestAgents))
    suite.addTests(loader.loadTestsFromTestCase(TestGates))
    suite.addTests(loader.loadTestsFromTestCase(TestDAG))
    suite.addTests(loader.loadTestsFromTestCase(TestRecovery))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    print(f"\n{'='*70}")
    print(f"테스트 완료: {result.testsRun}개 실행, "
          f"{len(result.failures)}개 실패, "
          f"{len(result.errors)}개 에러")
    print(f"{'='*70}")
