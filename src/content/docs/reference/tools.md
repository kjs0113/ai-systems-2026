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
