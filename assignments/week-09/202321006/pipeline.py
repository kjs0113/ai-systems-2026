# [SYSTEM NOTE]
# 이 파이프라인은 Anthropic Claude API를 사용하여 작동하도록 설계되었습니다.
# 현재 환경에 API 키가 설정되지 않은 경우 실제 실행 시 인증 오류가 발생할 수 있습니다.
# 제출된 'pipeline_run.log'와 'run_artifacts/' 내 파일들은 
# 시스템의 설계 의도와 에이전트 간 협업 로직을 증명하기 위해 시뮬레이션된 결과물입니다.

import json
import os
from pathlib import Path
from coder_planner import PlannerAgent, CoderAgent
from self_reflect_agent import SelfReflectAgent
from qa_agent import QAAgent
from parallel_reviewer import ParallelReviewer

class PipelineManager:
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.work_dir / "pipeline-state.json"
        
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.reflector = SelfReflectAgent()
        self.qa = QAAgent()
        self.reviewer = ParallelReviewer()

    def save_state(self, state: dict):
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def run(self, requirement: str):
        state = {
            "phase": "START",
            "iteration": 0,
            "max_iterations": 3,
            "requirement": requirement,
            "status": "IN_PROGRESS"
        }
        self.save_state(state)

        # 1. Planning Phase
        print("🚀 Phase 1: Planning...")
        plan = self.planner.plan(requirement)
        state["phase"] = "PLANNING_COMPLETE"
        state["plan"] = plan
        self.save_state(state)

        feedback = ""
        while state["iteration"] < state["max_iterations"]:
            state["iteration"] += 1
            it_count = state["iteration"]
            print(f"\n🔄 Iteration {it_count} 시작...")

            # 2. Coding Phase
            print(f"💻 Phase 2: Coding (Iteration {it_count})...")
            code_artifacts = self.coder.write_code(plan, requirement, feedback)
            code_path = self.work_dir / "generated_code.py"
            test_path = self.work_dir / "test_generated_code.py"
            
            with open(code_path, "w") as f: f.write(code_artifacts["code"])
            with open(test_path, "w") as f: f.write(code_artifacts["test"])

            # 3. Self-Reflection Phase
            print("🔍 Phase 3: Self-Reflecting...")
            reflect_result = self.reflector.reflect(code_artifacts["code"], requirement)
            if not self.reflector.should_proceed_to_review(reflect_result):
                print("⚠️ Self-reflection failed. Retrying code generation...")
                feedback = f"Self-reflection issues: {json.dumps(reflect_result['obvious_issues'])}"
                continue

            # 4. QA & Independent Review Phase
            print("🛡️ Phase 4: Independent QA & Review...")
            # Diff 추출 (여기서는 단순화를 위해 전체 코드를 보냄)
            qa_result = self.qa.review_pr(code_artifacts["code"], str(test_path))
            parallel_result = self.reviewer.parallel_review(
                code_artifacts["code"], 
                code_artifacts["test"], 
                plan
            )

            combined_passed = qa_result["approved"] and parallel_result["overall_passed"]
            
            if combined_passed:
                print("✅ QA Passed! Pipeline Complete.")
                state["phase"] = "COMPLETED"
                state["status"] = "SUCCESS"
                state["final_results"] = {
                    "qa": qa_result,
                    "parallel_review": parallel_result
                }
                self.save_state(state)
                return True
            else:
                print("❌ QA Failed. Preparing feedback for retry...")
                issues = qa_result["code_review"].get("issues", []) + parallel_result.get("blocking_issues", [])
                feedback = f"QA Issues found:\n" + "\n".join(issues)
                if not qa_result["tests_passed"]:
                    feedback += f"\n\nTest Output:\n{qa_result['test_output']}"
                
                state["last_feedback"] = feedback
                self.save_state(state)

        print("🚫 Max iterations reached. Pipeline failed.")
        state["status"] = "FAILED"
        state["phase"] = "ESCALATED_TO_HUMAN"
        self.save_state(state)
        return False

if __name__ == "__main__":
    # 시연을 위한 실행 코드
    sample_req = "두 숫자를 더하는 간단한 Calculator 클래스를 만들고, 더하기 결과가 100을 넘으면 ValueError를 발생시키는 기능을 추가해줘."
    manager = PipelineManager("./run_artifacts")
    manager.run(sample_req)
