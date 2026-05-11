---
title: Agent OS Runtime
description: Single-page reference for the MCP-first, provider-agnostic, event-sourced agent runtime (+ L8 workflow plane)
---

Agent OS Runtime treats agents as **verifiable runtime systems**, not just prompt-driven programs. This is a self-contained course unit. Students should be able to understand the architecture, contracts, implementation shape, and checklist without reading an external repository or separate subpages.

Core sentence:

> MCP-first, provider-agnostic, Plan-Work-Review, event-sourced, Markdown-SSOT, hook-gated, schema-versioned — and a workflow plane on top.

## Why It Exists

| Problem | Runtime answer |
|---|---|
| Tool calls are hard to trace | Route all external capabilities through MCP-style dispatch |
| Provider changes break code | Keep thin adapters and common request/response contracts |
| Agent handoffs are fragile prose | Validate IPC with versioned JSON Schema |
| Long runs are hard to reconstruct | Use append-only event logs and replay |
| Operational policy is mixed into code | Externalize allow, deny, transform decisions through hooks |
| Prompts, skills, and role descriptions drift from code | Keep Markdown as source of truth |
| Multi-phase workflow policy is scattered across code | Separate cycle / phase / policy / persona / artifact as a workflow-plane SSOT (L8) |

## Five Invariants

| ID | Invariant | Meaning |
|---|---|---|
| I-1 | Replayability | Every LLM call and state transition is appended to an event log; snapshots are recalculated from the log |
| I-2 | Provider Sovereignty | Provider changes should be profile/config changes, not business logic rewrites |
| I-3 | Fail-closed Gates | Hooks, schema validation, and tool registration deny by default on failure |
| I-4 | Markdown is SSOT | Skills, roles, and project context are canonical Markdown artifacts |
| I-5 | Schema-versioned IPC | Messages between agents, runtime, hooks, and tools are schema-validated |

## Request Flow

For a user request like `"fix the bug in auth.ts"`, the runtime:

1. appends `session.start`;
2. runs the `UserPromptSubmit` hook;
3. discovers matching Markdown skills;
4. scopes tools to the selected skill's `allowed-tools`;
5. asks Lead for `lead_directive_v1`;
6. asks Planner for `plan_v1`;
7. lets Worker act through tool dispatch and return `worker_report_v1`;
8. asks Reviewer for `review_result_v1`;
9. runs the Stop hook;
10. appends `session.close` and writes a replayable snapshot.

```text
session.start
hook.fired UserPromptSubmit allow
skill.invoke greet
agent.transition lead
llm.request lead
llm.response lead
agent.transition planner
llm.request planner
llm.response planner
agent.transition worker
tool.invoke echo
tool.result echo
llm.response worker
agent.transition reviewer
llm.response reviewer
hook.fired Stop deny
skill.complete greet ok
session.close ok
```

## 7-Layer Architecture

