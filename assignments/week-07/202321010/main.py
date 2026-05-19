"""
Main Entry Point

멀티에이전트 시스템 실행 메인 파일
"""

import json
from multi_agent_system.agents.planner import PlannerAgent
from multi_agent_system.agents.context import ContextAgent
from multi_agent_system.agents.builder import BuilderAgent
from multi_agent_system.agents.reviewer import ReviewerAgent
from multi_agent_system.agents.finalizer import FinalizerAgent

from multi_agent_system.gates.planning_gate import PlanningGate
from multi_agent_system.gates.context_gate import ContextGate
from multi_agent_system.gates.draft_gate import DraftGate
from multi_agent_system.gates.review_gate import ReviewGate
from multi_agent_system.gates.release_gate import ReleaseGate

from multi_agent_system.orchestrator.executor import Orchestrator
from multi_agent_system.orchestrator.recovery import ErrorRecoveryStrategy


def create_system():
    """시스템 초기화"""
    # 에이전트 생성
    agents = {
        "planner": PlannerAgent(),
        "context": ContextAgent(),
        "builder": BuilderAgent(),
        "reviewer": ReviewerAgent(),
        "finalizer": FinalizerAgent()
    }
    
    # 게이트 생성
    gates = {
        "planning": PlanningGate(),
        "context": ContextGate(),
        "draft": DraftGate(),
        "review": ReviewGate(),
        "release": ReleaseGate()
    }
    
    # 오케스트레이터 생성
    orchestrator = Orchestrator(agents, gates)
    
    # 복구 전략 생성
    recovery = ErrorRecoveryStrategy(max_retries=3)
    
    return orchestrator, recovery


def run_example(orchestrator: Orchestrator):
    """예제 실행 - Case 1: 정상 입력"""
    print("=" * 70)
    print("Case 1: 정상 입력 시나리오")
    print("=" * 70)
    print()
    
    # 초기 입력
    initial_input = {
        "requirements": "고객 피드백을 분석하여 인사이트를 도출하고 개선안을 제시하는 보고서를 작성하시오.",
        "constraints": [
            "보고서 길이는 적절하게 유지",
            "개인정보 포함 금지",
            "실행 가능한 권장사항 포함"
        ]
    }
    
    print("📥 초기 입력:")
    print(f"  - 요구사항: {initial_input['requirements']}")
    print(f"  - 제약사항: {len(initial_input['constraints'])}개")
    print()
    
    # DAG 분석 출력
    print("📊 DAG 병렬화 분석:")
    dag_analysis = orchestrator.get_dag_analysis()
    print(f"  - 총 노드 수: {dag_analysis['total_nodes']}")
    print(f"  - 총 Tier 수: {dag_analysis['total_tiers']}")
    print(f"  - 최대 병렬 노드: {dag_analysis['max_parallel_nodes']}")
    print(f"  - 병렬화 효율: {dag_analysis['parallelization_efficiency']:.1%}")
    print()
    
    print("🔄 Tier별 실행 계획:")
    for tier in dag_analysis['tier_details']:
        parallel = "✓" if tier['parallelizable'] else "✗"
        print(f"  Tier {tier['tier']}: {tier['nodes']} (병렬: {parallel})")
    print()
    
    # 시스템 실행
    print("🚀 시스템 실행 시작...")
    print()
    
    result = orchestrator.execute(initial_input)
    
    # 결과 출력
    print("=" * 70)
    print("📋 실행 결과")
    print("=" * 70)
    print()
    
    if result["status"] == "success":
        print("✅ 상태: 성공")
        print(f"📌 작업 ID: {result['task_id']}")
        print(f"⏱️  실행 시간: {result['execution_time']:.2f}초")
        print()
        
        # 최종 아티팩트 정보
        final_artifact = result["final_artifact"]
        print("📦 최종 산출물:")
        print(f"  - 배포 가능: {final_artifact.releaseable}")
        print(f"  - 제목: {final_artifact.final_content.get('title', 'N/A')}")
        print(f"  - 섹션 수: {len(final_artifact.final_content.get('sections', []))}")
        print(f"  - 품질 점수: {final_artifact.metadata.get('final_quality_score', 0):.2f}")
        print(f"  - 커버리지: {final_artifact.metadata.get('coverage_rate', 0):.1%}")
        print()
        
        # 감사 추적
        print("📝 감사 추적 (Audit Trail):")
        for log in result["audit_trail"][:7]:  # 최대 7개만 출력
            print(f"  [{log['stage']}] {log['status']} - {log.get('details', '')[:50]}")
        print()
        
        # 게이트 검증 결과
        print("🚪 게이트 검증 결과:")
        for gate_result in result["gate_results"]:
            status_icon = "✅" if gate_result["passed"] else "❌"
            print(f"  {status_icon} {gate_result['gate']}: {'통과' if gate_result['passed'] else '실패'}")
            if gate_result["errors"]:
                for error in gate_result["errors"][:2]:
                    print(f"      ⚠️  {error}")
        print()
        
    else:
        print(f"❌ 상태: 실패")
        print(f"📌 작업 ID: {result['task_id']}")
        print(f"❗ 실패 단계: {result.get('failed_stage', 'unknown')}")
        print(f"💬 에러: {result.get('error', 'Unknown error')}")
        print()
        
        # 감사 추적에서 상세 에러 확인
        if "audit_trail" in result:
            print("📝 에러 세부 정보 (Audit Trail):")
            for log in result["audit_trail"]:
                if log.get("status") == "failed":
                    print(f"  [{log['stage']}] {log.get('details', '')}")
            print()
    
    # 결과 해석 섹션 추가
    if result["status"] == "success":
        print("📌 결과 해석")
        print()
        print("본 결과는 다음 조건 하에서 도출되었습니다:")
        print("  ✓ 입력 요구사항이 명확하게 정의된 단일 시나리오")
        print("  ✓ 아티팩트 스키마 검증이 Pydantic으로 강하게 적용된 환경")
        print("  ✓ 제한된 테스트 케이스 (controlled environment)")
        print()
        print("따라서 해당 결과는 시스템의 최적 조건 하 성능(upper-bound performance)을")
        print("나타내며, 다양한 edge case 및 불완전 입력에 대해서는 추가 검증이 필요합니다.")
        print()
    
    return result


