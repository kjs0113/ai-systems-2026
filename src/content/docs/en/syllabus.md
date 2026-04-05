---
title: Course Syllabus
description: AI Systems 2026 — Agentic Workflows and Harness Engineering
lastUpdated: 2026-03-03
---

## Course Information

| Item | Details |
|------|---------|
| **Course Title** | AI Systems (Machine Learning Systems: Agentic Workflows and Harness Engineering) |
| **Course Code** | AI4001 |
| **Credits** | 3 credits (2 lecture + 1 lab) |
| **Target Students** | AI Department, 4th year |
| **Contact Hours** | 3 hours/week × 16 weeks |
| **Instructor** | Young Joon Lee (yj.lee@chu.ac.kr) |
| **Classroom** | AI Lab (DGX H100 Cluster) |
| **Course Site** | https://ai-systems-2026.halla.ai/ |

## Course Overview

The AI industry of 2025–2026 has decisively shifted from conversational models to **autonomous agentic systems**. This course is organized around two central themes: **harness engineering** — the discipline of controlling non-deterministic AI agents with deterministic systems — and the **Human-on-the-Loop (HOTL)** paradigm, in which humans take on strategic oversight rather than step-by-step approval.

Students will directly operate the NVIDIA DGX H100 server in the Jeju Halla University AI Lab (partitioned via MIG technology), gaining hands-on experience deploying and running open-source models such as **DeepSeek-Coder-V2** without relying on commercial APIs. The ultimate goal is to design an autonomous software development pipeline (multi-agent SDLC) and implement it in the capstone project **Ralphthon**.

## Learning Objectives

Upon completing this course, students will be able to:

1. Explain the differences among HITL, HOTL, and HIC governance architectures and implement them as Governance-as-Code
2. Design and implement harness engineering systems using the Ralph Loop methodology
3. Optimize long-running agent loops through context window management and instruction tuning
4. Build a multi-agent SDLC by connecting planner, coder, and QA agents via MCP
5. Deploy open-source LLMs in a DGX H100 + MIG + vLLM environment and measure their performance
6. Automatically evaluate the quality of agent systems using LLM-as-Judge and telemetry

## Weekly Schedule

### Phase 1: Foundations of Agentic Systems (Weeks 1–3)

| Week | Theory | Lab |
|------|--------|-----|
| [Week 1](/en/weeks/week-01/) | Course orientation, AI system paradigm shift, HITL vs HOTL | Dev environment setup, AI coding CLI installation (Lab 01) |
| [Week 2](/en/weeks/week-02/) | HOTL governance in depth, EU AI Act compliance, Governance-as-Code | Implementing the first agentic loop (Lab 02) |
| [Week 3](/en/weeks/week-03/) | MCP architecture deep dive, TBAC/governance gateway, MIG compute isolation | MCP server implementation and security verification (Lab 03) |

### Phase 2: Harness Engineering (Weeks 4–6)

| Week | Theory | Lab |
|------|--------|-----|
| [Week 4](/en/weeks/week-04/) | Loop paradigms — Test-time Compute Scaling, Ralph Loop/RLM/autoresearch | Ralph Loop implementation and cumulative learning (Lab 04) |
| [Week 5](/en/weeks/week-05/) | Context window management, preventing Context Rot, state tracking file design | Implementing a context management system (Lab 05) |
| [Week 6](/en/weeks/week-06/) | Instruction tuning, the "Sign" metaphor, designing permanent context payloads | PROMPT.md tuning practice (Lab 06) |

### Phase 3: Multi-Agent SDLC (Weeks 7–9)

| Week | Theory | Lab |
|------|--------|-----|
| [Week 7](/en/weeks/week-07/) | Agent role division, traditional SDLC vs agentic SDLC | Multi-agent pipeline design (Lab 07) |
| [Week 8](/en/weeks/week-08/) | Planner agent design, automated spec generation, codebase analysis | Planner agent implementation (Lab 08) |
| [Week 9](/en/weeks/week-09/) | QA agent, automated test pipeline, feedback loop | QA agent implementation (Lab 09) |

### Phase 4: Open-Source Models & MLOps (Weeks 10–12)

| Week | Theory | Lab |
|------|--------|-----|
| [Week 10](/en/weeks/week-10/) | DeepSeek-Coder-V2 architecture, open-source vs commercial API, tool ecosystem | vLLM deployment practice (Lab 10) |
| [Week 11](/en/weeks/week-11/) | vLLM high-throughput inference, CUDA optimization, MIG slice utilization | Building a high-throughput inference server |
| [Week 12](/en/weeks/week-12/) | Telemetry design, LLM-as-Judge evaluation framework, cost optimization | Telemetry & LLM-as-Judge (Labs 11 & 12) |

### Phase 5: Capstone Ralphthon (Weeks 13–16)

| Week | Content |
|------|---------|
| [Week 13](/en/weeks/week-13/) | Team formation, project topic selection, system architecture design |
| [Week 14](/en/weeks/week-14/) | Ralphthon execution — harness implementation, agent integration, iterative improvement |
| [Week 15](/en/weeks/week-15/) | System integration, automated testing, presentation preparation |
| [Week 16](/en/weeks/week-16/) | Final presentation and demo, peer evaluation, course wrap-up |

## Grading

| Item | Weight | Description |
|------|--------|-------------|
| Lab Assignments (Lab 01–12) | 40% | Individual submission via GitHub PR |
| Midterm Project | 20% | Integrated system covering Phases 1–3 |
| Capstone Ralphthon | 30% | Team project with final presentation |
| Contribution & Participation | 10% | GitHub PR contributions, class discussion |

## Textbooks and References

### Primary References
- Huntley, G. (2025). *The Ralph Loop: Deterministic Agentic Engineering*
- Anthropic. (2026). *Claude Code Documentation*
- NVIDIA. (2025). *DGX H100 MIG Configuration Guide*

### Additional References
- Karpathy, A. (2025). *autoresearch: Automated ML Research*
- Zhang, A. et al. (2025). *Recursive LM: Language Models that Call Themselves*
- Snell, C. et al. (2024). *Scaling LLM Test-Time Compute Optimally*
- Hong, S. et al. (2024). *MetaGPT: Meta Programming for Multi-Agent Collaborative Framework* (ICLR 2024)
- Qian, C. et al. (2024). *ChatDev: Communicative Agents for Software Development* (ACL 2024)
- Damani, S. et al. (2025). *Towards a Science of Scaling Agent Systems* (DeepMind + MIT)

### Online Resources
- [Model Context Protocol Official Docs](https://modelcontextprotocol.io)
- [vLLM Official Docs](https://docs.vllm.ai)
- [DeepSeek-Coder-V2 Paper](https://arxiv.org/abs/2406.11931)
- [Gemini CLI Docs](https://github.com/google-gemini/gemini-cli) — Google's AI coding CLI
- [Codex CLI Docs](https://github.com/openai/codex) — OpenAI's terminal coding agent
- [A2A Protocol Specification](https://google.github.io/A2A/) — Google's Agent-to-Agent communication standard
- [SWE-Bench](https://www.swebench.com/) — Agent coding benchmark

## Prerequisites

- Python 3.10+ programming proficiency
- Basic Git/GitHub usage
- Linux command-line fundamentals
- Machine learning basics (prerequisite courses: AI Fundamentals, Deep Learning)

## Contact

For course-related inquiries, please reach out via GitHub Issue or email (yj.lee@chu.ac.kr).
If you find errors in course materials, please report them via [GitHub Issue](https://github.com/halla-ai/ai-systems-2026/issues).