The goal is not simply to "make the model work." The goal is to place nondeterministic model calls inside a deterministic, observable, replayable system. L1–L7 is the core runtime that executes a single request safely; the optional [L8 Workflow Plane](#workflow-plane-l8) sits on top to sequence multi-phase cycles (a 7+1 structure).

| Layer | Name | Responsibility |
|---|---|---|
| L1 | MCP-first Tool Protocol | Route external capabilities through a tool boundary with schema, hooks, and events |
| L2 | Provider-agnostic Completion | Normalize Anthropic, OpenAI, Gemini, and local models into one call shape |
| L3 | Plan-Work-Review Collaboration | Control multi-agent execution through role separation and state transitions |
| L4 | Append-only Event Store | Serve as audit log, replay source, and cost/progress source |
| L5 | Markdown-SSOT Skill Runtime | Discover skills, match triggers, and scope allowed tools |
| L6 | Hook-intercepted Lifecycle | Externalize security, redaction, rate limiting, and loop stop policy |
| L7 | Schema-versioned IPC Registry | Validate every boundary payload with versioned JSON Schema |
| L8 | Workflow Orchestration | Sequence the cycle / phase / policy / persona / artifact axes as Markdown SSOT |

```text
L6 Hook Lifecycle
  intercepts everything below
L8 Workflow Orchestration
  sequences cycles, phases, personas, policies
L5 Markdown Skill Runtime
  selects skill and scopes tools
L3 Plan-Work-Review Agent Loop
  orchestrates role state
L2 Provider-agnostic Completion
  normalizes LLM calls
L1 MCP Tool Protocol
  exposes external capability
L4 Append-only Event Store
  records every state transition
L7 Schema-versioned IPC Registry
  validates every boundary payload
```

L4 and L7 cut across every layer. A state change without an event, or a boundary payload without schema validation, is treated as an out-of-runtime side effect. L6 intercepts every layer above it, and L8 is a workflow plane layered on top of L1–L7 — it inherits the same five invariants (I-1 through I-5) and decides, not "what should one prompt do?", but "which phases run in which order until which verdict?"

### L1 MCP-first Tool Protocol

All external capability goes through a tool registry.

```ts
interface ToolDef {
  name: string;
  schema_in: string;
  schema_out: string;
  invoke(args: unknown): Result<ToolResult, ToolError>;
}

interface ToolCall {
  id: string;
  name: string;
  args: unknown;
}
```

Execution order:

1. find the tool in the registry;
2. verify the caller's allowed tool scope;
3. validate args with `schema_in`;
4. run `PreToolUse`;
5. append `tool.invoke`;
6. invoke the tool;
7. append `tool.result`;
8. run `PostToolUse`;
9. validate the result with `schema_out`.

Forbidden patterns:

- direct filesystem, subprocess, or HTTP calls from business code;
- input schema without output schema;
- continuing execution after hook denial.

### L2 Provider-agnostic Completion

Provider SDK objects stay inside thin adapters.

```ts
interface CompletionRequest {
  messages: Array<{ role: string; content: string }>;
  model: string;
  tools?: ToolDef[];
  max_tokens?: number;
  temperature?: number;
  schema_version: "v1";
}

interface CompletionResponse {
  text: string;
  tool_calls: ToolCall[];
  finish_reason: "stop" | "tool_use" | "max_tokens" | "safety";
  usage: UsageInfo;
  model: string;
  schema_version: "v1";
}
```

Invariants:

- provider changes end at `RuntimeProfile`;
- requests and responses are redacted before event logging;
- retries stay inside adapter boundaries and domain failures return structured errors.

### L3 Plan-Work-Review Collaboration

| Role | Responsibility |
|---|---|
| Lead | Convert user request into intent and constraints |
| Planner | Produce verifiable steps and risks |
| Worker | Execute steps and report tool usage |
| Reviewer | Compare plan and worker report, then pass/fail |
| Advisor | Give outside advice for ambiguous/high-stakes requests |
| Scaffolder | Create stubs, tests, branches, or fixtures |

```text
INTAKE -> LEAD -> PLAN -> WORK -> REVIEW -> DONE
                              ^       |
                              |       v
                            REWORK <- FAIL
```

Every transition appends `agent.transition`. Handoffs are schema-bound JSON, not free prose.

### L4 Append-only Event Store

```ts
interface Event {
  id: string;
  session_id: string;
  ts: string;
  type: string;
  actor: string;
  payload: unknown;
  schema_version: "v1";
  parent_id: string | null;
}
```

Rules:

- each session owns `sessions/{session_id}/.events.jsonl`;
- events are append-only;
- corrections use new `event.amended` events;
- snapshots must be recalculable from the event log;
- replay creates no side effects. Calling LLMs or tools again is a re-run, not replay.

### L5 Markdown-SSOT Skill Runtime

```yaml
---
name: greet
description: Echoes a greeting using the echo tool.
triggers:
  - greet
  - hello
allowed-tools:
  - echo
version: 1
schema_version: v1
---
```

Skill discovery:

1. scan skill roots at startup;
2. read `SKILL.md` frontmatter;
3. validate with `skill_frontmatter_v1`;
4. register by skill id;
5. match user prompt triggers;
6. pass selected `allowed-tools` to L1 dispatch.

Markdown is canonical. If code and skill text disagree, adjust the code to match Markdown.

### L6 Hook-intercepted Lifecycle

| Hook | Purpose |
|---|---|
| SessionStart | session initialization policy |
| UserPromptSubmit | prompt redaction, reject, rewrite |
| PreToolUse | allow/deny/transform before tool execution |
| PostToolUse | observe or redact tool results |
| SkillStart | skill-specific policy |
| Stop | loop termination or continuation |
| PreCompact | protect information before compaction |

```ts
type HookDecision =
  | { decision: "allow"; reason?: string }
  | { decision: "deny"; reason: string }
  | { decision: "transform"; output: unknown; reason?: string };
```

If a hook throws or times out, the default decision is deny. Hooks return decisions; they do not mutate runtime state directly.

### L7 Schema-versioned IPC

```text
completion_request_v1.json
completion_response_v1.json
lead_directive_v1.json
plan_v1.json
worker_report_v1.json
review_result_v1.json
skill_frontmatter_v1.json
write_claim_v1.json
```

Validate before provider requests, after provider responses, after role output parsing, during skill registration, at tool input/output boundaries, and after hook transforms.

`v1` is frozen. Breaking changes require a new schema such as `plan_v2.json`.

## Workflow Plane (L8)

L1–L7 are the core primitives that execute a single agent request deterministically. They do not, however, answer "what cycle do we start with today, and when does it end?" **L8 Workflow Orchestration** uses a single L3 Plan-Work-Review pass as a building block and defines the following five axes as Markdown + JSON Schema SSOT.

| Axis | Unit of definition | Location | Schema |
|---|---|---|---|
| **Cycle** | A user-intent bundle — phases, entry/exit/abort conditions, loop bounds | `workflows/cycles/` | `cycle_v1` |
| **Phase** | A step inside a cycle — `advance_signal`, `halt_signal`, personas invoked | `workflows/phases/` | `phase_v1` |
| **Policy** | A gating rule (allow / deny / advisory, default deny) | `workflows/policies/` | `policy_v1` |
| **Persona** | A domain specialist layered on the L3 six roles (reviewer / researcher / document-reviewer) | `workflows/personas/` | `skill_frontmatter_v1`-compatible |
| **Artifact** | A deliverable template — naming rule, frontmatter | `workflows/artifacts/` | per-template schema |

L8 calls L3; it never references L1 or L2 directly (L3 does). L8 inherits the same five invariants (I-1 through I-5), so workflow definitions must also be deterministic, auditable, and provider-agnostic.

### Execution Flow

```text
USER REQUEST
  -> resolve cycle_id (from a skill or a lead_directive)
  -> WorkflowStart hook (allow / deny / transform)
  -> phase[0] = entry_phase
  -> loop:
       evaluate advance_signal / halt_signal
       if halt: WorkflowComplete (verdict=abort)
       fan-out personas in phase.agents_invoked
       fan-in findings -> aggregate
       evaluate policies in order
       PhaseAdvance hook (allow / deny / transform)
       phase = next phase
       if cycle.exit_conditions.done: WorkflowComplete (verdict=done)
       if cycle.loop_bounds breached: WorkflowComplete (verdict=halted)
```

Each phase may internally invoke a single L3 cycle. With one persona that becomes plain L3; with several personas it follows the fan-out → fan-in pattern.

### The Five Policy Kinds

| Kind | Decision unit |
|---|---|
| `confidence-gating` | Split actionable vs suppressed findings by confidence × severity |
| `severity-routing` | Route severity × autofix_class into apply / gated / manual / advisory |
| `role-permissions` | Restrict sub-persona dispatch and the paths a persona may write |
| `mode-dispatch` | Vary UX and deliverables by interactive / autofix / report-only / headless mode |
| `loop-halt` | Stop a bounded loop on max_generations, oscillation, or grade regression |

Each rule is a `when` → `then` → `reason` triple. If nothing matches, the `default` (allow / deny / advisory) applies; if `default` is omitted, deny is the default-of-default (**fail-closed**). When reviewers disagree on the same fingerprint, the conservative choice wins (`safe_auto < gated_auto < manual < advisory`, `allow < deny`).

### Hooks & Audit Events

| Hook | When |
|---|---|
| `WorkflowStart` | Just before a cycle begins — allow / deny / transform |
| `PhaseAdvance` | Just before a phase transition — allow / deny / transform |
| `WorkflowComplete` | Just after a verdict is decided — observe / record |

The audit events L8 emits:

```text
workflow.started        cycle_id, session_id
workflow.phase_advanced cycle_id, from_phase, to_phase
workflow.policy_gated   policy_id, decision, reason
workflow.completed      cycle_id, verdict
workflow.aborted        cycle_id, reason
```

LLM calls produced by persona fan-out are still recorded by L2 as `llm.request` / `llm.response`; L8 only adds workflow context on top.

### L8 Design Invariants

- **Zero code lines to add a cycle**: adding `workflows/cycles/<id>.md` alone must be enough. If Python/Go/TS code must change, the design is broken.
- **Unknown IDs fail closed**: unknown cycle/phase/policy/persona IDs are denied by the `WorkflowRegistry`. Allow-list registration only.
- **Personas live in their own Markdown**: never inline a persona inside a cycle. Split into `personas/<role>/<id>.md` and reference by ID.
- **Signals are deterministic expressions**: never delegate `advance_signal` to free-form natural-language evaluation. Use evaluable expressions like `review_aggregate.p0_unresolved == 0`.
- **Artifact naming lives in the template**: do not describe naming as informal prose. Encode the pattern in the frontmatter of `artifacts/<id>-template.md`.

## Contracts

Contracts are execution requirements, not documentation decoration.

### Shared JSON Schemas

#### `completion_request_v1`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "completion_request_v1",
  "type": "object",
  "required": ["messages", "model", "schema_version"],
  "properties": {
    "messages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["role", "content"],
        "properties": {
          "role": {"type": "string"},
          "content": {"type": "string"}
        }
      }
    },
    "model": {"type": "string"},
    "tools": {"type": "array"},
    "max_tokens": {"type": "integer"},
    "temperature": {"type": "number"},
    "schema_version": {"const": "v1"}
  }
}
```

#### `completion_response_v1`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "completion_response_v1",
  "type": "object",
  "required": ["text", "tool_calls", "finish_reason", "usage", "model", "schema_version"],
  "properties": {
    "text": {"type": "string"},
    "tool_calls": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "args"],
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "args": {"type": "object"}
        }
      }
    },
    "finish_reason": {"enum": ["stop", "tool_use", "max_tokens", "safety"]},
    "usage": {
      "type": "object",
      "required": ["input_tokens", "output_tokens"],
      "properties": {
        "input_tokens": {"type": "integer"},
        "output_tokens": {"type": "integer"},
        "cost_usd": {"type": "number"}
      }
    },
    "model": {"type": "string"},
    "schema_version": {"const": "v1"}
  }
}
```

