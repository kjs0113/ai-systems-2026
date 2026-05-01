---
title: 개발 도구
description: AI 시스템 2026 강의에서 사용하는 핵심 도구 목록과 가이드
---

## 핵심 도구

### Claude Code (Anthropic)

에이전틱 코딩의 기준 상용 도구. 터미널 통합, MCP 지원, GitHub 연동.

```bash
# 설치
pnpm add -g @anthropic-ai/claude-code

# 기본 사용
claude "Python 계산기를 만들어줘"

# 파일 컨텍스트 포함
claude --file=PROMPT.md

# 헤드리스 모드 (Ralph 루프용)
cat PROMPT.md | claude --headless
```

```bash
# /loop — 스케줄 기반 자율 에이전트 루프
claude /loop "failing tests를 찾아 수정" --every 2h --for 3d

# 루프 상태 확인 / 중지
claude /loop --status
claude /loop --stop
```

**주요 기능**:
- MCP 서버 통합 (`~/.claude/settings.json`)
- `CLAUDE.md` 프로젝트별 지침 파일
- `/loop` 스케줄 기반 자율 루프 (git worktree 격리, 최대 3일)
- 멀티파일 편집
- GitHub Actions 통합

**고급 기능**:

#### 계획 및 제어

- **Plan Mode** (`Shift+Tab`) — 코드 작성 전 계획을 먼저 수립. 계획 확정 후 자동 실행으로 전환.
  ```bash
  # 대화형 세션에서 Shift+Tab으로 Plan Mode 진입
  # 계획 수립 → 확인 → 자동 실행
  ```
- **Effort Levels** — 추론 깊이 조절. 단순 작업에는 낮은 effort로 비용 절감, 복잡한 설계에는 높은 effort 사용.
  ```bash
  claude --effort low "이 함수의 반환 타입을 알려줘"
  claude --effort high "이 모듈을 비동기로 리팩터링해줘"
  ```
- **Output Styles** — 인지 모드 프리셋. 설명형(Explanatory), 학습형(Learning), 간결형(Concise) 등.
  ```bash
  claude --output-style concise "테스트 실패 원인 분석"
  claude --output-style explanatory "MCP 프로토콜 설명해줘"
  ```

#### 확장 시스템

- **Custom Agents** — `.claude/agents/*.md` 파일로 전문화된 에이전트 정의. 역할, 허용 도구, 권한을 선언적으로 설정.
  ```bash
  # .claude/agents/qa-reviewer.md 에 역할 정의 후:
  claude --agent qa-reviewer "이 PR을 리뷰해줘"
  ```
  ```json
  // settings.json에서 기본 에이전트 지정
  { "defaultAgent": "qa-reviewer" }
  ```
- **Skills** — 설치 가능한 `.md` 스킬 파일. `~/.claude/skills/`에 배치하고 세션 내에서 로드.
  ```bash
  # 스킬 로드
  claude /skills refactor-guide
  ```
- **Hooks** — 도구 호출 등 이벤트에 트리거되는 셸 명령. `settings.json`에서 설정.
  ```json
  // ~/.claude/settings.json
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "command": "echo '$(date): Bash called' >> ~/.claude/audit.log"
        }
      ]
    }
  }
  ```

#### 격리 및 안전

- **Sandboxing** (`/sandbox`) — BashTool의 파일 및 네트워크 접근을 격리. 에이전트 실수의 피해 범위를 제한.
  ```bash
  # 세션 내에서 샌드박스 모드 활성화
  claude --sandbox
  ```
- **Worktree Native** (`--worktree`) — git worktree 기반 격리 세션. tmux 통합으로 백그라운드 실행 가능.
  ```bash
  # 격리된 worktree 세션 시작
  claude --worktree feature-auth
  # tmux 세션으로 백그라운드 실행
  claude --worktree feature-auth --tmux
  ```

#### 병렬 실행

- **Parallel Sessions** — 여러 Claude Code 인스턴스를 동시 실행. 각 세션이 독립 컨텍스트를 유지.
  ```bash
  # 터미널 1: 프론트엔드 작업
  claude --worktree frontend "React 컴포넌트 구현"
  # 터미널 2: 백엔드 작업
  claude --worktree backend "API 엔드포인트 구현"
  ```
- **/batch** — 대화형 계획 수립 후 worktree 격리 기반 병렬 실행. 각 에이전트가 테스트 후 개별 PR 생성.
  ```bash
  claude /batch "src/의 로깅을 새 구조화 로거로 마이그레이션"
  ```
- **/simplify** — 병렬 에이전트로 코드 리뷰 수행. 재사용성, 품질, 효율성 관점을 동시 분석.
  ```bash
  claude /simplify
  ```

#### 내부 구조 — 도구 시스템과 퍼미션

Claude Code 내부에서 도구는 **3-Layer**로 합성된다:

| Layer | 소스 | 설명 |
|-------|------|------|
| **Base** | 컴파일 타임 정적 정의 | 40개 빌트인 도구 (Bash, Read, Write, Edit, Glob, Grep, Agent, Skill 등) |
| **Plugin** | 사용자 설치 확장 | hook 기반 lifecycle (pre/post_tool_use) |
| **Runtime** | MCP 서버 동적 등록 | `mcp__{server}__{tool}` 네이밍. 서버 연결 시 자동 등록 |

**도구 카테고리**: Shell(2) · File I/O(4) · Search(3) · Web(2) · Agent(2) · Task/Session(6)

