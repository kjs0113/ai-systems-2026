"""
Orchestrator Module

멀티에이전트 시스템의 실행을 조율하는 오케스트레이터
"""

from typing import Dict, Any, List
from datetime import datetime
import asyncio

from .dag import AgentDAG
from ..agents.base import BaseAgent
from ..gates.base_gate import BaseGate
from ..artifacts.final import ExecutionLog


class ExecutionContext:
    """실행 컨텍스트"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.artifacts: Dict[str, Any] = {}
        self.logs: List[ExecutionLog] = []
        self.gate_results: List[Dict] = []
        self.start_time = datetime.utcnow()
        self.end_time = None
    
    def add_artifact(self, stage: str, artifact: Any):
        """아티팩트 저장"""
        self.artifacts[stage] = artifact
    
    def get_artifact(self, stage: str) -> Any:
        """아티팩트 조회"""
        return self.artifacts.get(stage)
    
    def add_log(self, stage: str, status: str, details: str = ""):
        """실행 로그 추가"""
        log = ExecutionLog(
            stage=stage,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            details=details
        )
        self.logs.append(log)
    
    def add_gate_result(self, result: Dict):
        """게이트 검증 결과 추가"""
        self.gate_results.append(result)
    
    def finalize(self):
        """실행 종료"""
        self.end_time = datetime.utcnow()
    
    def get_duration(self) -> float:
        """실행 시간 반환 (초)"""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()


class Orchestrator:
    """멀티에이전트 오케스트레이터"""
    
    def __init__(self, agents: Dict[str, BaseAgent], gates: Dict[str, BaseGate]):
        """
        Args:
            agents: 에이전트 딕셔너리 {name: agent}
            gates: 게이트 딕셔너리 {stage: gate}
        """
        self.agents = agents
        self.gates = gates
        self.dag = AgentDAG()
        self.dag.build_standard_pipeline()
    
    def execute(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        파이프라인 실행 (순차 버전)
        
        Args:
            initial_input: 초기 입력
            
        Returns:
            Dict: 실행 결과
        """
        task_id = initial_input.get("task_id", f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        context = ExecutionContext(task_id)
        
        try:
            # 1. Planner 실행
            plan_result = self._execute_stage(
                "planner", 
                initial_input, 
                context,
                gate_name="planning"
            )
            if plan_result["status"] != "success":
                return self._build_failure_response(context, "planner", plan_result)
            
            # 2. Context 실행
            context_input = {
                "plan": context.get_artifact("planner"),
                "task_id": task_id
            }
            context_result = self._execute_stage(
                "context",
                context_input,
                context,
                gate_name="context"
            )
            if context_result["status"] != "success":
                return self._build_failure_response(context, "context", context_result)
            
            # 3. Builder 실행
            builder_input = {
                "plan": context.get_artifact("planner"),
                "context": context.get_artifact("context"),
                "task_id": task_id
            }
            builder_result = self._execute_stage(
                "builder",
                builder_input,
                context,
                gate_name="draft"
            )
            if builder_result["status"] != "success":
                return self._build_failure_response(context, "builder", builder_result)
            
            # 4. Reviewer 실행
            reviewer_input = {
                "draft": context.get_artifact("builder"),
                "plan": context.get_artifact("planner"),
                "task_id": task_id
            }
            reviewer_result = self._execute_stage(
                "reviewer",
                reviewer_input,
                context,
                gate_name="review"
            )
            if reviewer_result["status"] != "success":
                return self._build_failure_response(context, "reviewer", reviewer_result)
            
            # 5. Finalizer 실행
            finalizer_input = {
                "draft": context.get_artifact("builder"),
                "review": context.get_artifact("reviewer"),
                "audit_trail": context.logs,
                "task_id": task_id
            }
            finalizer_result = self._execute_stage(
                "finalizer",
                finalizer_input,
                context,
                gate_name="release"
            )
            if finalizer_result["status"] != "success":
                return self._build_failure_response(context, "finalizer", finalizer_result)
            
            # 실행 완료
            context.finalize()
            
            return {
                "status": "success",
                "task_id": task_id,
                "final_artifact": context.get_artifact("finalizer"),
                "execution_time": context.get_duration(),
                "audit_trail": [log.__dict__ for log in context.logs],
                "gate_results": context.gate_results
            }
            
        except Exception as e:
            context.finalize()
            context.add_log("orchestrator", "failed", str(e))
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(e),
                "execution_time": context.get_duration(),
                "audit_trail": [log.__dict__ for log in context.logs]
            }
    
    def _execute_stage(self, agent_name: str, inputs: Dict[str, Any], 
                      context: ExecutionContext, gate_name: str = None) -> Dict[str, Any]:
        """
        단일 스테이지 실행
        
        Args:
            agent_name: 에이전트 이름
            inputs: 입력 데이터
            context: 실행 컨텍스트
            gate_name: 검증 게이트 이름 (선택)
            
        Returns:
            Dict: 실행 결과
        """
        # 에이전트 실행
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        
        context.add_log(agent_name, "started", f"Executing {agent_name}")
        
        try:
            result = agent.run(inputs)
        except Exception as e:
            # 예외 발생 시 로깅
            import traceback
            error_detail = traceback.format_exc()
            context.add_log(agent_name, "failed", f"Exception: {str(e)}\n{error_detail}")
            return {
                "status": "failed",
                "agent": agent_name,
                "error": str(e),
                "traceback": error_detail
            }
        
        if result["status"] == "success":
            artifact = result["artifact"]
            context.add_artifact(agent_name, artifact)
            context.add_log(agent_name, "completed", f"{agent_name} completed successfully")
            
            # 게이트 검증
            if gate_name and gate_name in self.gates:
                try:
                    gate = self.gates[gate_name]
                    validation = gate.validate(artifact)
                    context.add_gate_result(validation.to_dict())
                    
                    if not validation.passed:
                        context.add_log(
                            agent_name, 
                            "gate_failed",
                            f"Gate validation failed: {', '.join(validation.errors)}"
                        )
                        return {
                            "status": "gate_failed",
                            "agent": agent_name,
                            "gate": gate_name,
                            "validation": validation.to_dict()
                        }
                except Exception as e:
                    # 게이트 검증 중 예외 발생
                    import traceback
                    error_detail = traceback.format_exc()
                    context.add_log(gate_name, "failed", f"Gate exception: {str(e)}\n{error_detail}")
                    return {
                        "status": "failed",
                        "agent": agent_name,
                        "error": f"Gate validation exception: {str(e)}",
                        "traceback": error_detail
                    }
        else:
            context.add_log(agent_name, "failed", result.get("error", "Unknown error"))
        
        return result
    
    def _build_failure_response(self, context: ExecutionContext, 
                               failed_stage: str, result: Dict) -> Dict:
        """실패 응답 생성"""
        context.finalize()
        
        # gate_failed 상태 처리
        if result.get("status") == "gate_failed":
            validation = result.get("validation", {})
            error_msg = f"Gate '{result.get('gate')}' validation failed"
            if validation.get("errors"):
                error_msg += f": {', '.join(validation['errors'])}"
        else:
            error_msg = result.get("error", "Unknown error")
        
        traceback_info = result.get("traceback", "")
        
        return {
            "status": "failed",
            "task_id": context.task_id,
            "failed_stage": failed_stage,
            "error": error_msg,
            "execution_time": context.get_duration(),
            "audit_trail": [log.__dict__ for log in context.logs],
            "gate_results": context.gate_results
        }
    
    def get_dag_analysis(self) -> Dict:
        """DAG 분석 정보 반환"""
        return self.dag.get_parallelization_analysis()
    
    def visualize_dag(self) -> str:
        """DAG 시각화"""
        return self.dag.visualize_ascii()