#### Role output schemas

```json
{
  "$id": "lead_directive_v1",
  "type": "object",
  "required": ["intent", "constraints", "schema_version"],
  "properties": {
    "intent": {"type": "string", "minLength": 1},
    "constraints": {"type": "array", "items": {"type": "string"}},
    "needs_advisor": {"type": "boolean"},
    "schema_version": {"const": "v1"}
  }
}
```

```json
{
  "$id": "plan_v1",
  "type": "object",
  "required": ["steps", "risks", "needs_advisor", "schema_version"],
  "properties": {
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "description"],
        "properties": {
          "id": {"type": "string"},
          "description": {"type": "string"},
          "depends_on": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "risks": {"type": "array", "items": {"type": "string"}},
    "needs_advisor": {"type": "boolean"},
    "schema_version": {"const": "v1"}
  }
}
```

```json
{
  "$id": "worker_report_v1",
  "type": "object",
  "required": ["output", "steps_completed", "schema_version"],
  "properties": {
    "output": {"type": "string"},
    "steps_completed": {"type": "array", "items": {"type": "string"}},
    "tool_calls_made": {"type": "array", "items": {"type": "string"}},
    "schema_version": {"const": "v1"}
  }
}
```

```json
{
  "$id": "review_result_v1",
  "type": "object",
  "required": ["verdict", "feedback", "schema_version"],
  "properties": {
    "verdict": {"enum": ["pass", "fail"]},
    "feedback": {"type": "string"},
    "schema_version": {"const": "v1"}
  }
}
```

