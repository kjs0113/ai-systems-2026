---
title: Project Proposal Writing Guide
description: Guidelines and template for the Week 8 project proposal presentation
---

## Overview

The capstone project proposal is the primary deliverable for the **Week 8 (2026-04-21)** presentation, which replaces the midterm exam. This guide provides writing guidelines and a template to ensure consistency and specificity across proposals.

**Submission location**: `capstone/projects/[student-id]/proposal.md` (via GitHub PR)
**Deadline**: **2026-04-20 23:59** (the day before Week 8 class)
**Length**: 4–6 pages (about 2,000–3,000 words)
**Presentation time**: 15 minutes talk + 5 minutes Q&A

## Grading (Midterm Project, 20%)

| Criterion | Points | Description |
|-----------|--------|-------------|
| Clarity of problem definition | 4 | Why this problem, why an agentic approach |
| Specificity of system design | 6 | Agent roles, artifacts, pipeline structure |
| Application of course techniques | 4 | Explicit links to Weeks 1–7 content |
| Feasibility | 3 | Achievable within Weeks 13–16 |
| Presentation quality | 3 | Clear delivery, Q&A responsiveness |

---

## Writing Principles

1. **Specific > general**: "Use an LLM to improve code" ❌ → "Use GPT-5.1 Sonnet to analyze pytest failure logs and generate fix patches" ✓
2. **Numeric success criteria**: "Works well" ❌ → "Test coverage ≥ 80%, average loop count ≤ 5" ✓
3. **Explicitly map course techniques**: Name the technique and the week (e.g., "Week 5 Context Rot prevention", "Week 6 CLAUDE.md tuning")
4. **Be honest about risks**: Don't hide weak points — state them with mitigation strategies
5. **At least one diagram**: Visualize the agent pipeline or data flow

---

## Proposal Template

Copy this template to `capstone/projects/[student-id]/proposal.md` and fill it in.

```markdown
---
title: "[Project Title]"
student_id: "2023xxxx"
student_name: "Hong Gildong"
submitted: "2026-04-20"
---

# [Project Title]

**One-line summary**: (What problem does your agent system solve, in one sentence?)

**Student ID / Name**: 2023xxxx / Hong Gildong
**GitHub Repository**: https://github.com/...

---

## 1. Problem Definition

### 1.1 Current State
(Describe the current inefficiency — manual work, repetitive tasks)

### 1.2 Why an Agentic Approach?
(Argue why a simple script or a single LLM call is not enough.
Reference Week 1 HITL/HOTL and Week 4 loop paradigm.)

### 1.3 Target User / Usage Context
(Who uses this system, when, and how?)

---

## 2. Proposed System Design

### 2.1 Agent Roster

| Agent | Role | Input Artifact | Output Artifact | Model |
|-------|------|----------------|-----------------|-------|
| Planner | Requirement parsing | user prompt | spec.md | Opus |
| Coder | Implementation | spec.md, code | diff, PR | Sonnet |
| QA | Verification | PR, tests | review.md | Sonnet |

### 2.2 Pipeline Architecture

(Show the pipeline as a diagram or ASCII art)

```
User Input → Planner → Coder (Ralph Loop) → QA Gate → Human Approval → Deploy
```

### 2.3 MCP Tools / External Integrations

- GitHub MCP — PR creation/review
- Filesystem MCP — local file edits
- (add more)

### 2.4 State Tracking / Handoffs

(Describe the files/JSON structures used for agent-to-agent handoff — see Weeks 5/7)

---

## 3. Tech Stack

| Category | Choice | Rationale |
|----------|--------|-----------|
| LLM | current frontier reasoning model (Planner), cost-efficient coding model (Coder) | cost/quality balance (Weeks 5 and 10) |
| Framework | Claude Code + Custom Agents | .claude/agents/ directory |
| Language | Python 3.12 | Course standard |
| Testing | pytest | Easy CI integration |
| Deployment | GitHub Actions | Free and simple |

---

## 4. Course Technique Mapping

Name the techniques from each week you will **actually apply**. Not "I've heard of it" — "I am using it this way in this project."

| Week | Technique | How It Applies |
|------|-----------|----------------|
| Week 1 | HOTL governance | Human approval gate at deploy stage |
| Week 3 | MCP servers | Wrap GitHub API calls as an MCP server |
| Week 4 | Ralph Loop | Coder agent's test-fail-retry loop |
| Week 5 | Context Rot prevention | fix_plan.md + claude-progress.txt state files |
| Week 6 | CLAUDE.md tuning | Project-specific constraints (e.g., "never hardcode secrets") |
| Week 7 | Gated pipeline | 3-retry limit at QA failure, then human escalation |

---

## 5. Development Schedule

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| Week 13 | Planner + Coder skeleton | design.md, initial code |
| Week 14 | Ralph Loop integration, QA agent | Working pipeline demo |
| Week 15 | System integration, E2E testing | report.md, links.md (slides URL) |
| Week 16 | Final presentation, demo | links.md (demo video URL), final submission |

---

## 6. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Functional accuracy | ≥ 80% | Test case pass rate |
| Average loop count | ≤ 5 | Log analysis |
| Token cost per task | ≤ $0.50 | API billing logs |
| E2E response time | ≤ 2 min | Benchmark |

---

## 7. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| LLM hallucinates non-existent API calls | High | Enforce tests at QA gate (Week 7) |
| Token cost blow-up | Medium | Model tier routing (Haiku explore, Sonnet implement) |
| External API downtime | Low | Prepare mock fallback path |

---

## 8. References

- (Week links, papers, blog posts, etc.)
```

