---
title: 용어집
description: AI 시스템 2026 강의 주요 용어 정의
---

## 용어집

이 강의에서 사용하는 핵심 용어를 알파벳순으로 정리했다.

---

**autoresearch (자율 연구 루프)**
: Andrej Karpathy가 공개한 자율 ML 실험 루프. 에이전트가 train.py를 수정하고, 고정 시간 예산(5분) 후 val_bpb를 측정하여 개선되면 commit, 아니면 reset한다. Ralph Loop과 동일한 패턴이되 검증 조건이 테스트 통과가 아닌 메트릭 개선이다.

**AI System (AI 시스템)**
: EU AI Act(Article 3) 정의 — varying levels of autonomy로 동작하며 input으로부터 output을 추론하는 machine-based system. AI 모델(엔진)에 도구 사용, 메모리, 계획, 실행 환경, 안전 장치, 관측성을 감싼 전체 구조. 모델이 엔진이라면 AI 시스템은 자동차다.

**Agentic System (에이전틱 시스템)**
: 파일 수정, 코드 실행, API 호출 등 실제 행동을 자율적으로 수행하는 AI 시스템. 단순 텍스트 생성을 넘어 환경과 상호작용한다.

**Agent Ops**
: 에이전트 시스템의 운영 discipline. 모델 배포보다 tool boundary, permission, event log, replay, policy gate, human override, telemetry를 관리하는 데 초점을 둔다.

**Automatic Prefix Caching**
: 반복되는 system prompt, tool schema, instruction 파일 등 정적 prefix의 KV cache를 재사용하는 추론 서버 최적화. Ralph 루프처럼 같은 prefix를 반복 호출하는 workload에서 TTFT와 비용을 줄인다.

**Bitter Lesson (비터 레슨)**
: Rich Sutton(2019)이 제시한 원칙. 연산을 활용하는 일반적 방법이 도메인 지식을 활용하는 특수한 방법보다 궁극적으로 효과적이다. 사전학습 스케일링(GPT-3→GPT-4)은 "학습" 측면, test-time compute scaling(o1, DeepSeek R1)은 "탐색" 측면의 구현이다.

**Backpressure (백프레셔)**
: Ralph 루프에서 에이전트 출력이 기준에 맞지 않을 때 시스템이 자동으로 거부하고 재시도를 강제하는 메커니즘. 컴파일러, 타입 체커, 테스트 스위트가 대표적 백프레셔 구성 요소.

**Bootstrap Sequence (부트스트랩 시퀀스)**
: Claude Code 세션 시작 시 7단계 초기화 과정. prefetch → warning handler → CLI parse → concurrent setup → deferred init → mode routing → query engine loop. FastPath 최적화로 단순 명령은 전체 초기화를 건너뛴다.

**Compaction (컴팩션)**
: 긴 대화에서 오래된 턴을 요약하여 토큰 예산 내로 압축하는 메커니즘. Claude Code에서는 12턴 초과 시 자동 트리거되며, 최근 4개 메시지를 보존하고 나머지를 plaintext 변환 + 중복 제거로 압축한다.

**Context Engineering (컨텍스트 엔지니어링)**
: 에이전트에 입력되는 컨텍스트를 체계적으로 설계하는 분야. Simon Willison이 2026년 명명. 프롬프트 엔지니어링이 "무엇을 말할 것인가"라면, 컨텍스트 엔지니어링은 "어떤 정보를 어떤 형식으로 어떤 순서에 넣을 것인가"까지 포괄한다.

**Context Rot (컨텍스트 부패)**
: 장기 실행 에이전트에서 컨텍스트 창이 실패 시도와 오래된 코드로 채워져 추론 품질이 저하되는 현상.

**Context Window (컨텍스트 창)**
: LLM이 한 번에 처리할 수 있는 최대 토큰 수. 최신 frontier 모델은 수십만~100만 토큰급 창을 제공하지만, 실효 사용량은 tool schema와 안전 마진 때문에 더 작다.