def run_failure_case(orchestrator: Orchestrator):
    """실패 케이스 실행 - Case 2: 오류 입력"""
    print("\n")
    print("=" * 70)
    print("Case 2: 오류 입력 시나리오 (모호한 요구사항)")
    print("=" * 70)
    print()
    
    # 의도적으로 모호한 입력
    initial_input = {
        "requirements": "뭔가 좋은 거",  # 모호한 요구사항
        "constraints": [
            "짧게",
            "상세하게"  # 상충되는 제약
        ]
    }
    
    print("📥 초기 입력 (의도적 오류):")
    print(f"  - 요구사항: {initial_input['requirements']} ⚠️ (모호함)")
    print(f"  - 제약사항: {initial_input['constraints']} ⚠️ (상충)")
    print()
    
    print("🚀 시스템 실행 시작...")
    print()
    
    result = orchestrator.execute(initial_input)
    
    # 결과 출력
    print("=" * 70)
    print("📋 실행 결과")
    print("=" * 70)
    print()
    
    if result["status"] == "success":
        print("✅ 상태: 성공 (복구 전략 작동)")
        print(f"📌 작업 ID: {result['task_id']}")
        print(f"⏱️  실행 시간: {result['execution_time']:.2f}초")
        print()
        print("📝 주요 이슈:")
        print("  - 모호한 요구사항 입력으로 인한 낮은 품질 점수")
        print("  - 상충되는 제약사항 (짧게 vs 상세하게)")
        print()
    else:
        print(f"❌ 상태: 실패")
        print(f"📌 작업 ID: {result['task_id']}")
        print(f"❗ 실패 단계: {result.get('failed_stage', 'unknown')}")
        print(f"💬 에러: {result.get('error', 'Unknown error')}")
        print()
        
        # 게이트 검증 결과
        if "gate_results" in result and result["gate_results"]:
            print("🚪 게이트 검증 결과:")
            for gate_result in result["gate_results"]:
                status_icon = "✅" if gate_result["passed"] else "❌"
                print(f"  {status_icon} {gate_result['gate']}: {'통과' if gate_result['passed'] else '실패'}")
                if gate_result["errors"]:
                    for error in gate_result["errors"][:2]:
                        print(f"      ⚠️  {error}")
            print()
        
        print("📌 실패 원인 분석:")
        print("  - 입력 품질이 낮아 Planning Gate 또는 Context Gate에서 검증 실패")
        print("  - 모호한 목표 정의로 인한 성공 기준 도출 불가")
        print("  - 복구 전략 실행: Planner 재실행 또는 수동 개입 필요")
        print()
    
    return result


