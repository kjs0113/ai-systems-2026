import json
import time
from datetime import datetime
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider

# 1. OpenTelemetry Setup
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

# 2. Agent Wrapper with Tracing and Event Logging
def run_agent_with_telemetry(task_packet):
    event_store = EventStore()
    
    with tracer.start_as_current_span("agent.run") as span:
        run_id = f"run-{int(time.time())}"
        span.set_attribute("run.id", run_id)
        span.set_attribute("task.id", task_packet["id"])
        span.set_attribute("agent.role", task_packet.get("role", "worker"))
        span.set_attribute("model.name", task_packet.get("model", "sonnet-4.6"))
        
        event_store.append("run.started", run_id=run_id, task_id=task_packet["id"], model=task_packet.get("model"))
        
        # [Simulated Steps]
        # 1. Model Call
        with tracer.start_as_current_span("model.call") as m_span:
            m_span.set_attribute("model.name", "sonnet-4.6")
            # ... model logic ...
            pass
            
        # 2. Tool Invoke
        with tracer.start_as_current_span("tool.invoke") as t_span:
            t_span.set_attribute("tool.name", "read_file")
            event_store.append("tool.invoke", run_id=run_id, tool="read_file", input={"path": "src/app.py"})
            # ... tool logic ...
            event_store.append("tool.result", run_id=run_id, tool="read_file", status="ok")

        # 3. Final Result
        span.set_attribute("gate.result", "pass")
        event_store.append("run.closed", run_id=run_id, status="success")
        
    return run_id

if __name__ == "__main__":
    test_task = {"id": "task-001", "objective": "Fix the bug in parser", "role": "worker"}
    run_id = run_agent_with_telemetry(test_task)
    print(f"Completed run: {run_id}")
