---
title: Agent OS Runtime
description: MCP-first, provider-agnostic, event-sourced agent runtime (+ L8 workflow plane) 단일 참고자료
---

Agent OS Runtime은 에이전트를 "프롬프트를 잘 쓰는 프로그램"이 아니라 **검증 가능한 런타임 시스템**으로 다루기 위한 기준 아키텍처다. 이 문서는 독립 교재다. 별도 저장소나 외부 문서를 읽지 않아도 전체 구조, 계약, 예시, 구현 기준, 체크리스트를 한 페이지에서 따라갈 수 있게 구성했다.

핵심 문장:

> MCP-first, provider-agnostic, Plan-Work-Review, event-sourced, Markdown-SSOT, hook-gated, schema-versioned — and a workflow plane on top.

## 왜 필요한가

AI 코딩 에이전트는 강력하지만 기본 상태로는 다음 문제가 있다.

| 문제 | 런타임 관점의 해법 |
|---|---|
| 도구 호출 추적이 어려움 | 모든 외부 능력을 MCP-style dispatch로 통과 |
| provider 교체 시 코드가 흔들림 | 얇은 provider adapter와 공통 request/response 계약 |
| 에이전트 간 handoff가 자연어라 깨짐 | versioned JSON Schema로 IPC 검증 |
| 긴 실행 후 상태 재구성이 어려움 | append-only event log와 replay |
| 운영 정책이 코드 안에 섞임 | hook으로 allow, deny, transform 외부화 |
| prompt/skill/role 설명이 코드와 분리됨 | Markdown을 source of truth로 유지 |
| 다중 phase 워크플로우 규칙이 코드에 흩어짐 | cycle / phase / policy / persona / artifact를 SSOT(L8)로 분리 |

## 5개 불변 조건

| ID | 불변 | 의미 |
|---|---|---|
| I-1 | Replayability | 모든 LLM 호출과 상태 전이는 append-only event log에 남고, snapshot은 log에서 다시 계산 가능 |
| I-2 | Provider Sovereignty | provider 교체는 config/profile 변경으로 끝나야 하며 비즈니스 로직은 수정하지 않음 |
| I-3 | Fail-closed Gates | hook, schema validation, tool registration은 실패 시 기본 deny |
| I-4 | Markdown is SSOT | skill, role, project context는 Markdown이 기준이고 코드는 이를 로드해 해석 |
| I-5 | Schema-versioned IPC | agent, runtime, hook, tool 사이의 모든 메시지는 versioned schema로 검증 |

## 한 요청의 흐름

사용자가 `"fix the bug in auth.ts"`라고 요청하면 런타임은 다음 순서로 처리한다.

1. `session.start` event를 기록한다.
2. `UserPromptSubmit` hook이 prompt를 허용, 거부, 변형한다.
3. Markdown skill registry가 관련 skill을 탐색한다.
4. matching skill이 있으면 해당 skill의 `allowed-tools`로 tool scope를 제한한다.
5. Lead가 요청을 `lead_directive_v1`로 정리한다.
6. Planner가 `plan_v1`을 만든다.
7. Worker가 tool dispatch를 통해 작업하고 `worker_report_v1`을 만든다.
8. Reviewer가 `review_result_v1`로 통과/실패를 판정한다.
9. Stop hook이 루프 종료 여부를 결정한다.
10. `session.close` event를 기록하고 replay 가능한 snapshot을 남긴다.

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

L8 workflow plane을 쓰는 요청은 위 단일 request 흐름을 cycle로 감싼다. 이때 core event에 더해 `workflow.started`, `workflow.phase_advanced`, `workflow.policy_gated`, `workflow.completed` 또는 `workflow.aborted`가 남고, replay snapshot은 현재 cycle, phase, verdict까지 복원해야 한다. L8을 쓰지 않는 구현은 여전히 L1–L7 core runtime으로 완전한 평가 대상이다.

## 7-Layer Architecture