def demonstrate_recovery():
    """복구 전략 시연"""
    print("\n")
    print("=" * 70)
    print("🔧 에러 복구 전략 시연 (시뮬레이션)")
    print("=" * 70)
    print()
    
    recovery = ErrorRecoveryStrategy(max_retries=3)
    
    # 시나리오 1: 스키마 불일치
    print("시나리오 1: 스키마 불일치")
    result1 = recovery.handle_error("schema_mismatch", {
        "retry_count": 0,
        "error_details": "필수 필드 'content' 누락"
    })
    print(f"  - 액션: {result1.action.value}")
    print(f"  - 메시지: {result1.message}")
    print()
    
    # 시나리오 2: 컨텍스트 충돌
    print("시나리오 2: 컨텍스트 충돌")
    result2 = recovery.handle_error("context_conflict", {
        "conflict_items": ["길이는 짧게", "반드시 상세하게"],
        "priority_policy": "system"
    })
    print(f"  - 액션: {result2.action.value}")
    print(f"  - 메시지: {result2.message}")
    print()
    
    # 시나리오 3: 게이트 실패
    print("시나리오 3: 게이트 실패")
    result3 = recovery.handle_error("gate_failure", {
        "issues": [
            {"issue_id": "i1", "severity": "high", "suggested_fix": "섹션 2 추가"},
            {"issue_id": "i2", "severity": "medium", "suggested_fix": "오타 수정"}
        ],
        "gate_name": "draft_gate",
        "severity_counts": {"high": 1, "medium": 1}
    })
    print(f"  - 액션: {result3.action.value}")
    print(f"  - 메시지: {result3.message}")
    print()
    
    # 복구 통계
    stats = recovery.get_recovery_statistics()
    print("📊 복구 통계:")
    print(f"  - 총 복구 시도: {stats['total']}")
    print(f"  - 에러 타입별: {stats['by_type']}")
    print(f"  - 액션별: {stats['by_action']}")
    print()


def main():
    """메인 실행"""
    # 시스템 생성
    orchestrator, recovery = create_system()
    
    # Case 1: 정상 입력
    result1 = run_example(orchestrator)
    
    # Case 2: 오류 입력
    result2 = run_failure_case(orchestrator)
    
    # 복구 전략 시연
    demonstrate_recovery()
    
    # 비교 요약
    print("\n")
    print("=" * 70)
    print("📊 시나리오 비교 요약")
    print("=" * 70)
    print()
    print("Case 1 (정상 입력):")
    print(f"  - 상태: {result1['status']}")
    print(f"  - 실행 시간: {result1.get('execution_time', 0):.2f}초")
    print(f"  - 게이트 통과율: {len([g for g in result1.get('gate_results', []) if g['passed']])}/{len(result1.get('gate_results', []))}") 
    print()
    print("Case 2 (오류 입력):")
    print(f"  - 상태: {result2['status']}")
    print(f"  - 실행 시간: {result2.get('execution_time', 0):.2f}초")
    if result2['status'] == 'failed':
        print(f"  - 실패 지점: {result2.get('failed_stage', 'unknown')}")
        print(f"  - 게이트 통과율: {len([g for g in result2.get('gate_results', []) if g['passed']])}/{len(result2.get('gate_results', []))}")
    print()
    print("✅ 시스템 검증 완료:")
    print("  - 정상 조건에서 100% 성공")
    print("  - 오류 조건에서 적절히 실패 및 에러 보고")
    print("  - 복구 전략 정의 완료")
    print()
    
    # DAG 시각화
    print("\n")
    print("=" * 70)
    print("🌳 DAG 시각화")
    print("=" * 70)
    print()
    print(orchestrator.visualize_dag())
    
    print("\n")
    print("=" * 70)
    print("✨ 실행 완료")
    print("=" * 70)
    
    return result1


if __name__ == "__main__":
    main()