**CUD Operations**
: Create, Update, Delete 작업. HOTL 거버넌스에서 High Risk로 분류되어 Hard Interrupt가 필요한 작업.

**Degraded Mode (부분 장애 모드)**
: MCP 서버 일부가 실패해도 나머지가 정상 운영되는 모드. 실패 서버는 startup/handshake/config/partial로 분류되며, 가용한 서버의 도구만 등록하여 계속 작동한다. 마이크로서비스의 circuit breaker 패턴과 동일한 원리.

**DeepSeek-V4**
: DeepSeek의 최신 V4 오픈웨이트 계열. `DeepSeek-V4-Pro`는 1.6T total / 49B active MoE, `DeepSeek-V4-Flash`는 284B total / 13B active MoE로 공개되어 있으며 1M context, long-context reasoning, coding, agentic task를 강조한다.

**Disaggregated Prefill**
: LLM serving에서 prefill과 decode 단계를 별도 worker/GPU로 분리하는 아키텍처. 긴 입력과 짧은 응답 요청이 섞인 production workload에서 queue blocking을 줄이는 데 사용한다.

**DGX H100**
: NVIDIA의 엔터프라이즈급 AI 서버. 제주한라대학교 AI 실습실에 설치된 모델. H100 GPU 8개 탑재.

**Elicitation (MCP 사용자 확인 요청)**
: MCP에서 서버가 클라이언트를 통해 사용자에게 직접 확인이나 입력을 요청하는 역방향 훅. Human-in-the-loop를 프로토콜 수준에서 구현한다. 서버가 민감한 작업 전 사용자 동의를 얻거나 추가 정보를 수집할 때 사용한다.

**Garbage Collection (가비지 컬렉션)**
: Ralph 루프에서 에이전트가 생성한 잘못된 코드를 `git checkout .`으로 완전히 제거하고 저장소를 클린 상태로 복원하는 과정.

**Governance-as-Code**
: 거버넌스 정책(누가 어떤 행동을 할 수 있는가)을 소프트웨어 코드로 구현하여 자동으로 강제하는 접근법.

**Hook (훅)**
: Claude Code에서 도구 호출, 세션 이벤트 등에 자동으로 실행되는 핸들러. 4종 타입(command/http/prompt/agent)이 있다. CLAUDE.md가 advisory(~80% 준수)인 반면, Hook은 deterministic(100% 시행)이다. settings.json에 정의.

**Hard Interrupt**
: 에이전트가 High Risk 작업(CUD)을 시도할 때 반드시 인간의 명시적 승인을 받아야 하는 강제 정지 메커니즘.

**Harness (하네스)**
: Ralph 루프를 둘러싸는 결정론적 외부 시스템. 백프레셔, 가비지 컬렉션, 상태 추적 등을 포함. 에이전트의 비결정적 출력을 통제한다.

**Harness Engineering (하네스 엔지니어링)**
: 비결정적 AI 에이전트를 제어하는 결정론적 외부 시스템을 설계하는 공학 분야. 더 강력한 모델보다 더 강력한 하네스를 만드는 것을 목표로 한다.

**HIC (Human-in-Command)**
: AI 시스템의 최상위 거버넌스 계층. 인간이 전체 전략과 경계 조건을 설정하며 AI는 전술적 실행을 담당.

**HITL (Human-in-the-Loop)**
: AI가 행동하기 전 반드시 인간의 승인이 필요한 아키텍처. 안전하지만 느리고 확장성이 낮음.

**HOTL (Human-on-the-Loop)**
: AI가 자율적으로 실행하고 인간은 텔레메트리를 모니터링하며 필요시 개입하는 아키텍처. 속도와 확장성이 높음.

**Instructional Tuning (인스트럭션 튜닝)**
: 모델 가중치를 재훈련하지 않고 PROMPT.md에 구체적 지시를 추가하여 에이전트의 반복 오류를 교정하는 방법.

**LLM-as-Judge**
: LLM을 사용하여 다른 LLM의 출력 품질을 자동으로 평가하는 방법론. 인간 평가자를 부분적으로 대체.