---

## Writing Tips

### Common Mistakes (avoid these)

- **X** "A system that automatically generates code with AI" — too abstract
- **O** "An agent that takes pytest failure logs as input and produces fix commits" — concrete I/O

- **X** "Uses Claude"
- **O** "Planner uses a current frontier reasoning model (`--effort high`), Coder uses a cost-efficient coding model (`--effort medium`)"

- **X** "Will produce good results"
- **O** "Test coverage ≥ 80%, converges in ≤ 1.5 fixes on average"

### It Must Be an Agentic System

Your project must have **at least 3** of the following to qualify as a capstone:

- [ ] **Agent iterates in a loop** (Ralph Loop)
- [ ] **Multi-stage pipeline** (Planner → Coder → QA, etc.)
- [ ] **Tool use** (file system, shell, external APIs)
- [ ] **Autonomous decisions** (no human intervention at every step)
- [ ] **State tracking files** for context management
- [ ] **Validation gates** (tests, QA, human approval)

### Presentation Structure (15 minutes)

| Time | Section |
|------|---------|
| 2 min | Problem definition (§1) |
| 5 min | System design (§2) — diagram-centric |
| 3 min | Course technique mapping (§4) — why these weeks matter |
| 2 min | Schedule and success criteria (§5–6) |
| 3 min | Risks and mitigations (§7) |

---

## FAQ

**Q. I haven't picked a topic yet.**
A. See [Week 13 project ideas](/en/weeks/week-13#recommended-project-ideas). Five example topics are listed there.

**Q. Can I extend an existing open-source tool (e.g., sdlc-toolkit)?**
A. Yes, but you must clearly describe **what you added or changed**. Pure reuse does not count.

**Q. Can I use a local model (Ollama)?**
A. Yes. This connects with Weeks 10–11 on open-source model deployment.

**Q. Should my GitHub repo be public or private?**
A. Public is recommended (easier for peer evaluation). If private, invite the instructor and TA as collaborators.

---

## Related Pages

- [Capstone Overview](/en/capstone)
- [Project Registration](/en/capstone/teams)
- [Rubric](/en/capstone/rubric)
- [Week 8: Project Proposal Presentation](/en/weeks/week-08)