**퍼미션 3모드**: ReadOnly(읽기만) → WorkspaceWrite(기본, 워크스페이스 내 쓰기) → DangerFullAccess(전체 접근). 도구마다 필요 퍼미션이 지정되어 있어, 모드에 따라 사용 가능한 도구가 자동으로 필터링된다.

→ 상세: [Claude Code 내부 구조](/reference/claude-code-internals)

> 기능별 상세 설명과 실습 예제는 [4주차](/weeks/week-04/) (루프/worktree), [6주차](/weeks/week-06/) (인스트럭션 튜닝), [7주차](/weeks/week-07/) (멀티에이전트 설계) 참조.

---

### Gemini CLI (Google)

무료 티어를 제공하는 Google의 AI 코딩 CLI. 1M 토큰 컨텍스트 창, MCP 지원.

```bash
# 설치
pnpm add -g @google/gemini-cli

# 대화형 실행
gemini

# 파이프 모드 (헤드리스)
cat PROMPT.md | gemini
```

**주요 기능**:
- MCP 서버 통합 (`~/.gemini/settings.json`)
- `GEMINI.md` 프로젝트별 지침 파일
- 무료 티어: 1,000 req/day
- 1M 토큰 컨텍스트 창

---

### Codex CLI (OpenAI)

OpenAI의 터미널 기반 코딩 에이전트. 내장 샌드박스로 안전한 자동 실행 가능.

```bash
# 설치
pnpm add -g @openai/codex

# 기본 사용
codex "Python 계산기를 만들어줘"

# 자동 승인 모드 (Ralph 루프용)
codex --approval-mode full-auto "$(cat PROMPT.md)"
```

**주요 기능**:
- 내장 샌드박스 (가장 안전한 자동 실행)
- `AGENTS.md` 프로젝트별 지침 파일
- MCP 미지원
- ChatGPT Plus 또는 API 키 필요

---

### OpenCode

오픈소스 TUI 기반 AI 코딩 도구. 다양한 모델 백엔드 지원, 로컬 모델 연동 가능.

```bash
# 설치 (macOS)
brew install opencode

# TUI 모드 실행
opencode

# API 서버 모드
opencode serve
```

**주요 기능**:
- TUI(Terminal UI) 인터페이스
- OpenAI, Anthropic, 로컬 모델(Ollama) 등 다양한 백엔드
- 무료 (로컬 모델 사용 시 API 비용 없음)
- MCP 제한적 지원

> 도구별 상세 비교는 [AI 코딩 도구 선택 가이드](/reference/tool-selection) 참조.

---

### vLLM

고처리량 LLM 추론 서버. OpenAI 호환 API 제공.

```bash
# 설치
pip install vllm

# 서버 시작
python -m vllm.entrypoints.openai.api_server \
  --model deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct \
  --port 8000

# 클라이언트 사용 (OpenAI 호환)
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="token")
```

---

### Model Context Protocol (MCP)

에이전트와 외부 도구를 연결하는 표준 프로토콜.

**주요 MCP 서버**:

| 서버 | 기능 | 설치 |
|------|------|------|
| `@modelcontextprotocol/server-filesystem` | 파일 읽기/쓰기 | `npx` |
| `mcp-server-git` | Git 작업 | `uvx` |
| `mcp-server-github` | GitHub API | `uvx` |
| `mcp-server-postgres` | PostgreSQL | `uvx` |

```json
// Claude Code: ~/.claude/settings.json
// Gemini CLI: ~/.gemini/settings.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/project"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."]
    }
  }
}
```

---

### OpenTelemetry

에이전트 시스템 텔레메트리 수집 표준.

```python
pip install opentelemetry-sdk opentelemetry-exporter-prometheus
```

---

### 오픈소스 코딩 LLM

로컬 배포 가능한 주요 코딩 모델. vLLM 또는 SGLang으로 서빙하여 OpenAI 호환 API로 사용.

| 모델 | 파라미터 | 활성 | 컨텍스트 | HuggingFace |
|------|---------|------|---------|-------------|
| **Qwen3-Coder** | 235B (MoE) | 22B | 128K | `Qwen/Qwen3-Coder-32B-Instruct` |
| **DeepSeek V3** | 685B (MoE) | 37B | 128K | `deepseek-ai/DeepSeek-V3` |
| **GLM-4.7** | ~32B (Dense) | 전체 | 128K | `THUDM/glm-4-9b-chat` |
| **MiniMax M2.1** | 230B (MoE) | 10B | 128K | `MiniMax/MiniMax-M2.1` |
| **DeepSeek-Coder-V2** | 236B (MoE) | 21B | 128K | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` |
| **Qwen3 14B/8B** | 14B/8B | 전체 | 128K | `Qwen/Qwen3-14B`, `Qwen/Qwen3-8B` |

> 모델별 상세 비교와 하드웨어 요건은 [10주차 강의](/weeks/week-10) 참조.

---

### 기타 유용한 도구

| 도구 | 용도 | 설치 |
|------|------|------|
| `uv` | Python 패키지 관리 (pip 대체) | `pip install uv` |
| `Ruff` | Python 린터/포매터 | `pip install ruff` |
| `pytest` | Python 테스트 프레임워크 | `pip install pytest` |
| `mypy` | Python 타입 체커 | `pip install mypy` |
| `httpx` | 비동기 HTTP 클라이언트 | `pip install httpx` |