**MCP (Model Context Protocol)**
: 에이전트와 외부 도구(파일시스템, Git, 데이터베이스 등)를 연결하는 표준화된 프로토콜. Anthropic이 개발.

**McpInject**
: SANDWORM_MODE 공격의 핵심 모듈. 악성 MCP 서버를 설치하고 무해한 이름의 도구 3종을 등록한 뒤, 도구 설명(description)에 프롬프트 인젝션을 내장하여 AI 어시스턴트가 .ssh/id_rsa, .aws/credentials 등을 자율적으로 수집하도록 조종한다. 메모리 취약점이 아닌 AI의 언어 이해력을 악용하는 의미론적 공격.

**MIG (Multi-Instance GPU)**
: NVIDIA GPU를 독립적인 인스턴스로 분할하는 기술. H100에서 최대 7개 인스턴스 생성 가능. 하드웨어 수준 격리 제공.

**MiniMax-M2.7**
: MiniMax의 최신 229B급 agentic 모델 후보. 코딩, 검색, office work, 장기 agentic workflow를 강조하며 vendor benchmark claim은 강의 Lab에서 동일 하네스로 재검증한다.

**MoE (Mixture of Experts)**
: LLM 아키텍처 중 하나. 전체 파라미터 중 일부만 활성화하여 추론 효율성을 높임. Qwen3-Coder-Next, DeepSeek-V4, MiniMax-M2.7 등에 적용.

**OBO (On-Behalf-Of)**
: MCP 서버가 서비스 계정 대신 위임된 사용자/에이전트 ID로 작업하는 인증 패턴. OAuth 2.1 토큰 교환을 통해 "누구를 대신하여" 작업하는지 명시하여, 에이전트 환경에서 발생하는 책임 단절(accountability breakdown) 문제를 해결한다.

**Initializer Pattern (이니셜라이저 패턴)**
: Anthropic 공식 하네스 가이드의 2-phase 상태 관리 패턴. Phase 1(Initializer)에서 JSON feature list, claude-progress.txt, init.sh를 생성하고, Phase 2(Coding Agent)에서 점진적으로 작업을 수행한다. feature list를 JSON으로 쓰는 이유: 모델의 scope creep 방지.

**Permission Mode (퍼미션 모드)**
: Claude Code의 3단계 권한 모드. ReadOnly(읽기만), WorkspaceWrite(워크스페이스 내 쓰기, 기본값), DangerFullAccess(전체 접근). 4중 보안 레이어(도구 은닉 → 도구별 오버라이드 → CLI 프리셋 → Workspace boundary)와 결합하여 에이전트 행동 범위를 결정론적으로 제어한다.

**Prompt Caching (프롬프트 캐싱)**
: 에이전트의 반복되는 정적 부분(시스템 프롬프트, 도구 스키마, CLAUDE.md)을 캐시하여 비용을 절감하는 기법. 캐시 읽기는 기본 가격의 0.1x(90% 절감). Ralph 루프의 fresh context 전략은 매 세션 캐시 재생성이 필요하여 비용이 증가하는 트레이드오프가 있다.

**Query Engine (쿼리 엔진)**
: Claude Code의 대화 루프 엔진. 사용자 메시지 수신 → 시스템 프롬프트 조립 → API 스트리밍 호출 → 도구 실행 → 결과 추가를 max_turns(기본 8)까지 반복한다. 매 턴마다 TurnResult(input, response, tools, permissions, tokens, termination reason)를 캡처한다.

**Qwen3-Coder**
: Alibaba의 코딩 특화 MoE 모델 계열. 최신 수업 기준 대표 모델은 `Qwen3-Coder-Next`이며 80B total / 3B active, 256K context, Apache 2.0 라이선스를 제공한다.

**GLM-5.1**
: Z.ai/Zhipu 계열의 최신 공개 GLM 모델. agentic engineering, coding, terminal task, tool use를 강조하며 최신 GLM 비교 기준으로 사용한다.

