import json
from telemetry import EventStore, run_agent_step, generate_replay_snapshot
from judge import LLMJudge, gate_policy
from correlate import calculate_correlation

# 1. 10 Code Samples (명백히 좋은 것, 나쁜 것, 테스트는 통과하지만 설계가 구린 것 등 포함)
SAMPLES = [
    {"id": "S01", "name": "Perfect Add", "quality": 9.5, "pass": True, "human": 9.5},
    {"id": "S02", "name": "Messy Parser", "quality": 4.5, "pass": True, "human": 4.0}, # Test pass but bad design
    {"id": "S03", "name": "Broken Logic", "quality": 2.0, "pass": False, "human": 2.0},
    {"id": "S04", "name": "Solid Auth", "quality": 8.5, "pass": True, "human": 8.5},
    {"id": "S05", "name": "Over-engineered", "quality": 6.0, "pass": True, "human": 5.5},
    {"id": "S06", "name": "Vulnerable SQL", "quality": 3.0, "pass": True, "human": 2.5}, # Security issue
    {"id": "S07", "name": "Clean API", "quality": 9.0, "pass": True, "human": 9.0},
    {"id": "S08", "name": "No Error Handling", "quality": 5.0, "pass": True, "human": 4.5},
    {"id": "S09", "name": "Great Coverage", "quality": 8.0, "pass": True, "human": 8.0},
    {"id": "S10", "name": "Spaghetti Code", "quality": 3.5, "pass": True, "human": 3.0},
]

def main():
    event_store = EventStore("events.jsonl")
    judge = LLMJudge()
    
    results = []
    
    print("Starting Assignment Simulation...")
    for s in SAMPLES:
        # Evaluate with Judge
        judge_res = judge.evaluate({"name": s["name"], "quality_score": s["quality"], "code": "X" * (int(s["quality"]) * 100)})
        
        # Run agent loop with telemetry
        task = {
            "id": s["id"],
            "role": "worker",
            "model": "sonnet-4.6",
            "should_pass": s["pass"],
            "judge_score": judge_res["overall"]
        }
        run_id = run_agent_step(task, event_store)
        
        # Apply Gate Policy
        final_verdict = gate_policy(judge_res, s["pass"])
        
        results.append({
            "sample": s["name"],
            "human": s["human"],
            "judge": judge_res["overall"],
            "verdict": final_verdict
        })
        print(f"Processed {s['name']}: Verdict={final_verdict}")

    # Generate Snapshot
    generate_replay_snapshot()
    
    # Calculate Correlations
    human_scores = [r["human"] for r in results]
    judge_scores = [r["judge"] for r in results]
    stats = calculate_correlation(human_scores, judge_scores)
    
    with open("analysis_results.json", "w") as f:
        json.dump({"stats": stats, "details": results}, f, indent=2)
        
    print("\nSimulation Complete. Analysis saved to analysis_results.json")

if __name__ == "__main__":
    main()
