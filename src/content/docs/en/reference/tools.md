---
title: Development Tools
description: Core tools used in the AI Systems 2026 course, with guides and usage examples
---

## Core Tools

### Claude Code (Anthropic)

The reference commercial tool for agentic coding. Terminal integration, MCP support, GitHub integration.

```bash
# Install
pnpm add -g @anthropic-ai/claude-code

# Basic usage
claude "Build a Python calculator"

# Include file context
claude --file=PROMPT.md

# Headless mode (for Ralph Loop)
cat PROMPT.md | claude --headless
```

```bash
# /loop — schedule-based autonomous agent loop
claude /loop "find and fix failing tests" --every 2h --for 3d

# Check loop status / stop
claude /loop --status
claude /loop --stop
```

**Key features**:
- MCP server integration (`~/.claude/settings.json`)
- `CLAUDE.md` per-project instruction file
- `/loop` schedule-based autonomous loop (git worktree isolation, up to 3 days)
- Multi-file editing
- GitHub Actions integration

**Advanced features**:

#### Planning & Control

- **Plan Mode** (`Shift+Tab`) — Draft a plan before writing code. Once confirmed, auto-executes the plan.
  ```bash
  # In an interactive session, press Shift+Tab to enter Plan Mode
  # Draft plan → confirm → auto-execute
  ```
- **Effort Levels** — Adjust reasoning depth. Use low effort for simple tasks to save cost; high effort for complex design work.
  ```bash
  claude --effort low "What is the return type of this function?"
  claude --effort high "Refactor this module to be async"
  ```
- **Output Styles** — Cognitive mode presets: Explanatory, Learning, Concise, etc.
  ```bash
  claude --output-style concise "Analyze test failure cause"
  claude --output-style explanatory "Explain the MCP protocol"
  ```

#### Extension System

- **Custom Agents** — Define specialized agents in `.claude/agents/*.md`. Declaratively set role, allowed tools, and permissions.
  ```bash
  # After defining a role in .claude/agents/qa-reviewer.md:
  claude --agent qa-reviewer "Review this PR"
  ```
  ```json
  // Set default agent in settings.json
  { "defaultAgent": "qa-reviewer" }
  ```
- **Skills** — Installable `.md` skill files. Place in `~/.claude/skills/` and load within a session.
  ```bash
  # Load a skill
  claude /skills refactor-guide
  ```
- **Hooks** — Shell commands triggered by events (tool calls, etc.). Configured in settings.json.
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

#### Isolation & Safety

- **Sandboxing** (`/sandbox`) — Isolate BashTool file and network access. Limits blast radius of agent mistakes.
  ```bash
  # Activate sandbox mode
  claude --sandbox
  ```
- **Worktree Native** (`--worktree`) — Git worktree-based isolated sessions. Supports tmux integration for background execution.
  ```bash
  # Start an isolated worktree session
  claude --worktree feature-auth
  # Run in background via tmux
  claude --worktree feature-auth --tmux
  ```

#### Parallel Execution

- **Parallel Sessions** — Run multiple Claude Code instances simultaneously. Each session maintains an independent context.
  ```bash
  # Terminal 1: frontend work
  claude --worktree frontend "Implement React components"
  # Terminal 2: backend work
  claude --worktree backend "Implement API endpoints"
  ```
- **/batch** — Interactive planning followed by worktree-isolated parallel execution. Each agent tests and opens an individual PR.
  ```bash
  claude /batch "Migrate logging in src/ to the new structured logger"
  ```
- **/simplify** — Parallel-agent code review across reuse, quality, and efficiency dimensions.
  ```bash
  claude /simplify
  ```

> For detailed explanations and hands-on examples, see [Week 4](/en/weeks/week-04/) (loops/worktree), [Week 6](/en/weeks/week-06/) (instruction tuning), and [Week 7](/en/weeks/week-07/) (multi-agent design).

---

### Gemini CLI (Google)

Google's AI coding CLI with a free tier. 1M token context window, MCP support.

```bash
# Install
pnpm add -g @google/gemini-cli

# Interactive mode
gemini

# Pipe mode (headless)
cat PROMPT.md | gemini
```

**Key features**:
- MCP server integration (`~/.gemini/settings.json`)
- `GEMINI.md` per-project instruction file
- Free tier: 1,000 req/day
- 1M token context window

---

### Codex CLI (OpenAI)

OpenAI's terminal-based coding agent. Built-in sandbox for safe automated execution.

```bash
# Install
pnpm add -g @openai/codex

# Basic usage
codex "Build a Python calculator"

# Auto-approval mode (for Ralph Loop)
codex --approval-mode full-auto "$(cat PROMPT.md)"
```

**Key features**:
- Built-in sandbox (safest automated execution)
- `AGENTS.md` per-project instruction file
- No MCP support
- Requires ChatGPT Plus or API key

---

### OpenCode

Open-source TUI-based AI coding tool. Supports multiple model backends including local models.

```bash
# Install (macOS)
brew install opencode

# TUI mode
opencode

# API server mode
opencode serve
```

**Key features**:
- TUI (Terminal UI) interface
- Multiple backends: OpenAI, Anthropic, local models (Ollama), and more
- Free when using local models (no API cost)
- Limited MCP support

> For a detailed comparison of tools, see the [AI Coding Tool Selection Guide](/en/reference/tool-selection).

---

### vLLM

High-throughput LLM inference server with an OpenAI-compatible API.

```bash
# Install
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
  --model deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct \
  --port 8000

# Client usage (OpenAI-compatible)
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="token")
```

---

### Model Context Protocol (MCP)

The standard protocol for connecting agents to external tools.

**Key MCP servers**:

| Server | Function | Install |
|--------|----------|---------|
| `@modelcontextprotocol/server-filesystem` | File read/write | `npx` |
| `mcp-server-git` | Git operations | `uvx` |
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

The standard for collecting telemetry from agent systems.

```python
pip install opentelemetry-sdk opentelemetry-exporter-prometheus
```

---

### Open-Source Coding LLMs

Major coding models that can be deployed locally. Served via vLLM or SGLang with an OpenAI-compatible API.

| Model | Parameters | Active | Context | HuggingFace |
|-------|-----------|--------|---------|-------------|
| **Qwen3-Coder** | 235B (MoE) | 22B | 128K | `Qwen/Qwen3-Coder-32B-Instruct` |
| **DeepSeek V3** | 685B (MoE) | 37B | 128K | `deepseek-ai/DeepSeek-V3` |
| **GLM-4.7** | ~32B (Dense) | Full | 128K | `THUDM/glm-4-9b-chat` |
| **MiniMax M2.1** | 230B (MoE) | 10B | 128K | `MiniMax/MiniMax-M2.1` |
| **DeepSeek-Coder-V2** | 236B (MoE) | 21B | 128K | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` |
| **Qwen3 14B/8B** | 14B/8B | Full | 128K | `Qwen/Qwen3-14B`, `Qwen/Qwen3-8B` |

> For detailed per-model comparisons and hardware requirements, see [Week 10 lecture](/weeks/week-10).

---

### Other Useful Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `uv` | Python package manager (pip alternative) | `pip install uv` |
| `Ruff` | Python linter/formatter | `pip install ruff` |
| `pytest` | Python test framework | `pip install pytest` |
| `mypy` | Python type checker | `pip install mypy` |
| `httpx` | Async HTTP client | `pip install httpx` |