**SGLang**
: vLLM과 함께 대표적인 오픈소스 LLM 추론 프레임워크. RadixAttention 기반 KV 캐시 재사용으로 높은 처리량 제공.

**PagedAttention**
: vLLM의 핵심 기술. OS의 가상 메모리 페이징을 KV 캐시에 적용하여 메모리 낭비를 4% 이하로 줄임.

**Speculative Decoding**
: 작은 draft model, n-gram speculation, 또는 multi-token prediction으로 후보 토큰을 먼저 생성하고 큰 모델이 검증하는 추론 가속 기법. 주 목적은 출력 품질을 유지하면서 latency를 줄이는 것이다.

**Agentmaxxing (에이전트맥싱)**
: 다중 AI 코딩 도구(Claude Code, Codex CLI, Gemini CLI, Cursor 등)를 한 레포에서 동시에 병렬 실행하는 전략. 2026년 초부터 확산. 담당 영역(모듈/파일)을 명확히 분리하지 않으면 머지 충돌이 N² 규모로 폭발한다.

**AI 코딩 CLI (AI Coding CLI)**
: 터미널에서 AI 에이전트를 실행하는 명령줄 도구의 총칭. Claude Code, Gemini CLI, Codex CLI, OpenCode 등이 해당. 헤드리스 모드로 Ralph 루프에서 자동화 가능.

**RLM (Recursive Language Model, 재귀적 언어 모델)**
: 모델이 자기 자신을 재귀 호출하여 장문 문서를 처리하는 기법. 긴 프롬프트를 Python REPL 변수에 올리고, 모델이 코드를 짜서 필요한 부분만 골라 자기 자신을 재귀 호출한다. context window를 키우는 대신 모델이 맥락 탐색 전략을 스스로 결정한다.

**Ralph Loop (Ralph 루프)**
: Geoffrey Huntley가 2025년 대중화한 에이전틱 개발 방법론. `while :; do cat PROMPT.md | <ai-coding-cli>; done` 형태의 단순 지속 루프. `<ai-coding-cli>`에는 `claude`, `gemini`, `codex` 등을 사용할 수 있다.

**/loop (Claude Code Loop)**
: Claude Code의 공식 스케줄 기반 자율 에이전트 루프 명령. `claude /loop "<지시>" --every <간격> --for <기간>` 형태로 실행. 매 반복마다 git worktree를 생성하여 격리 실행하고, CLAUDE.md를 다시 읽어 최신 컨텍스트를 반영한다. 최대 3일 만료 — 잊혀진 에이전트의 컨텍스트 드리프트를 방지하기 위한 의도적 설계. Ralph 루프의 범용 패턴을 Claude Code 전용으로 제품화한 것.

**Ralphthon**
: Ralph 루프 방법론을 중심으로 한 해커톤 형식의 집중 개발 이벤트. 이 강의 캡스톤 프로젝트의 이름.

**Sampling (MCP 서버 주도 추론 요청)**
: MCP에서 서버가 클라이언트의 LLM에 추론을 요청하는 역방향 훅. 서버는 자체 모델 API 키 없이도 호스트의 LLM 지능을 활용할 수 있다. Human-on-the-Loop 원칙에 따라 사용자 승인이 필수이며, 클라이언트가 모델 선택과 토큰 제한을 제어한다.

**Sign Fatigue (간판 피로)**
: instruction 파일(PROMPT.md, CLAUDE.md)에 제약이 과다해져 에이전트가 핵심 지시를 놓치는 현상. Huntley의 Sign 메타포 확장 — 놀이터에 30개 경고판이 붙으면 아무도 읽지 않는 것과 같다. 인스트럭션 튜닝은 추가뿐 아니라 정리와 우선순위 재조정을 포함한다.

**SDLC (Software Development Lifecycle)**
: 소프트웨어 개발 생애주기. 요구사항 분석 → 설계 → 구현 → 테스트 → 배포 → 유지보수.