Agent OS Runtime의 목적은 "모델에게 일을 시킨다"가 아니라 **비결정적 모델 호출을 결정론적으로 관측, 검증, 재실행 가능한 시스템에 넣는 것**이다. L1–L7은 한 번의 request를 안전하게 실행하는 core runtime이고, 그 위에 다중 phase 사이클을 시퀀싱하는 [L8 Workflow Plane](#workflow-plane-l8)이 옵션 plane으로 얹힌다(7+1 구조).

| Layer | 이름 | 책임 |
|---|---|---|
| L1 | MCP-first Tool Protocol | 외부 능력을 schema, hook, event가 붙은 tool boundary로 통과 |
| L2 | Provider-agnostic Completion | Anthropic, OpenAI, Gemini, local model을 같은 call shape으로 추상화 |
| L3 | Plan-Work-Review Collaboration | 역할 분리와 상태 전이로 다중 에이전트 실행 제어 |
| L4 | Append-only Event Store | audit log, replay source, cost/progress snapshot의 원천 |
| L5 | Markdown-SSOT Skill Runtime | skill discovery, trigger matching, allowed tool scope |
| L6 | Hook-intercepted Lifecycle | 보안, redaction, rate limit, loop stop 정책을 외부화 |
| L7 | Schema-versioned IPC Registry | 모든 boundary payload를 versioned JSON Schema로 검증 |
| L8 | Workflow Orchestration | cycle / phase / policy / persona / artifact 5축을 SSOT로 시퀀싱 |

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

L4와 L7은 모든 레이어를 가로지른다. event를 남기지 않는 상태 변화, schema를 통과하지 않는 boundary payload는 런타임 밖의 side effect로 취급한다. L6은 위에서 모든 레이어를 가로채고(interception), L8은 L1–L7 위에 얹는 workflow plane이다 — 같은 5개 불변(I-1~I-5)을 상속하며, 단일 prompt가 아니라 "여러 phase를 어떤 순서로 굴려서 어떤 verdict로 종료할지"를 결정한다.

### L1 MCP-first Tool Protocol

L1은 runtime이 외부 세계와 만나는 유일한 능력 경계다. 파일 I/O, web fetch, database query, shell command, sub-agent dispatch는 runtime 내부에서 직접 호출하지 않고 tool registry를 통과한다.

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

실행 순서:

1. tool name을 registry에서 찾는다.
2. caller의 allowed tool scope에 포함되는지 확인한다.
3. `schema_in`으로 args를 검증한다.
4. `PreToolUse` hook을 실행한다.
5. `tool.invoke` event를 append한다.
6. 실제 tool을 호출한다.
7. `tool.result` event를 append한다.
8. `PostToolUse` hook을 실행한다.
9. `schema_out`으로 결과를 검증한다.

금지 패턴:

- business code에서 직접 `fs.readFileSync`, `subprocess.run`, HTTP client 호출
- input schema만 있고 output schema가 없음
- hook deny를 무시하고 tool을 계속 실행

### L2 Provider-agnostic Completion

L2는 LLM provider를 단일 인터페이스로 바꾼다. provider별 SDK 객체는 adapter 내부에만 둔다.

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

불변 조건:

- provider 교체는 `RuntimeProfile` 변경으로 끝난다.
- request와 response는 event log에 남기기 전 redaction한다.
- retry는 adapter boundary 안에서 처리하고, domain failure는 structured error로 반환한다.

### L3 Plan-Work-Review Collaboration

단일 agent가 계획, 실행, 검토를 모두 맡으면 자기 평가가 약하고 큰 task에서 발산하기 쉽다. 최소 역할은 다음과 같다.

| Role | 책임 |
|---|---|
| Lead | 사용자 요청을 intent와 constraints로 정리 |
| Planner | verifiable step과 risk를 포함한 plan 작성 |
| Worker | plan step 실행, tool 사용 기록, 결과 보고 |
| Reviewer | plan과 worker report 비교, pass/fail 판정 |
| Advisor | ambiguous/high-stakes request의 외부 의견 |
| Scaffolder | 파일/브랜치/test stub 생성 |

```text
INTAKE -> LEAD -> PLAN -> WORK -> REVIEW -> DONE
                              ^       |
                              |       v
                            REWORK <- FAIL
```

모든 전이는 `agent.transition` event로 남긴다. handoff는 자연어가 아니라 `lead_directive_v1`, `plan_v1`, `worker_report_v1`, `review_result_v1` 같은 schema-bound JSON이어야 한다.

### L4 Append-only Event Store

"현재 상태"는 source of truth가 아니라 event log에서 계산한 view다.

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

저장 규칙:

- 한 session은 `sessions/{session_id}/.events.jsonl`을 가진다.
- event는 append만 한다.
- 기존 event 정정은 in-place edit가 아니라 `event.amended` 새 event로 표현한다.
- snapshot은 항상 event log에서 재계산 가능해야 한다.
- Replay는 side effect를 만들지 않는다. LLM, tool, hook을 다시 실행하면 replay가 아니라 re-run이다.

### L5 Markdown-SSOT Skill Runtime

Skill은 언제 사용되는지, 어떤 tool을 허용하는지, 어떤 절차를 따르는지를 Markdown으로 선언한다.

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

skill discovery flow:

1. runtime startup에서 skill roots를 scan한다.
2. `SKILL.md` 파일의 frontmatter를 읽는다.
3. `skill_frontmatter_v1`로 검증한다.
4. registry에 skill id로 등록한다.
5. user prompt가 trigger에 매칭되면 skill을 선택한다.
6. selected skill의 `allowed-tools`를 L1 dispatch scope로 전달한다.

Markdown이 canonical이다. code와 skill body가 충돌하면 code를 Markdown에 맞게 고쳐야 한다.

### L6 Hook-intercepted Lifecycle

Hook은 callback이 아니라 policy decision을 반환하는 gate다.

| Hook | 용도 |
|---|---|
| SessionStart | session 초기화 정책 |
| UserPromptSubmit | prompt redaction, reject, rewrite |
| PreToolUse | tool 실행 전 allow/deny/transform |
| PostToolUse | tool 결과 관찰, redaction |
| SkillStart | skill-specific policy |
| Stop | loop 종료 또는 continuation 결정 |
| PreCompact | context compaction 전 보호 |

```ts
type HookDecision =
  | { decision: "allow"; reason?: string }
  | { decision: "deny"; reason: string }
  | { decision: "transform"; output: unknown; reason?: string };
```

hook handler가 throw하거나 timeout이면 기본 decision은 deny다. Hook은 runtime state를 직접 mutate하지 않고, caller가 event append를 통해 상태를 바꾼다.

### L7 Schema-versioned IPC

모든 message boundary는 versioned JSON Schema로 고정한다.

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

validation points:

- provider request 전
- provider response 후
- role output parse 후
- skill registration 시
- tool input/output boundary
- hook transform output이 boundary를 넘을 때

`v1`은 frozen이다. backward-incompatible change가 필요하면 `plan_v2.json`을 새로 추가하고 v1을 보존한다.

## Workflow Plane (L8)

L1–L7은 한 번의 agent request를 결정론적으로 실행하는 core primitive다. 그러나 "오늘 어떤 사이클부터 시작해서 어떻게 종료할지"는 비어 있다. **L8 Workflow Orchestration**은 L3 한 사이클(Plan-Work-Review)을 building block으로 다음 5축을 SSOT(markdown + JSON Schema)로 정의한다.

| 축 | 정의 단위 | 위치 | Schema |
|---|---|---|---|
| **Cycle** | 사용자 의도 묶음, 진입/종료/abort 조건, loop bound | `workflows/cycles/` | `cycle_v1` |
| **Phase** | cycle 내부 단계, `advance_signal` / `halt_signal`, persona 호출 | `workflows/phases/` | `phase_v1` |
| **Policy** | 게이팅 규칙 (allow / deny / advisory, default deny) | `workflows/policies/` | `policy_v1` |
| **Persona** | L3 6역할 위에 얹는 도메인 specialist (reviewer / researcher 등) | `workflows/personas/` | `skill_frontmatter_v1` 호환 |
| **Artifact** | 산출물 템플릿, 명명 규칙, frontmatter | `workflows/artifacts/` | template별 schema |

L8은 L3를 호출하지만 L1·L2를 직접 참조하지 않는다(L3가 호출). 같은 5개 불변(I-1~I-5)을 상속하므로 workflow 정의도 결정론적·감사 가능·provider 무관해야 한다.

### Execution Flow

```text
USER REQUEST
  -> resolve cycle_id (skill 또는 lead_directive로부터)
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

각 phase는 내부적으로 L3 한 사이클을 호출할 수 있다. persona가 단일이면 L3 그대로, 다중이면 fan-out → fan-in 패턴.

### Policy 5종

| Kind | 결정 단위 |
|---|---|
| `confidence-gating` | finding의 confidence × severity로 actionable / suppressed 분리 |
| `severity-routing` | severity × autofix_class로 즉시 적용 / 게이트 / manual / advisory 분기 |
| `role-permissions` | persona가 호출 가능한 sub-persona, write-claim 가능 path 제한 |
| `mode-dispatch` | interactive / autofix / report-only / headless 모드별 UX·산출물 차이 |
| `loop-halt` | bounded loop의 max_generations, oscillation, grade regression 정지 |

각 rule은 `when` → `then` → `reason` 3-tuple. 미매칭 시 `default`(allow / deny / advisory) 적용. `default` 미지정 시 deny가 default of default (**fail-closed**). 여러 reviewer가 같은 fingerprint에 다른 결정을 내리면 보수적 결정 채택(`safe_auto < gated_auto < manual < advisory`, `allow < deny`).

### Hooks & Audit Events

| Hook | 시점 |
|---|---|
| `WorkflowStart` | cycle 진입 직전 — allow / deny / transform |
| `PhaseAdvance` | phase 전환 직전 — allow / deny / transform |
| `WorkflowComplete` | verdict 결정 직후 — observe / record |

남기는 audit event:

```text
workflow.started        cycle_id, session_id
workflow.phase_advanced cycle_id, from_phase, to_phase
workflow.policy_gated   policy_id, decision, reason
workflow.completed      cycle_id, verdict
workflow.aborted        cycle_id, reason
```

페르소나 fan-out으로 발생하는 LLM 호출은 L2가 `llm.request`/`llm.response`로 기록하고, L8은 그 위에 workflow context만 더한다.

### L8 Design Invariants

- **새 cycle 추가에 코드 0줄**: `workflows/cycles/<id>.md`에 markdown만 추가하면 동작해야 한다. Python/Go/TS 코드 변경이 필요하면 설계 위반.
- **미등록 ID는 fail-closed**: unknown cycle/phase/policy/persona ID는 `WorkflowRegistry`에서 deny. allow-list 등록만 승인.
- **persona는 markdown에 분리**: cycle 안에 persona를 inline으로 작성하지 않는다. `personas/<role>/<id>.md`로 분리, cycle은 ID로만 참조.
- **신호는 결정론적 expression**: `advance_signal`을 한국어/자연어 평가에 위탁하지 않는다. `review_aggregate.p0_unresolved == 0` 같은 평가 가능한 표현식만 사용.
- **artifact 명명은 template에 명시**: 산출물 명명 규칙을 비공식 prose로 두지 않고 `artifacts/<id>-template.md`의 frontmatter에 패턴으로 정의.

## Contracts

Agent OS Runtime에서 계약은 문서 장식이 아니라 실행 조건이다. schema, role prompt, skill, hook이 모두 repository 안의 명시적 artifact로 존재해야 한다.

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

L8 workflow plane을 사용하는 구현은 추가로 다음 schema를 등록한다. 아래 표는 학생 구현에 필요한 최소 계약이며, 실제 파일은 `workflows/` Markdown frontmatter와 산출물 JSON이 이 구조를 만족해야 한다.

| Schema id | 필수/핵심 필드 | 역할 |
|---|---|---|
| `cycle_v1` | `id`, `phases`, `entry_phase`, `schema_version`; 선택 `exit_conditions`, `loop_bounds`, `policies` | 사용자 의도를 phase sequence와 종료 조건으로 묶음 |
| `phase_v1` | `id`, `advance_signal`, `schema_version`; 선택 `halt_signal`, `agents_invoked`, `input_schema`, `output_schema`, `policies` | cycle 내부의 결정론적 단계 |
| `policy_v1` | `id`, `kind`, `rules`, `schema_version`; 선택 `default` | `when` / `then` / `reason` 규칙으로 allow, deny, advisory 결정 |
| `finding_v1` | `id`, `reviewer`, `severity`, `autofix_class`, `confidence`, `title`, `schema_version` | persona review 결과 단위 |
| `review_aggregate_v1` | `findings`, `suppressed`, `pre_existing`, `verdict`, `schema_version`; 선택 `coverage`, `p0_unresolved` | fan-in 결과와 gate 입력 |
| `brainstorm_v1` / `plan_v1` (재사용) / `solution_v1` / `learning_v1` / `pulse_report_v1` | 산출물별 필수 필드는 각 schema가 정의 | cycle별 artifact 산출물 |

`finding_v1.severity`는 `P0`–`P3`, `confidence`는 `0/25/50/75/100`, `autofix_class`는 `safe_auto`, `gated_auto`, `manual`, `advisory` 중 하나다. 수업 실습에서 쓰는 `critical/major/minor/info`는 각각 `P0/P1/P2/P3`로 매핑해도 된다.

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

- 모든 role output은 JSON only다.
- schema validation 실패는 silent fallback이 아니라 fail-closed다.
- skill frontmatter가 invalid이면 해당 skill은 등록하지 않는다.
- tool call은 selected skill의 `allowed-tools` 안에 있어야 한다.
- hook transform output도 다음 boundary schema를 통과해야 한다.
- event payload는 event type에 맞는 schema로 routing되어야 한다.

## Implementation Guide

이 구현 가이드는 production framework가 아니라 수업용 reference runtime을 만드는 기준이다. 목표는 기능 수가 아니라 **동일한 계약을 여러 언어에서 같은 의미로 실행하는 parity**다.

### 권장 디렉터리 구조

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

공유 계약 surface는 `schemas/`, `agents/`, `skills/`다. Python, Go, TypeScript 구현이 이 파일들을 fork하면 parity가 깨진다.

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

도메인 실패는 exception보다 `Err(DomainError)`로 반환한다. exception은 runtime invariant 위반에만 사용한다.

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

| 항목 | Python | Go | TypeScript |
|---|---|---|---|
| schema validation | 실제 JSON Schema validation | 최소 validation 또는 deterministic checks | 최소 validation 또는 deterministic checks |
| event log | `.events.jsonl` append/read/replay | temp session log | test session log |
| provider | mock + real adapter boundary | deterministic mock | deterministic mock |
| skill discovery | YAML frontmatter validation | shared fixture read | shared fixture read |
| protected write | hash check + conflict | hash check + conflict | hash check + conflict |
| tests | end-to-end checklist | `go test ./...` | Node test runner |
| L8 workflow plane | `workflows/` SSOT loader | core-only (선택) | core-only (선택) |

L1–L7은 core compliance, L8은 옵셔널 plane이다. L8을 지원하는 구현은 `workflows/` 디렉토리(`cycles/` `phases/` `policies/` `personas/` `artifacts/`) SSOT만 읽으면 동작해야 하며, 새 cycle 추가에 코드 0줄이 design invariant다.

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

이 체크리스트는 Lab 07 이후 멀티에이전트 파이프라인, Lab 11 telemetry, 캡스톤 Ralphthon 평가에 공통으로 사용할 수 있다.

### Core (L1–L7) Implementation Checklist

- [ ] `Event` type과 append-only `.events.jsonl` event store
- [ ] `replay()` function: event log에서 snapshot 재계산
- [ ] `SchemaRegistry`: 최소 5종 schema 로드와 validation
- [ ] `RuntimeProfile`: provider backend와 model을 config로 선택
- [ ] mock provider path: API key 없이 deterministic end-to-end test 가능
- [ ] MCP-style `echo` tool 등록
- [ ] `dispatch_tool()`: allowed tool, schema, hook, event 기록을 모두 통과
- [ ] 최소 3개 hook: `PreToolUse`, `Stop`, `UserPromptSubmit`
- [ ] Markdown skill discovery: `skills/greet/SKILL.md`
- [ ] skill frontmatter validation과 invalid skill skip
- [ ] Plan-Work-Review loop: Lead -> Planner -> Worker -> Reviewer
- [ ] role output schema validation
- [ ] protected write conflict detection
- [ ] schema violation이 silent pass가 아니라 fail-closed error로 남음

### L8 Workflow-Plane Checklist (옵션)

L8 plane을 함께 지원한다고 주장하려면 core checklist에 더해 다음을 만족한다. L8이 없어도 L1–L7 core-compatible runtime일 수 있다.

- [ ] `WorkflowRegistry`: cycle / phase / policy / persona / artifact markdown SSOT를 fail-closed로 로드
- [ ] `cycle_v1`, `phase_v1`, `policy_v1` schemas와 cycle별 artifact schema 등록
- [ ] `workflow.started`, `workflow.phase_advanced`, `workflow.policy_gated`, `workflow.completed`, `workflow.aborted` event
- [ ] `WorkflowStart`, `PhaseAdvance`, `WorkflowComplete` hook 통합
- [ ] replay snapshot이 current cycle, current phase, verdict, visited phases를 복원
- [ ] 새 cycle/phase/policy/persona를 markdown 추가만으로 등록 가능 (코드 0줄)
- [ ] unknown cycle/phase/policy/persona ID는 deny (fail-closed)

### Audit Completeness

하나의 성공 session에는 최소한 아래 event type이 있어야 한다.

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

L8 plane을 사용하는 session은 위 목록에 다음이 추가된다:

```text
workflow.started
workflow.phase_advanced   (phase 전환마다 1회)
workflow.policy_gated     (policy decision마다 1회)
workflow.completed        (verdict=done|halted)
workflow.aborted          (verdict=abort)
```

다음 항목 중 하나가 빠지면 audit failure로 본다.

- 모든 LLM request/response 쌍
- 모든 tool invoke/result 쌍
- 모든 agent state transition
- 모든 hook decision
- 모든 schema violation
- session close 여부

### Fail-closed Cases

| 상황 | 기대 동작 |
|---|---|
| unknown tool | `TOOL_NOT_FOUND` |
| selected skill 밖 tool | `TOOL_NOT_ALLOWED` |
| invalid role JSON | `MALFORMED_AGENT_MESSAGE` |
| missing schema id | invariant violation 또는 schema error |
| hook timeout/exception | deny |
| stale file hash | `WRITE_CONFLICT` |
| provider retry exhausted | `PROVIDER_ERROR` |
| reviewer verdict fail | rework 또는 human escalation |

### Anti-patterns

| Anti-pattern | 왜 문제인가 | 대체 |
|---|---|---|
| runtime 내부에서 직접 filesystem/network 호출 | audit과 sandbox boundary가 깨짐 | MCP tool dispatch |
| provider SDK object가 business logic까지 퍼짐 | provider 교체가 코드 수정으로 번짐 | thin adapter |
| role output을 prose로 handoff | downstream parsing이 비결정적 | versioned JSON Schema |
| event를 in-place 수정 | replay와 causality가 깨짐 | `event.amended` 새 event |
| skill을 코드로 등록 | 운영 지식이 배포 artifact에 묶임 | Markdown discovery |
| hook이 runtime state를 직접 mutate | policy와 state transition이 섞임 | decision 반환 + caller event append |
| schema v1을 breaking change | 과거 session replay가 깨짐 | v2 schema 추가 |
| persona를 cycle 안에 inline 작성 | audit, coverage, role-permissions 적용이 깨짐 | `personas/<role>/<id>.md`로 분리, cycle은 ID 참조 |
| `advance_signal`을 자연어 평가에 위탁 | 신호가 비결정적이라 replay/regression이 불가능 | `review_aggregate.p0_unresolved == 0` 같은 결정론적 expression |
| policy를 코드 안에 하드코딩 | 새 정책 추가가 배포 사이클에 묶임 | `workflows/policies/`에 등록, ID로 참조 |
| 새 cycle 추가에 Python 수정 | workflow plane이 코드 plane으로 회귀 | `workflows/cycles/`에 markdown만 추가 |
| L4 audit을 우회한 transition | invariant 위반 — replay/감사 실패 | 모든 phase/policy 전환을 `workflow.*` event로 append |

### Lab Rubric

| 기준 | 통과 조건 |
|---|---|
| Runtime boundary | tool/provider/skill/hook/schema/event 책임이 분리되어 있음 |
| Contract discipline | role output과 tool boundary가 schema validation을 통과 |
| Observability | `.events.jsonl`과 replay snapshot 제출 |
| Safety | fail-closed 사례 2개 이상 테스트 |
| Determinism | mock provider로 반복 가능한 end-to-end test |
| Documentation | README에 실행 명령, event 예시, known limitations 기록 |

### 제출물 예시

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

README에는 실행 명령, mock provider로 end-to-end test를 돌리는 방법, event trace 예시 10줄 이상, schema violation 또는 hook deny 재현 방법, known limitations를 포함한다.

## 강의 연결

| 주차 | 연결 지점 |
|---|---|
| Week 03 | MCP는 편의 API가 아니라 capability boundary |
| Week 04 | Ralph Loop는 Stop hook과 event log가 결합될 때 운영 가능한 루프가 됨 |
| Week 05 | Context reset은 Markdown state와 event replay가 있어야 안전함 |
| Week 06 | CLAUDE.md/PROMPT.md는 Markdown-SSOT skill runtime으로 일반화 가능 |
| Week 07 | 멀티에이전트 SDLC의 게이트드 파이프라인은 L8 cycle/phase의 인스턴스로 일반화 가능 |
| Week 09 | 3-병렬 리뷰어 + 심각도 PASS/FAIL은 L8 **persona fan-out + severity-routing** 정책의 비공식 구현 |
| Week 12 | telemetry는 OpenTelemetry span뿐 아니라 replay 가능한 event log까지 포함 — L8 사용 시 `workflow.*` event도 audit 대상 |
| Week 13–14 | 팀별 runtime checklist를 rubric으로 사용 가능. 다중 phase 사이클을 굴리는 팀은 L8 workflow plane의 cycle/phase/policy markdown SSOT를 함께 제출 |
