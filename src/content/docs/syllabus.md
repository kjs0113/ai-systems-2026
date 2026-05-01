---
title: 강의계획서
description: AI 시스템 2026 — 에이전틱 워크플로우와 하네스 엔지니어링
lastUpdated: 2026-04-06
---

## 강의 기본 정보

| 항목 | 내용 |
|------|------|
| **강의명** | AI 시스템 (Machine Learning Systems: Agentic Workflows and Harness Engineering) |
| **학수번호** | AI4001 |
| **학점** | 3학점 (이론 2 + 실습 1) |
| **대상** | 인공지능학과 4학년 |
| **강의 시수** | 주 3시간 × 16주 |
| **담당교수** | 이영준 (yj.lee@chu.ac.kr) |
| **강의실** | AI 실습실 (DGX H100 클러스터) |
| **강의 사이트** | https://ai-systems-2026.halla.ai/ |

## 강의 개요

2025–2026년의 AI 산업은 대화형 모델에서 **자율 에이전틱 시스템**으로 결정적으로 전환되었다. 이 강의는 비결정적 AI 에이전트를 결정론적 시스템으로 제어하는 **하네스 엔지니어링**과, 인간이 세부 실행이 아닌 전략적 감독 역할을 수행하는 **Human-on-the-Loop(HOTL)** 패러다임을 중심으로 구성된다.

학생들은 제주한라대학교 AI 실습실의 NVIDIA DGX H100 서버(MIG 기술로 파티셔닝)를 직접 운용하며, 상용 API에 의존하지 않고 **DeepSeek-Coder-V2** 등 오픈소스 모델을 배포·운영하는 전 과정을 실습한다. 최종 목표는 자율 소프트웨어 개발 파이프라인(멀티에이전트 SDLC)을 설계하고, 캡스톤 프로젝트 **Ralphthon**에서 이를 구현하는 것이다.

## 학습 목표

이 강의를 이수하면 다음을 할 수 있다:

1. HITL → HOTL → HIC 거버넌스 아키텍처의 차이를 설명하고 Governance-as-Code로 구현한다
2. Ralph 루프 방법론으로 하네스 엔지니어링 시스템을 설계·구현한다
3. 컨텍스트 창 관리와 인스트럭션 튜닝으로 장기 실행 에이전트 루프를 최적화한다
4. 플래너·코더·QA 에이전트를 MCP를 통해 연동한 멀티에이전트 SDLC를 구축한다
5. DGX H100 + MIG + vLLM 환경에서 오픈소스 LLM을 배포하고 성능을 측정한다
6. LLM-as-Judge와 텔레메트리로 에이전트 시스템의 품질을 자동 평가한다

## 주차별 계획

### Phase 1: 에이전틱 시스템 기초 (1–3주)

| 주차 | 이론 | 실습 |
|------|------|------|
| [1주](/weeks/week-01/) | 코스 오리엔테이션, AI 시스템 패러다임 전환, HITL vs HOTL 비교 | 개발 환경 설정, AI 코딩 CLI 도구 설치 (Lab 01) |
| [2주](/weeks/week-02/) | HOTL 거버넌스 상세, EU AI Act 컴플라이언스, Governance-as-Code | 첫 번째 에이전틱 루프 구현 (Lab 02) |
| [3주](/weeks/week-03/) | MCP 아키텍처 심층 분석, TBAC/거버넌스 게이트웨이, MIG 컴퓨팅 격리 | MCP 서버 구현과 보안 검증 (Lab 03) |

### Phase 2: 하네스 엔지니어링 (4–6주)

| 주차 | 이론 | 실습 |
|------|------|------|
| [4주](/weeks/week-04/) | 루프 패러다임 — Test-time Compute Scaling, Ralph Loop/RLM/autoresearch | Ralph 루프 구현과 누적 학습 (Lab 04) |
| [5주](/weeks/week-05/) | 컨텍스트 창 관리, Context Rot 방지, 상태 추적 파일 설계 | 컨텍스트 관리 시스템 구현 (Lab 05) |
| [6주](/weeks/week-06/) | 인스트럭션 튜닝, "Sign" 메타포, 영구 컨텍스트 페이로드 설계 | PROMPT.md 튜닝 실습 (Lab 06) |

### Phase 3: 멀티에이전트 SDLC (7–9주)

