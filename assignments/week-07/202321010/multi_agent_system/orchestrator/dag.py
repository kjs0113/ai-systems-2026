"""
DAG (Directed Acyclic Graph) Module

에이전트 실행 순서를 관리하는 DAG 구현
"""

import networkx as nx
from typing import List, Dict, Set, Tuple
from ..artifacts.plan import PlanArtifact


class AgentDAG:
    """에이전트 실행 의존성 DAG"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.tiers: List[Set[str]] = []
    
    def build_from_plan(self, plan: PlanArtifact):
        """
        PlanArtifact로부터 DAG 구축
        
        Args:
            plan: PlanArtifact 객체
        """
        self.graph.clear()
        
        # 노드 추가
        for step in plan.steps:
            self.graph.add_node(
                step.step_id,
                agent=step.owner_agent,
                description=step.description
            )
        
        # 엣지 추가 (의존성)
        for step in plan.steps:
            for dependency in step.depends_on:
                # dependency -> step_id (dependency가 먼저 실행되어야 함)
                self.graph.add_edge(dependency, step.step_id)
        
        # Tier 계산
        self._compute_tiers()
    
    def build_standard_pipeline(self):
        """
        표준 5단계 파이프라인 DAG 구축
        """
        self.graph.clear()
        
        # 노드 정의
        nodes = [
            ("planner", "planner", "계획 수립"),
            ("context", "context", "맥락 수집"),
            ("builder", "builder", "초안 생성"),
            ("reviewer", "reviewer", "품질 검토"),
            ("finalizer", "finalizer", "최종화")
        ]
        
        for node_id, agent, desc in nodes:
            self.graph.add_node(node_id, agent=agent, description=desc)
        
        # 의존성 정의
        edges = [
            ("planner", "context"),
            ("planner", "builder"),
            ("context", "builder"),
            ("builder", "reviewer"),
            ("reviewer", "finalizer")
        ]
        
        self.graph.add_edges_from(edges)
        
        # Tier 계산
        self._compute_tiers()
    
    def _compute_tiers(self):
        """
        병렬화 Tier 계산
        
        같은 tier의 노드들은 병렬 실행 가능
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Graph contains cycles!")
        
        self.tiers = []
        remaining_nodes = set(self.graph.nodes())
        
        while remaining_nodes:
            # 현재 tier: 의존성이 모두 해결된 노드들
            current_tier = set()
            
            for node in remaining_nodes:
                predecessors = set(self.graph.predecessors(node))
                # 선행 노드가 없거나, 모두 이미 처리됨
                if not predecessors or predecessors.isdisjoint(remaining_nodes):
                    current_tier.add(node)
            
            if not current_tier:
                raise ValueError("Cannot compute tiers - possible cycle")
            
            self.tiers.append(current_tier)
            remaining_nodes -= current_tier
    
    def get_execution_order(self) -> List[Set[str]]:
        """
        실행 순서 반환 (tier 단위)
        
        Returns:
            List[Set[str]]: 각 tier의 노드 집합 리스트
        """
        return self.tiers
    
    def get_tier_count(self) -> int:
        """Tier 개수 반환"""
        return len(self.tiers)
    
    def get_parallelization_analysis(self) -> Dict:
        """
        병렬화 분석 결과 반환
        
        Returns:
            Dict: 병렬화 분석 정보
        """
        total_nodes = self.graph.number_of_nodes()
        max_parallel = max(len(tier) for tier in self.tiers) if self.tiers else 0
        
        tier_info = []
        for idx, tier in enumerate(self.tiers):
            tier_details = {
                "tier": idx,
                "nodes": list(tier),
                "parallelizable": len(tier) > 1,
                "count": len(tier)
            }
            tier_info.append(tier_details)
        
        # 병렬화 효율 계산
        sequential_time = total_nodes  # 모두 순차 실행 시
        parallel_time = len(self.tiers)  # 병렬 실행 시
        efficiency = 1.0 - (parallel_time / sequential_time) if sequential_time > 0 else 0.0
        
        return {
            "total_nodes": total_nodes,
            "total_tiers": len(self.tiers),
            "max_parallel_nodes": max_parallel,
            "parallelization_efficiency": round(efficiency, 2),
            "tier_details": tier_info
        }
    
    def validate(self) -> Tuple[bool, str]:
        """
        DAG 유효성 검증
        
        Returns:
            Tuple[bool, str]: (유효 여부, 메시지)
        """
        if self.graph.number_of_nodes() == 0:
            return False, "Graph is empty"
        
        if not nx.is_directed_acyclic_graph(self.graph):
            return False, "Graph contains cycles"
        
        # 고립된 노드 확인
        isolated = list(nx.isolates(self.graph))
        if isolated:
            return False, f"Isolated nodes found: {isolated}"
        
        return True, "DAG is valid"
    
    def visualize_ascii(self) -> str:
        """
        ASCII로 DAG 시각화
        
        Returns:
            str: ASCII 표현
        """
        lines = ["=== Agent DAG ===\n"]
        
        for tier_idx, tier in enumerate(self.tiers):
            lines.append(f"Tier {tier_idx}:")
            for node in sorted(tier):
                agent = self.graph.nodes[node].get('agent', 'unknown')
                desc = self.graph.nodes[node].get('description', '')
                lines.append(f"  - {node} ({agent}): {desc}")
                
                # 후속 노드 표시
                successors = list(self.graph.successors(node))
                if successors:
                    lines.append(f"    → {', '.join(successors)}")
            lines.append("")
        
        return "\n".join(lines)
