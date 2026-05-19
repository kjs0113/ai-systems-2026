import json
import time
import os
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# OpenTelemetry Setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("agent-harness")

class EventStore:
    def __init__(self, filename="events.jsonl"):
        self.filename = filename

    def append(self, event_type, **kwargs):
        event = {
            "type": event_type,
            "ts": datetime.utcnow().isoformat() + "Z",
            **kwargs
        }
        with open(self.filename, "a") as f:
            f.write(json.dumps(event) + "\n")

def generate_replay_snapshot(events_file="events.jsonl", snapshot_file="replay_snapshot.json"):
    events = []
    if not os.path.exists(events_file):
        return
    with open(events_file, "r") as f:
        for line in f:
            events.append(json.loads(line))
            
    # Simple Replay Logic
    replays = {}
    for ev in events:
        rid = ev.get("run_id")
        if not rid: continue
        if rid not in replays:
            replays[rid] = {"tools": [], "tests": [], "judge": None, "status": "open", "cost": 0}
        
        if ev["type"] == "run.started":
            replays[rid]["task_id"] = ev.get("task_id")
            replays[rid]["model"] = ev.get("model")
        elif ev["type"] == "tool.result":
            replays[rid]["tools"].append(ev)
        elif ev["type"] == "test.result":
            replays[rid]["tests"].append(ev)
        elif ev["type"] == "judge.result":
            replays[rid]["judge"] = ev
        elif ev["type"] == "run.closed":
            replays[rid]["status"] = "closed"
            replays[rid]["final_status"] = ev.get("status")
            
    with open(snapshot_file, "w") as f:
        json.dump(replays, f, indent=2)

def run_agent_step(task, event_store):
    run_id = f"run-{int(time.time() * 1000)}"
    
    with tracer.start_as_current_span("agent.run") as span:
        span.set_attribute("run.id", run_id)
        span.set_attribute("task.id", task["id"])
        span.set_attribute("agent.role", task.get("role", "worker"))
        span.set_attribute("model.name", task.get("model", "sonnet-4.6"))
        
        event_store.append("run.started", run_id=run_id, task_id=task["id"], model=task.get("model"))
        
        # 1. Model Call
        with tracer.start_as_current_span("model.call") as m_span:
            m_span.set_attribute("model.name", task.get("model"))
            time.sleep(0.1)
            
        # 2. Tool Invoke
        with tracer.start_as_current_span("tool.invoke") as t_span:
            t_span.set_attribute("tool.name", "run_tests")
            event_store.append("tool.invoke", run_id=run_id, tool="run_tests", input={"cmd": "pytest"})
            # Simulated test result
            passed = task.get("should_pass", True)
            event_store.append("tool.result", run_id=run_id, tool="run_tests", status="ok" if passed else "error")
            event_store.append("test.result", run_id=run_id, command="pytest", passed=passed)

        # 3. Judge Evaluate (Probabilistic Gate)
        with tracer.start_as_current_span("judge.evaluate") as j_span:
            j_span.set_attribute("run.id", run_id)
            # This would call judge.py logic
            judge_res = {"overall": task.get("judge_score", 8.5), "verdict": "pass" if task.get("judge_score", 8.5) > 7 else "revise"}
            event_store.append("judge.result", run_id=run_id, **judge_res)
            j_span.set_attribute("gate.result", judge_res["verdict"])

        # 4. Final Close
        span.set_attribute("gate.result", "pass" if passed else "fail")
        event_store.append("run.closed", run_id=run_id, status="success" if passed else "failed")
        
    return run_id