#### L8 workflow schemas

L8-aware implementations register the following additional schemas. We keep only the identifiers in this page; the JSON definitions live in the upstream [`agent-os-runtime/schemas/`](https://github.com/entelecheia/agent-os-runtime/tree/main/schemas).

| Schema id | Role |
|---|---|
| `cycle_v1` | cycle frontmatter — phases, entry_phase, exit_conditions, policies |
| `phase_v1` | phase frontmatter — advance_signal, halt_signal, agents_invoked, artifacts |
| `policy_v1` | policy frontmatter — kind, default, rules (`when` / `then` / `reason`) |
| `finding_v1` | persona review finding — severity, autofix_class, confidence, fingerprint |
| `review_aggregate_v1` | fan-in result — coverage, p0_unresolved, top findings |
| `brainstorm_v1` / `plan_v1` (reused) / `solution_v1` / `learning_v1` / `pulse_report_v1` | per-cycle artifact deliverables |

The `autofix_class` enum on `finding_v1` (`safe_auto`, `gated_auto`, `manual`, `advisory`) is the input that drives the severity-routing policy.

#### `skill_frontmatter_v1` and `write_claim_v1`

```json
{
  "$id": "skill_frontmatter_v1",
  "type": "object",
  "required": ["name", "description"],
  "properties": {
    "name": {"type": "string"},
    "description": {"type": "string"},
    "triggers": {"type": "array", "items": {"type": "string"}},
    "allowed-tools": {"type": "array", "items": {"type": "string"}},
    "plugin": {"type": "string"},
    "version": {"type": "integer"},
    "schema_version": {"const": "v1"}
  }
}
```

```json
{
  "$id": "write_claim_v1",
  "type": "object",
  "required": ["who", "why", "expected_hash", "schema_version"],
  "properties": {
    "who": {"type": "string"},
    "why": {"type": "string"},
    "expected_hash": {"type": "string"},
    "schema_version": {"const": "v1"}
  }
}
```

### Canonical Role Prompts

#### Lead

```md
# Lead role

You are the lead agent. Your job is to receive a user request and turn it into a lead_directive_v1 JSON payload.

Return JSON:
{
  "intent": "<one-sentence statement of what the user wants>",
  "constraints": ["<constraint 1>", "<constraint 2>"],
  "needs_advisor": false,
  "schema_version": "v1"
}

Rules:
- Set needs_advisor true only when the request is ambiguous, high stakes, or scope-defining.
- Constraints capture explicit must/must-not statements from the user prompt.
- Output JSON only.
```

#### Planner

```md
# Planner role

Decompose a lead_directive_v1 into a step-by-step plan.

Return JSON matching plan_v1:
{
  "steps": [
    {"id": "s1", "description": "<what to do>", "depends_on": []}
  ],
  "risks": ["<risk 1>"],
  "needs_advisor": false,
  "schema_version": "v1"
}

Rules:
- Steps must be independently verifiable.
- depends_on lists step ids that must complete first.
- risks captures ambiguity, missing context, unavailable dependencies, or likely failure.
- Output JSON only.
```

#### Worker

```md
# Worker role

Execute the plan_v1 steps. Use available tools declared by the selected skill.

Return JSON matching worker_report_v1:
{
  "output": "<final result>",
  "steps_completed": ["s1", "s2"],
  "tool_calls_made": ["echo:t1"],
  "schema_version": "v1"
}

Rules:
- Use tools through dispatch_tool only.
- If a step fails, stop and report partial progress.
- Do not fabricate output or tool calls.
- Output JSON only.
```

#### Reviewer

```md
# Reviewer role

Verify a worker_report_v1 against the plan_v1 it was supposed to fulfill.

Return JSON matching review_result_v1:
{
  "verdict": "pass",
  "feedback": "<reason>",
  "schema_version": "v1"
}

Rules:
- verdict pass only if every plan step has a corresponding completed step and output addresses the intent.
- verdict fail requires concrete feedback.
- The runtime should prevent a role from reviewing its own output.
- Output JSON only.
```

### Example Skill

```md
---
name: greet
description: Echoes a greeting back to the user using the echo tool.
triggers:
  - greet
  - hello
  - hi
allowed-tools:
  - echo
plugin: skeleton
version: 1
schema_version: v1
---

# Greet skill

When a user prompt contains "greet", "hello", or "hi", this skill takes over.

1. Worker constructs a greeting string from the user's name, defaulting to "world".
2. Worker invokes the echo MCP tool with the greeting.
3. Worker reports the echoed value as final output.
4. Reviewer verifies output is non-empty.
```

### Example Hooks

```python
from unified.hooks import HookDecision, HookHandler

def make_pre_tool_use_handler() -> HookHandler:
    def fn(input: dict) -> HookDecision:
        return HookDecision(decision="allow", reason="default-allow")
    return HookHandler(id="pre_tool_use_default", fn=fn, priority=10)

def make_deny_dangerous_tools_handler() -> HookHandler:
    deny = {"rm", "delete", "drop_table"}
    def fn(input: dict) -> HookDecision:
        if input.get("tool") in deny:
            return HookDecision(decision="deny", reason=f"tool {input['tool']} on denylist")
        return HookDecision(decision="allow")
    return HookHandler(id="deny_dangerous_tools", fn=fn, priority=100)
```

```python
def make_stop_handler() -> HookHandler:
    def fn(input: dict) -> HookDecision:
        return HookDecision(decision="deny", reason="loop reached terminal state")
    return HookHandler(id="stop_after_one", fn=fn, priority=10)

def make_user_prompt_submit_handler() -> HookHandler:
    def fn(input: dict) -> HookDecision:
        prompt = input["prompt"]
        import re
        redacted = re.sub(r"\b\d{16}\b", "[REDACTED-CC]", prompt)
        if redacted != prompt:
            return HookDecision(
                decision="transform",
                output={"prompt": redacted},
                reason="redacted suspected card number",
            )
        return HookDecision(decision="allow")
    return HookHandler(id="redact_pii", fn=fn, priority=80)
```

### Contract Rules

- Role outputs are JSON only.
- Schema validation failure fails closed.
- Invalid skill frontmatter prevents skill registration.
- Tool calls must be inside the selected skill's `allowed-tools`.
- Hook transform outputs must pass the next boundary schema.
- Event payloads are routed by event type schema.

## Implementation Guide

This guide defines a course reference runtime, not a production framework. The goal is **semantic parity** across implementations, not feature count.

### Recommended directory shape

```text
agent-runtime/
├── schemas/
├── agents/
├── skills/greet/SKILL.md
├── hooks/
├── runtime/
│   ├── event_store.py
│   ├── schema.py
│   ├── mcp.py
│   ├── provider.py
│   ├── skills.py
│   ├── hooks.py
│   └── agents.py
└── sessions/
    └── sess_01/.events.jsonl
```

The shared contract surface is `schemas/`, `agents/`, and `skills/`. If Python, Go, and TypeScript fork these files, parity breaks.

### Minimal Python Runtime Shape

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")

@dataclass
class Ok(Generic[T]):
    value: T

@dataclass
class Err(Generic[E]):
    error: E

@dataclass
class DomainError:
    kind: str
    code: str
    message: str
    retryable: bool = False
```

Return domain failures as `Err(DomainError)`. Reserve exceptions for runtime invariant violations.

### Event Store

```python
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

@dataclass
class Event:
    id: str
    session_id: str
    ts: float
    type: str
    actor: str
    payload: dict
    schema_version: str = "v1"
    parent_id: str | None = None

class EventStore:
    def __init__(self, root: Path):
        self.root = root

    def append(self, session_id: str, type: str, actor: str, payload: dict, parent_id: str | None = None) -> Event:
        event = Event(
            id=str(uuid4()),
            session_id=session_id,
            ts=time.time(),
            type=type,
            actor=actor,
            payload=payload,
            parent_id=parent_id,
        )
        session_dir = self.root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        with (session_dir / ".events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        return event
```

### Replay

```python
def replay(events: EventStore, session_id: str) -> dict:
    snap = {
        "closed": False,
        "output": None,
        "cost": {"input": 0, "output": 0},
        "agents": {},
        "tools_invoked": [],
    }
    for event in events.read_all(session_id):
        if event.type == "llm.response":
            usage = event.payload.get("usage", {})
            snap["cost"]["input"] += usage.get("input_tokens", 0)
            snap["cost"]["output"] += usage.get("output_tokens", 0)
        elif event.type == "tool.invoke":
            snap["tools_invoked"].append(event.payload)
        elif event.type == "agent.transition":
            snap["agents"][event.actor] = event.payload.get("to")
        elif event.type == "worker.report":
            snap["output"] = event.payload.get("output")
        elif event.type == "session.close":
            snap["closed"] = True
    return snap
```

### Tool Dispatch

```python
def dispatch_tool(call, mcp, schemas, hooks, events, session_id, allowed_tools):
    if call.name not in allowed_tools:
        return Err(DomainError("gate", "TOOL_NOT_ALLOWED", call.name))

    tool = mcp.find_tool(call.name)
    if tool is None:
        return Err(DomainError("gate", "TOOL_NOT_FOUND", call.name))

    checked = schemas.validate(call.args, tool.schema_in)
    if isinstance(checked, Err):
        return checked

    gate = hooks.fire("PreToolUse", {"tool": call.name, "args": call.args})
    if gate.decision == "deny":
        return Err(DomainError("gate", "GATE_DENIED", gate.reason))

    invoke_event = events.append(session_id, "tool.invoke", "worker", {"name": call.name, "args": call.args})
    result = tool.invoke(gate.output or call.args)
    events.append(session_id, "tool.result", "tool", {"name": call.name, "result": result}, parent_id=invoke_event.id)
    hooks.fire("PostToolUse", {"tool": call.name, "result": result})
    return Ok(result)
```

### Plan-Work-Review Loop

```python
def handle_user_request(runtime, prompt: str):
    session_id = runtime.new_session_id()
    runtime.events.append(session_id, "session.start", "user", {"prompt": prompt})

    intake = runtime.hooks.fire("UserPromptSubmit", {"prompt": prompt})
    if intake.decision == "deny":
        runtime.events.append(session_id, "session.close", "system", {"ok": False, "reason": intake.reason})
        return Err(DomainError("gate", "PROMPT_DENIED", intake.reason))

    prompt = intake.output.get("prompt", prompt) if intake.decision == "transform" else prompt
    skill = runtime.skills.select(prompt)
    allowed_tools = set(skill.allowed_tools if skill else [])

    lead = runtime.call_role("lead", prompt, schema="lead_directive_v1", session_id=session_id)
    plan = runtime.call_role("planner", lead.value, schema="plan_v1", session_id=session_id)
    report = runtime.call_role("worker", plan.value, schema="worker_report_v1", session_id=session_id, allowed_tools=allowed_tools)
    review = runtime.call_role("reviewer", {"plan": plan.value, "report": report.value}, schema="review_result_v1", session_id=session_id)

    ok = review.value["verdict"] == "pass"
    runtime.hooks.fire("Stop", {"session_id": session_id, "ok": ok})
    runtime.events.append(session_id, "session.close", "system", {"ok": ok})
    return Ok({"session_id": session_id, "report": report.value, "review": review.value})
```

### Polyglot Parity

| Item | Python | Go | TypeScript |
|---|---|---|---|
| schema validation | real JSON Schema validation | minimal validation or deterministic checks | minimal validation or deterministic checks |
| event log | `.events.jsonl` append/read/replay | temp session log | test session log |
| provider | mock + real adapter boundary | deterministic mock | deterministic mock |
| skill discovery | YAML frontmatter validation | shared fixture read | shared fixture read |
| protected write | hash check + conflict | hash check + conflict | hash check + conflict |
| tests | end-to-end checklist | `go test ./...` | Node test runner |
| L8 workflow plane | `workflows/` SSOT loader (PR 5) | core-only (optional) | core-only (optional) |

L1–L7 is the core compliance surface; L8 is an optional plane. L8-capable implementations must read the `workflows/` directory (`cycles/`, `phases/`, `policies/`, `personas/`, `artifacts/`) as SSOT and add new cycles with zero code changes — that is the design invariant.

### Protected Write

```python
import hashlib
from pathlib import Path

def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def protected_write(path: Path, new_text: str, expected_hash: str, who: str, why: str):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if expected_hash and sha256_of(current) != expected_hash:
        return Err(DomainError("lock", "WRITE_CONFLICT", f"{who}: {why}"))
    path.write_text(new_text, encoding="utf-8")
    return Ok({"path": str(path), "hash": sha256_of(new_text)})
```

### End-to-End Test Criteria

```text
1. required schemas are loaded
2. greet skill is discovered
3. echo tool is registered
4. PreToolUse, Stop, UserPromptSubmit hooks are registered
5. provider can be swapped through RuntimeProfile
6. handle_user_request completes lead -> planner -> worker -> reviewer
7. .events.jsonl contains session, llm, agent, hook, skill, tool events
8. replay() reproduces closed snapshot and worker output
9. protected_write rejects stale expected_hash
10. invalid schema payload fails closed
11. UserPromptSubmit can redact a 16-digit sequence
```

## Checklist

Use this checklist for Lab 07 multi-agent pipelines, Lab 11 telemetry, and the Ralphthon capstone.

### Core (L1–L7) Implementation Checklist

- [ ] `Event` type and append-only `.events.jsonl` event store
- [ ] `replay()` recalculates snapshots from the event log
- [ ] `SchemaRegistry` loads and validates at least five schemas
- [ ] `RuntimeProfile` selects provider backend and model through config
- [ ] mock provider path enables deterministic end-to-end tests without API keys
- [ ] MCP-style `echo` tool is registered
- [ ] `dispatch_tool()` enforces allowed tools, schema, hooks, and events
- [ ] at least three hooks: `PreToolUse`, `Stop`, `UserPromptSubmit`
- [ ] Markdown skill discovery through `skills/greet/SKILL.md`
- [ ] skill frontmatter validation and invalid skill skip
- [ ] Plan-Work-Review loop: Lead -> Planner -> Worker -> Reviewer
- [ ] role output schema validation
- [ ] protected write conflict detection
- [ ] schema violations fail closed rather than silently passing

### L8 Workflow-Plane Checklist (optional)

A runtime that also claims L8 support must, on top of the core checklist:

- [ ] a `WorkflowRegistry` that loads cycle / phase / policy / persona / artifact Markdown SSOT fail-closed
- [ ] `cycle_v1`, `phase_v1`, `policy_v1` schemas plus per-cycle artifact schemas
- [ ] `workflow.started`, `workflow.phase_advanced`, `workflow.policy_gated`, `workflow.completed`, `workflow.aborted` events
- [ ] `WorkflowStart`, `PhaseAdvance`, `WorkflowComplete` hook integration
- [ ] replay snapshot reconstruction for current cycle, current phase, verdict, and visited phases
- [ ] new cycles/phases/policies/personas can be added by writing Markdown alone (zero code lines)
- [ ] unknown cycle/phase/policy/persona IDs deny fail-closed

### Audit Completeness

A successful session should include at least:

```text
session.start
hook.fired
skill.invoke
agent.transition
llm.request
llm.response
tool.invoke
tool.result
worker.report
skill.complete
session.close
```

Sessions that run through the L8 plane add the following on top:

```text
workflow.started
workflow.phase_advanced   (one per phase transition)
workflow.policy_gated     (one per policy decision)
workflow.completed        (verdict=done|halted)
workflow.aborted          (verdict=abort)
```

Audit failure if any of these are missing:

- all LLM request/response pairs;
- all tool invoke/result pairs;
- all agent state transitions;
- all hook decisions;
- all schema violations;
- session close.

### Fail-closed Cases

| Case | Expected behavior |
|---|---|
| unknown tool | `TOOL_NOT_FOUND` |
| tool outside selected skill | `TOOL_NOT_ALLOWED` |
| invalid role JSON | `MALFORMED_AGENT_MESSAGE` |
| missing schema id | invariant violation or schema error |
| hook timeout/exception | deny |
| stale file hash | `WRITE_CONFLICT` |
| provider retry exhausted | `PROVIDER_ERROR` |
| reviewer verdict fail | rework or human escalation |

### Anti-patterns

| Anti-pattern | Why it is bad | Alternative |
|---|---|---|
| direct filesystem/network calls inside runtime | breaks audit and sandbox boundary | MCP tool dispatch |
| provider SDK object leaks into business logic | provider swap requires code edits | thin adapter |
| prose role handoff | downstream parsing is nondeterministic | versioned JSON Schema |
| in-place event edits | breaks replay and causality | append `event.amended` |
| skill registered in code | operational knowledge is locked in deploy artifact | Markdown discovery |
| hook directly mutates runtime state | mixes policy and state transition | return decision + append event |
| breaking schema v1 | old session replay breaks | add v2 schema |
| inlining a persona inside a cycle | breaks audit, coverage, and role-permissions | split into `personas/<role>/<id>.md`; cycle references the ID |
| natural-language `advance_signal` | signal is nondeterministic, replay/regression impossible | deterministic expression like `review_aggregate.p0_unresolved == 0` |
| hard-coding policy inside Python | new policies are locked to a deploy cycle | register in `workflows/policies/` and reference by ID |
| new cycle requires Python edits | the workflow plane collapses back into the code plane | add Markdown to `workflows/cycles/` only |
| skipping L4 audit for a workflow transition | invariant violation — replay/audit broken | append a `workflow.*` event for every phase/policy transition |

### Lab Rubric

| Criterion | Passing condition |
|---|---|
| Runtime boundary | tool/provider/skill/hook/schema/event responsibilities are separated |
| Contract discipline | role outputs and tool boundaries pass schema validation |
| Observability | `.events.jsonl` and replay snapshot submitted |
| Safety | at least two fail-closed cases tested |
| Determinism | repeatable end-to-end test through mock provider |
| Documentation | README includes commands, event examples, and known limitations |

### Example Submission

```text
assignments/lab-07/20230001/
├── schemas/
├── agents/
├── skills/greet/SKILL.md
├── runtime/
├── tests/
├── sessions/example/.events.jsonl
├── replay_snapshot.json
└── README.md
```

The README must include execution commands, mock-provider test instructions, at least 10 event trace lines, a way to reproduce schema violation or hook denial, and known limitations.

## Course Connections

| Week | Connection |
|---|---|
| Week 03 | MCP is a capability boundary, not just a convenience API |
| Week 04 | Ralph Loop becomes operational when Stop hooks and event logs are added |
| Week 05 | Context reset is safe only with Markdown state and event replay |
| Week 06 | CLAUDE.md/PROMPT.md generalizes into a Markdown-SSOT skill runtime |
| Week 07 | The gated multi-agent SDLC pipeline generalizes as one instance of an L8 cycle/phase definition |
| Week 09 | The three-way parallel reviewer plus severity PASS/FAIL is an informal implementation of L8's **persona fan-out + severity-routing** policy |
| Week 12 | Telemetry includes OpenTelemetry spans and replayable event logs — `workflow.*` events join the audit surface when L8 is used |
| Week 13–14 | Team runtime checklist can become the rubric. Teams that run multi-phase cycles may additionally submit L8 cycle/phase/policy Markdown SSOT |