**Software 3.0 (소프트웨어 3.0)**
: Andrej Karpathy가 제안한 개념. 프로그래머가 코드를 직접 작성하는 대신 AI 에이전트를 지휘(conduct)하는 패러다임. Software 1.0(수동 코딩), Software 2.0(신경망 학습), Software 3.0(에이전트 오케스트레이션)으로 진화한다.

**Task Packet (태스크 패킷)**
: 에이전트에게 자연어 프롬프트 대신 구조화된 형식으로 작업을 전달하는 명세. objective(목표), scope(범위: Workspace/Module/SingleFile), branch_policy(브랜치 전략), acceptance_tests(수락 기준), escalation_policy(에스컬레이션 정책) 등을 포함한다. 로깅, 재시도, 에이전트 간 계약 명확화에 유리.

**TBAC (Task-Based Access Control)**
: 에이전트의 작업 목적 단위로 도구 접근을 제어하는 패러다임. Tasks → Tools → Transactions 3계층으로 구성된다. RBAC/ABAC의 "누가"보다 "어떤 작업"이 중요한 에이전트 환경에 적합하다. 변수 치환 엔진이 `mcp.*`, `jwt.*` 네임스페이스를 지원하여 동적 정책 평가가 가능하다.

**Test-Time Compute Scaling (추론 시점 연산 확장)**
: 모델 크기를 키우지 않고 추론 시점에 연산을 더 투입하여 성능을 높이는 전략. OpenAI o1이 검증. Ralph Loop, RLM, autoresearch는 모두 이 원리의 구체적 실현으로, 같은 모델을 반복 호출하되 결정론적 검증으로 결과를 필터링한다.

**T2 Scaling Laws (T2 스케일링 법칙)**
: 추론(inference) 비용을 고려한 최적 사전학습 전략. 기존 Chinchilla(2022)가 학습 연산만 최적화한 것과 달리, T2(arxiv 2604.01411, 2026)는 추론 비용까지 포함하여 최적점을 재계산한다. 결론: 추론 비용을 고려하면 Chinchilla 최적보다 overtrain이 유리 — 작은 모델을 더 오래 학습시키면 추론 시 토큰당 비용이 낮아진다.

**Telemetry (텔레메트리)**
: 실행 중인 시스템의 성능 지표(메트릭), 로그, 추적(트레이스) 데이터를 실시간으로 수집하는 기술.

**Tool Surface (도구 표면)**
: 에이전트가 접근 가능한 도구의 전체 집합. Claude Code에서는 Base(40개 빌트인) + Plugin(사용자 설치) + Runtime(MCP 서버 동적 등록) 3레이어로 구성된다. 상위 레이어가 하위와 이름 충돌 시 등록이 거부되며, simple mode에서는 3개로 축소된다.

**ToolSpec**
: Claude Code에서 도구 하나를 정의하는 단위. 이름(name), 설명(description), JSON input schema, 필요 퍼미션 레벨(required_permission)을 포함한다. 시스템 프롬프트에 도구 목록으로 삽입되어 LLM이 어떤 도구를 쓸 수 있는지 인식하게 한다.

**Triple Gate Pattern (3중 게이트 패턴)**
: AI Gateway → MCP Gateway → API Gateway의 3중 방어 아키텍처. 1차 AI 게이트웨이가 프롬프트 인젝션/PII를 필터링하고, 2차 MCP 게이트웨이가 TBAC 인가를 수행하며, 3차 API 게이트웨이가 rate limiting을 적용한다. 각 게이트가 독립적 관심사를 담당하여 단일 장애점을 방지한다.

**vLLM**
: 오픈소스 고처리량 LLM 추론 라이브러리. PagedAttention, automatic prefix caching, speculative decoding, structured outputs, OpenAI-compatible serving, 관측성 예제를 제공한다.

**Workspace Boundary (워크스페이스 경계)**
: 파일 쓰기가 허용되는 디렉토리 경계. Claude Code의 Permission Enforcer가 symlink escape, `../` 탈출, canonical path 비교로 경계를 검증한다. WorkspaceWrite 모드에서 이 경계 밖 쓰기를 시도하면 사유와 함께 거부된다.