| 주차 | 이론 | 실습 |
|------|------|------|
| [7주](/weeks/week-07/) | 에이전트 역할 분담, 전통적 SDLC와 에이전틱 SDLC 비교 | 멀티에이전트 파이프라인 설계 (Lab 07) |
| [8주](/weeks/week-08/) | 플래너 에이전트 설계, 명세서 자동 생성, 코드베이스 분석 | 플래너 에이전트 구현 (Lab 08) |
| [9주](/weeks/week-09/) | QA 에이전트, 자동 테스트 파이프라인, 피드백 루프 | QA 에이전트 구현 (Lab 09) |

### Phase 4: 오픈소스 모델 & MLOps (10–12주)

| 주차 | 이론 | 실습 |
|------|------|------|
| [10주](/weeks/week-10/) | DeepSeek-Coder-V2 아키텍처, 오픈소스 vs 상용 API 비교, 도구 생태계 | vLLM 배포 실습 (Lab 10) |
| [11주](/weeks/week-11/) | vLLM 고처리량 추론, CUDA 최적화, MIG 슬라이스 활용 | 고처리량 추론 서버 구축 |
| [12주](/weeks/week-12/) | 텔레메트리 설계, LLM-as-Judge 평가 프레임워크, 비용 최적화 | 텔레메트리 & LLM-as-Judge (Lab 11, 12) |

### Phase 5: 캡스톤 Ralphthon (13–16주)

| 주차 | 내용 |
|------|------|
| [13주](/weeks/week-13/) | 팀 구성, 프로젝트 주제 선정, 시스템 아키텍처 설계 |
| [14주](/weeks/week-14/) | Ralphthon 실행 — 하네스 구현, 에이전트 연동, 반복 개선 |
| [15주](/weeks/week-15/) | 시스템 통합, 자동 테스트, 발표 자료 준비 |
| [16주](/weeks/week-16/) | 최종 발표 및 데모, 동료 평가, 수업 정리 |

## 평가 기준

| 항목 | 비율 | 내용 |
|------|------|------|
| 실습과제 (Lab 01–12) | 40% | 개인 제출, GitHub PR |
| 중간 프로젝트 | 20% | Phase 1–3 통합 시스템 |
| 캡스톤 Ralphthon | 30% | 팀 프로젝트, 최종 발표 |
| 기여 & 참여 | 10% | GitHub PR 기여, 수업 토론 |

## 교재 및 참고자료

### 주요 참고자료
- Huntley, G. (2025). *The Ralph Loop: Deterministic Agentic Engineering*
- Anthropic. (2026). *Claude Code Documentation*
- NVIDIA. (2025). *DGX H100 MIG Configuration Guide*

### 추가 참고자료
- Karpathy, A. (2025). *autoresearch: Automated ML Research*
- Zhang, A. et al. (2025). *Recursive LM: Language Models that Call Themselves*
- Snell, C. et al. (2024). *Scaling LLM Test-Time Compute Optimally*
- Hong, S. et al. (2024). *MetaGPT: Meta Programming for Multi-Agent Collaborative Framework* (ICLR 2024)
- Qian, C. et al. (2024). *ChatDev: Communicative Agents for Software Development* (ACL 2024)
- Damani, S. et al. (2025). *Towards a Science of Scaling Agent Systems* (DeepMind + MIT)

### 온라인 자료
- [Model Context Protocol 공식 문서](https://modelcontextprotocol.io)
- [vLLM 공식 문서](https://docs.vllm.ai)
- [DeepSeek-Coder-V2 논문](https://arxiv.org/abs/2406.11931)
- [Gemini CLI 문서](https://github.com/google-gemini/gemini-cli) — Google의 AI 코딩 CLI
- [Codex CLI 문서](https://github.com/openai/codex) — OpenAI의 터미널 코딩 에이전트
- [A2A Protocol Specification](https://google.github.io/A2A/) — Google의 Agent-to-Agent 통신 표준
- [SWE-Bench](https://www.swebench.com/) — 에이전트 코딩 벤치마크

## 수강 전 요구사항

- Python 3.10+ 프로그래밍 능력
- Git/GitHub 기본 사용법
- Linux 커맨드라인 기초
- 머신러닝 기초 (선수과목: AI 기초, 딥러닝)

## 문의

강의 관련 문의는 GitHub Issue 또는 이메일(yj.lee@chu.ac.kr)로 연락주세요.
수업 자료 오류 발견 시 [GitHub Issue](https://github.com/halla-ai/ai-systems-2026/issues)를 통해 신고해 주세요.
