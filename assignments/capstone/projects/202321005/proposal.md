---
title: "소크라테스 튜터(Socratic Tutor) — 정답을 주지 않는 교육용 에이전트 시스템"
student_id: "202321005"
student_name: "JaeEun Kim"
submitted: "2026-04-20"
---

# 소크라테스 튜터(Socratic Tutor) — 정답을 주지 않는 교육용 에이전트 시스템

**한 줄 요약**: 학생의 버그 코드와 오답을 입력받아, 정답 코드·문장을 단 한 줄도 노출하지 않으면서 질문만으로 오개념을 교정하도록 유도하는 이중 루프 · 4-모듈 · 3-tier 방어 에이전틱 시스템.

**학번 / 이름**: 202321005 / JaeEun Kim
**GitHub 저장소**: https://github.com/JaeEunKim-hub/ai-systems-2026-capstone-socratic-tutor

> v4 설계 원칙: 2026년형 에이전틱 SDLC(루프 패러다임 · 인스트럭션 튜닝 · 모듈 기반 멀티에이전트 · 컨텍스트 위생 · 아티팩트 핸드오프 · Critic 패턴 · 3-tier Boundary System)를 결합한 교육용 에이전트. 에이전트 개별 나열을 버리고 **4개 모듈**(Analysis / Dialogue / Review / Logging)로 재구성. Review Module 내부에 Advisory 센서(Q-Critic)와 Deterministic 센서(Validator)의 병렬 AND 게이트. 각 모듈이 Guides / Sensors / Backpressure / Observer 중 어느 역할에 대응되는지 1:1 매핑.

---

## 1. 문제 정의

### 1.1 현재 상황 — 소크라테스 튜터 시스템이 마주한 세 가지 기술적 난제

LLM에 "소크라테스식으로 가르쳐라"라는 프롬프트만 걸어놓고 돌려보면, 내부 파일럿(Claude Sonnet 4.6 단일 세션, 15~30턴 대화 20세션)에서 세 가지 실패 양상이 반복 관찰된다. 셋 모두 측정 가능하며, 본 프로젝트가 해결해야 할 핵심 과제다.

#### 난제 ① Response Loop — 문맥이 길어질수록 같은 질문을 반복한다

- **관찰**: 턴 12 이후 *"루프가 언제 종료되어야 할까요?"* 같은 Level 1 질문이 연속 3회 이상 등장. 학생이 이미 답변했음에도 이전 힌트 수위를 잊고 Level 1로 회귀.
- **정량**: 질문 유사도(embedding cosine ≥ 0.85) 반복률이 초반 5턴에서는 3%이나, 15턴 이후 **22%까지 상승**.
- **원인**: Context Rot (Week 5). 긴 대화 창에서 LLM이 앞쪽의 원칙·수위 정보를 잃고 평균 응답으로 회귀.
- **교육적 폐해**: 학생은 "시스템이 내 말을 안 듣는다"고 느끼고 이탈.

#### 난제 ② State Drift — 학생 이해도(State)를 연속적으로 유지하기 어렵다

- **교육의 핵심**: *"이 학생이 지금 어디까지 이해했는가"*를 추적하면서 다음 질문 수위를 결정하는 것. 튜터링에서는 오히려 모델의 "답 잘 내기"보다 **이해도 모델링**이 중요하다.
- **관찰**: 학생이 턴 3에서 "인덱스는 0부터 시작한다"를 이해했음에도, 턴 9에서 동일 개념을 묻는 질문이 재등장. 힌트 Level이 3→1→2→1로 **비일관적으로 진동**.
- **원인**: 이해도가 대화 텍스트 속에 암묵적으로 섞여 있을 뿐 **외부화된 상태로 저장되지 않음**. LLM은 무상태(stateless)라 매 턴 이력을 재해석하며 누적 오개념을 구조화해 인식하지 못한다.
- **교육적 폐해**: 학생 입장에서 튜터가 "아까 그거 내가 이해했는데 또 물어보네" → 신뢰 붕괴.

#### 난제 ③ Unverifiable Output — 질문이 "소크라테스식"인지 사후 검증할 수단이 없다

- **문제의 본질**: "정답을 주지 말고 질문만 해라"는 규칙은 **주관적 판단**이 필요하다. 단순 정규식으로는 검출 불가.
  - 예: *"이 리스트의 마지막 원소를 가져오려면 인덱스가 길이보다 하나 작아야겠죠?"* — 문법상 의문문이지만 사실상 정답을 평서문 뒤 꼬리로 붙인 **유사 의문문**. 규칙 기반 필터는 통과시킨다.
- **반대 실패**: 순수 규칙 기반(금지어 매칭)만 쓰면 합법적 교육 비유("리스트를 책꽂이라고 생각해 볼까요?")까지 오탐으로 차단.
- **정량**: 내부 파일럿 50턴 중 **교수자 평가 기준 "소크라테스식 부적합" 판정 18% (9건)**. 이 중 정규식 필터가 잡아낸 건 2건뿐, 나머지 7건은 사람이 로그를 보고서야 발견.
- **교육적 폐해**: 튜터가 정답을 슬쩍 흘리면 학생의 사고 과정이 단축되어 학습 목표 자체가 무너진다.

#### 세 난제는 서로 연쇄적으로 악화된다

```
   ② State Drift ──── 이해도를 놓침 ──▶ ① Response Loop
        ▲                                       │
        │                                       ▼
   학생 포기 ◀─── 품질 하락 ───── ③ Unverifiable Output
```

상태가 흐려지면(②) 같은 수위의 질문이 반복되고(①), 반복 질문은 모델의 품질 하락으로 이어져 정답 유출 가능성이 커지며(③), 결국 학생이 이탈한다. **하나만 고쳐서는 해결되지 않는다.**

### 1.2 핵심 원칙 (설계 5원칙)

1. **Zero-Answer Policy**: 튜터는 정답을 알고 있지만 말하지 않는다.
2. **Adaptive Hinting**: 학생 상태에 따라 힌트 수위(Level 1~3)를 자동 조절한다.
3. **Dual-Sensor Quality Assurance**: Advisory 센서와 Deterministic 센서가 **동시에** 승인해야 출력이 나간다(AND 게이트).
4. **Context Hygiene**: 대화가 길어져도 튜터가 규칙과 목표를 망각하지 않게 한다.
5. **3-tier Defense**: 선언적 / 검증적 / 구조적 경계를 중첩하여 어느 한 층이 뚫려도 다음 층이 방어한다.

### 1.3 왜 에이전틱 접근인가 — 그리고 왜 강한 시스템 제어가 동반되어야 하는가

§1.1의 세 난제는 "프롬프트를 더 잘 쓴다"거나 "더 큰 모델을 쓴다"로 풀리지 않는다. 각각이 **서로 다른 계층의 문제**이고, 각 계층에 맞는 제어 메커니즘이 따로 필요하기 때문이다. 또한 이 시스템은 일반 코딩 에이전트와 달리 **교육적 효과**를 최종 목표로 하므로, 아키텍처 선택이 곧 학습 결과 선택이 된다.

#### 1.3.0 교육적 관점 — 단일 LLM 접근은 왜 "교육 효과"를 파괴하는가

단일 LLM 호출로 "소크라테스식으로 가르쳐라"를 시키면, 단순히 "덜 좋은 튜터"가 되는 게 아니라 **교육 효과가 역전**될 수 있다. 세 가지 이유가 있다.

**① 올바른 교육 방향 제공 불가 — Drift의 누적**
- 소크라테스식 튜터링의 본질은 *"학생의 인지 지점(zone of proximal development)을 정확히 짚고, 그 바로 한 칸 위를 질문으로 유도"*하는 것이다. 힌트 Level이 진동하면(난제 ②) 인지 부하가 증가해 학습이 **오히려 나빠진다** (Sweller 1988 Cognitive Load Theory).
- 단일 LLM은 매 턴 대화 이력을 통째로 재해석하므로 "이 학생의 현재 인지 지점"을 연속적으로 표상하지 못한다. 10턴 이상 대화에서 방향성 일관성이 붕괴.

**② 교육 효과 극대화 불가 — Aha-moment 설계의 실패**
- 교육의 목표는 질문을 잘 만드는 것이 아니라 **학생이 스스로 답에 도달하는 순간(Aha-moment)**을 설계하는 것이다. 이를 위해서는 "다음 질문이 학생을 Aha에 1단계 더 가깝게 만드는가"를 판정해야 하는데, 이는 생성자(Tutor)와 별개의 **평가자(Critic)**가 필요하다.
- 단일 LLM에게 "질문을 만들고 스스로 평가해라"고 시키면 self-grading bias로 자기 질문을 관대하게 평가 → Aha-moment 설계가 무작위화됨.

**③ 교육 효과 역전 가능성 — 정답 유출의 누적 학습**
- 단일 LLM이 5%의 확률로 정답을 흘린다고 가정하면, 20턴 세션에서 정답이 **적어도 한 번은 유출될 확률이 64% (1 - 0.95²⁰)**. 학생은 "좀 조르면 답이 나오는 시스템"이라고 학습하게 되고, 이후 **자율적 문제 해결 의지 자체가 꺾인다**.
- 이것이 Khan Academy Khanmigo(2024)에서 보고된 "학생들이 AI 튜터를 힌트 추출기로만 사용하는" 현상의 구조적 원인이다.

**즉, 단일 LLM 접근은 "품질이 낮은 튜터"가 아니라 "교육적으로 해로운 환경"이 될 수 있다.** 이것이 본 프로젝트가 에이전틱한 구조 + 강한 시스템 제어를 **교육학적으로도** 요구받는 이유다.

#### 1.3.1 난제별 필요한 제어 계층

| 난제 | 근본 계층 | 단일 LLM 호출로 왜 안 되는가 | 필요한 시스템 제어 |
|------|----------|-----------------------------|------------------|
| ① Response Loop | 컨텍스트 / 상태 | 모델은 자신의 앞선 출력을 "사실"로만 읽을 뿐 "반복을 피해야 할 이력"으로 인식하지 못함. 긴 컨텍스트에서 수위·원칙 정보가 희석됨 | 외부화된 상태 + 주기적 **Fresh Context 리셋** (Week 5) |
| ② State Drift | 상태 표현 | 이해도가 자연어에 섞여 있으면 매 턴 재추론해야 함 — 비용·일관성 모두 붕괴. LLM은 무상태이므로 "누적 상태"라는 개념이 없음 | **구조화된 상태 아티팩트** (`student_gap.json`, JSON 스키마 핸드오프, Week 7) |
| ③ Unverifiable Output | 품질 검증 | 출력을 내는 주체와 검증하는 주체가 같으면 자기 검열이 불완전 (self-grading bias). 또한 주관 기준과 객관 기준이 혼재하면 한쪽 기준만으로는 사각지대 발생 | **독립된 Critic + 이종 센서 (Advisory ∥ Deterministic) AND 게이트** (Week 6·9) |

#### 1.3.2 결국 필요한 시스템 제어 목록 (7종)

단일 에이전트 1개로는 세 난제를 동시에 해결할 수 없다. 구체적으로 다음 제어 메커니즘이 **모두 필요**하다:

1. **루프 제어 (Week 4 Ralph Loop 응용)**: 질문이 기준 미달이면 학생에게 전달하기 전에 거부하고 다시 만드는 내부 루프. → 난제 ③ 대응.
2. **독립 QA 에이전트 (Week 9)**: Dialogue를 생성한 LLM이 스스로 평가하면 자기 검열 편향이 생기므로, 별도 세션·프롬프트의 Q-Critic 분리. → 난제 ③ 대응.
3. **이종 센서 결합 (Week 6 제약 개념)**: Advisory(Q-Critic, 주관)와 Deterministic(Validator, 규칙)을 AND로 묶어 양쪽의 실패 모드를 상호 보완. → 난제 ③의 사각지대 제거.
4. **외부화된 상태 아티팩트 (Week 5·7)**: 이해도·오개념·힌트 수위를 LLM 컨텍스트가 아닌 JSON으로 보관, 모듈 간 핸드오프 시 오직 이 파일만 공유. → 난제 ② 대응.
5. **Context Reset 정책 (Week 5)**: 10턴마다 Dialogue 세션을 초기화하되 상태 아티팩트만 이어받아 반복 질문 고리를 끊는다. → 난제 ① 대응.
6. **구조적 경계 (Week 6 Tier 3)**: 정답 정보를 Dialogue 모듈의 컨텍스트에 **물리적으로 넣지 않음**. 어떤 프롬프트 인젝션이 와도 유출될 수 없게 하는 정보이론적 방어. → 난제 ③의 최후 방어선.
7. **Observer 분리**: 위 모든 동작의 지표(반복률, 재생성 횟수, Tier 3 누출)를 수집하는 별도 Logging 모듈. → 세 난제 모두의 **사후 검증 근거**.

#### 1.3.3 단일 호출 vs 스크립트 vs 에이전트 시스템 비교

| 접근 | 난제 ① Response Loop | 난제 ② State Drift | 난제 ③ Unverifiable |
|------|:-------------------:|:-----------------:|:-------------------:|
| 단일 LLM 호출 (system prompt) | ❌ | ❌ | ❌ |
| 스크립트 기반 힌트 (규칙) | △ | ❌ | △ (정규식만) |
| 단일 에이전트 (메모리 있음) | △ | △ | ❌ (자기 검열 편향) |
| **본 프로젝트: 4-모듈 + 이중 루프 + 3-tier** | ✅ | ✅ | ✅ |

#### 1.3.4 HITL가 아니라 HOTL이어야 하는 이유 (Week 1)

- 교수는 매 대화에 개입할 수 없다 — 수업당 수십 명 동시 세션.
- 더 본질적으로, **교수가 개입하는 순간 소크라테스식 "학생 스스로 발견" 원칙이 깨진다**. 학생이 "막히면 교수가 알려줄 것"이라고 기대하면 사고 과정을 멈춰 버린다.
- 따라서 시스템은 자율 동작하고 (**HOTL**, Human-On-The-Loop), 교수는 Review Module의 reject 로그와 `PATH.md`를 **사후에만** 검토한다.

#### 1.3.5 결론

> "에이전트 하나"가 아니라 **"에이전트들 + 그들을 제어하는 하네스"**가 필요하다.
>
> 이것이 본 프로젝트가 **4개 모듈(Analysis / Dialogue / Review / Logging) + 3-tier Boundary + 이중 루프 구조**를 채택한 직접적 이유이며, §2부터의 설계가 각 난제를 어떻게 봉쇄하는지를 모듈 단위로 증명한다.

### 1.4 설계 원리 — 주차별 매핑 개요

| 주차 | 이론 | 본 시스템에 적용된 부분 |
|------|------|----------------------|
| Week 4 | Ralph Loop | 소크라테스 외부 루프(학생 입력 → Gap 분석 → 질문 생성 → 학생 사고) |
| Week 5 | Context Rot | Fresh Context 주기적 초기화 + 아티팩트 기반 상태 저장 |
| Week 6 | Instruction Tuning · Harness(Guides/Sensors/Backpressure) · Advisory vs Deterministic 제약 | SOCRATES.md 제어 시스템, 3-tier Boundary, 이종 센서 병렬 |
| Week 7 | 중앙 집중형 조율 · 아티팩트 스키마 · Validation Gate · Critic 패턴 | 모듈 기반 조율, `student_gap.json`, Review Module |
| Week 9 (예상) | QA 에이전트 독립성 | Analysis / Review 모듈이 Dialogue 모듈과 역할 격리 |

### 1.5 목표 사용자 / 사용 맥락

| 사용자 | 시점 | 사용 방식 |
|--------|------|----------|
| 프로그래밍 입문 수강생 | 과제 중 버그 발견 시 | CLI/웹에서 코드·에러 메시지를 제출, 질문만 돌려받음 |
| 조교 | 주 1회 | `PATH.md` 리포트로 학생별 오개념 패턴 확인 |
| 교수 | 학기말 | Logging Module의 지표로 교재 개선점 도출 |

**대상 과목**: Python 기초, 자료구조 입문(초기 범위). 향후 SQL·알고리즘으로 확장.

---

## 2. 제안 시스템 설계

### 2.1 하네스 설계 — 제어 시스템으로서의 SOCRATES.md

#### 2.1.1 왜 하네스는 "그냥 프롬프트"가 아닌가

SOCRATES.md 같은 지침서를 보면 *"그냥 system prompt 잘 써둔 것 아닌가?"* 오해가 생긴다. 하지만 에이전틱 SDLC에서 **하네스(Harness)**는 단방향 지시문이 아니라 **피드포워드 + 피드백 + 압력 제어**가 결합된 제어 루프 시스템이다. Week 6의 3요소로 쪼개면:

| 구성요소 | 역할 | 방향 | 본 시스템에서 |
|---------|------|------|--------------|
| **Guides** (가이드) | 에이전트가 행동하기 전 방향 제시 | Feedforward | Analysis Module이 생성하는 `student_gap.json` + SOCRATES.md |
| **Sensors** (센서) | 결과물을 측정 | Feedback | Review Module (Q-Critic + Validator) |
| **Backpressure** (압력 제어) | 품질 미달 시 출력 차단·재생성 | Control | 내부 루프 재생성, Context Reset 트리거 |

세 요소가 **닫힌 루프**로 돌아야 비로소 "하네스"라고 부를 수 있다.

#### 2.1.2 Advisory 센서 vs Deterministic 센서 (Week 6 제약 개념)

센서는 한 종류가 아니다. Week 6의 두 제약 방식을 센서에도 그대로 적용한다.

| 센서 종류 | 특성 | 판정 기준 | 실패 모드 | 본 시스템에서 |
|----------|------|----------|----------|--------------|
| **Advisory (soft)** | 주관적·맥락 기반 | "교육적으로 훌륭한가?" | False Negative (미묘한 품질 저하를 놓침) | Q-Critic |
| **Deterministic (hard)** | 객관적·규칙 기반 | "금지 문자열이 포함됐는가?" | False Positive(오탐)은 적지만 우회 가능 | Validator |

두 센서는 서로의 실패 모드를 보완한다. Q-Critic이 놓친 교묘한 정답 유출은 Validator의 규칙 기반 필터가 잡고, Validator가 허용한 "겉보기엔 깨끗하지만 답을 유도하는 설명문"은 Q-Critic이 잡는다. 두 센서를 모두 통과한 질문만 학생에게 전달된다(**AND 게이트**).

#### 2.1.3 SOCRATES.md — Guides 층의 구체 내용

```markdown
# SOCRATES.md — 교육 지침 (Guides 층)

## 핵심 원칙: Zero-Answer Policy
- 어떤 상황에서도 코드 조각(Code Snippet)을 직접 제공하지 않는다.
- 학생이 "정답이 뭐야?"라고 물으면, 질문으로 되받아친다.
- Learning 스타일을 강제하며, 설명(Explanatory)보다 발견(Discovery)에 집중한다.

## 힌트 강도 조절 (Adaptive Hinting)
- Level 1 (Concept):     추상적 개념 질문   — "루프가 언제 종료되어야 할까요?"
- Level 2 (Logic):       논리적 모순 지적   — "변수 i가 증가하지 않으면 어떻게 될까요?"
- Level 3 (Scaffolding): 의사코드 유도     — "한글로 로직을 먼저 적어볼까요?"

## 질문 품질 요건 (Review Module 판정 기준)

### Advisory (Q-Critic) 기준
- 질문은 반드시 의문문 형태여야 한다 (답을 숨긴 설명문 금지).
- 현재 hint_level을 초과하지 않아야 한다.
- pedagogical_goal과 방향이 일치해야 한다.
- 학생의 misconception을 실제로 건드려야 한다.

### Deterministic (Validator) 기준
- forbidden_content 목록의 문자열을 포함하지 않아야 한다.
- 코드 블록(```) 마커를 포함하지 않아야 한다.

## Deterministic Hooks (Backpressure 트리거)
- 학생 제출 코드의 정답 포함 여부를 Analysis Module이 100% 검증한 후 인터랙션 시작.
- Review Module의 두 센서가 동시에 pass해야 학생에게 전달된다.
- Review 재시도 3회 초과 시 Context Reset 자동 트리거.
```

#### 2.1.4 3-tier Boundary System — 왜 세 층이 필요한가

SOCRATES.md의 Zero-Answer Policy 하나를 **세 층위로 중첩 방어**한다.

| Tier | 경계 종류 | 본 시스템 구현 | 실패 모드 | 방어 강도 |
|------|----------|---------------|----------|----------|
| **Tier 1** | 선언적 (Declarative) | SOCRATES.md 지침 | 프롬프트 인젝션, 망각 | 확률적 |
| **Tier 2** | 검증적 (Verificational) | Review Module (Advisory + Deterministic 센서) | 센서 사각지대 | 확률적 |
| **Tier 3** | 구조적 (Structural) | Dialogue Module에 정답을 애초에 주지 않음 | — (물리적 불가능) | **정보이론적** |

**Tier 3가 가장 중요한 이유**: Tier 1·2는 "어기지 말라고 말하고, 어기면 잡는" 확률적 방어인 반면, Tier 3는 *"어길 수 있는 정보 자체를 제거"*하는 정보이론적 방어다. Dialogue Module이 정답 문자열 `len(arr) - 1`을 출력할 확률은, 해당 정보가 context에 존재하지 않는 한 LLM의 일반 학습 지식에 의존한 추측으로만 제한된다.

#### 2.1.5 하네스 제어 루프 전체 그림

```
                    ┌─────────────────────────────────┐
                    │  Tier 1: Guides                  │
                    │  (SOCRATES.md · student_gap.json)│  Feedforward
                    └──────────────┬──────────────────┘
                                   │ 행동 지침 주입
                                   ▼
  ┌───────────────┐         ┌─────────────┐        ┌───────────────┐
  │ Tier 3:       │ ─────>  │  Dialogue   │ ─────> │ 질문 초안      │
  │ Structural    │ Gap만   │   Module    │        │                │
  │ (정답 차단)   │ 전달    └─────────────┘        └───────┬───────┘
  └───────────────┘                                         │
                                                            ▼
                    ┌─────────────────────────────────┐
                    │  Tier 2: Sensors (Review Module) │
                    │  ┌─Q-Critic─┐  ┌──Validator──┐   │
                    │  │ Advisory │∥ │Deterministic│   │  Feedback
                    │  └──────────┘  └─────────────┘   │
                    │       └──── AND ────┘            │
                    └──────────────┬──────────────────┘
                                   │ reject (둘 중 하나라도)
                                   ▼
                    ┌─────────────────────────────────┐
                    │  Backpressure                    │
                    │  (재생성 루프 · Context Reset)   │  Control
                    └─────────────────────────────────┘
```

### 2.2 루프 아키텍처 — 이중 루프 구조

Week 4의 Ralph 루프가 "실행 → 검증 → 재시도"였다면, 소크라테스 시스템은 **외부 루프(학생 ↔ 시스템)**와 **내부 루프(질문 생성 ↔ 비평)**가 결합된 이중 구조다.

- **외부 루프 (학생 대화)**: 학생 입력 → Analysis → Dialogue/Review → 학생 사고 → 새 입력
- **내부 루프 (질문 품질 보증)**: Dialogue 초안 → Review(Q-Critic ∥ Validator) → (reject 시) Dialogue 재생성

```
 [외부 루프]
┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
│ 학생 입력     │──>│ Analysis Module │──>│ Dialogue     │
│ (코드/답변)   │   │ (정답 보유)     │   │ Module       │
└──────────────┘   └─────────────────┘   └──────┬───────┘
       ▲                                         │
       │                                         ▼  [내부 루프]
       │                                ┌────────────────┐
       │                                │ Review Module  │
       │                                │ (AND 게이트)   │
       │                                └──────┬─────────┘
       │                                실패 │ │ 통과
       │                           ┌─────────┘ │
       │                           │           ▼
       │                           │   [학생에게 전달]
       │                           │
       │                           └──> Dialogue 재생성
       │                                (Backpressure)
       │                                      │
       └──────────────── 학생 사고 ◀──────────┘
```

- **Backpressure**: 학생 답변이 루브릭에 미달 → 에이전트가 거부하고 다시 질문. Review Module이 reject하면 튜터 스스로에게도 재생성을 강제.
- **Garbage Collection**: 학생이 잘못된 개념(Conception Rot)을 가지면 오염된 맥락을 끊고 새로운 비유로 개념을 재정립.

### 2.3 모듈 아키텍처 (Module-based Topology)

개별 에이전트 6개를 나열하는 대신, 기능별로 묶인 **4개 모듈**로 시스템을 구성한다. 각 모듈은 하네스 제어 시스템의 한 역할과 1:1로 대응된다.

#### 2.3.1 모듈 스택 (System Overview)

| 모듈 | 별칭 | 내부 에이전트 | 하네스 역할 | 아티팩트 In → Out |
|------|------|--------------|-------------|-------------------|
| ① Analysis Module | The Truth Center (Backstage) | Judge + Planner | Guides 생성 | Student Code → `student_gap.json` |
| ② Dialogue Module | The Frontstage | Tutor | Action (생성) | `student_gap.json` → Question Draft |
| ③ Review Module | The Quality Filter | Q-Critic + Validator | Sensors & Backpressure | Question Draft → Approved Question / Reject |
| ④ Logging Module | The Observer | Path Tracker | Observer (관찰) | Full Conversation → `PATH.md` |

#### 2.3.2 Analysis Module — "The Truth Center"

정답(Ground Truth)에 접근할 수 있는 **유일한 영역**. 이 경계 안쪽에만 정답이 존재하고, 밖으로 나가는 데이터는 오직 가공된 상태 정보(`student_gap.json`)뿐이다.

| 내부 에이전트 | 역할 | 정답 접근 |
|--------------|------|----------|
| **Judge** | 학생 제출 코드에 정답이 통째로 포함됐는지 판정 | ✅ |
| **Planner** | 학생 코드와 정답을 비교해 Gap 식별, `student_gap.json` 생성 | ✅ |

**동작 순서**: Judge가 먼저 "학생이 답을 베껴왔는지" 판정 → 통과하면 Planner가 Gap 아티팩트를 생성하여 모듈 밖으로 내보낸다.

**장점**: 정답 데이터가 이 모듈 경계 밖으로 유출되지 않는다는 단일 보안 장벽을 세우기 쉽다. Week 9의 QA 독립성 원칙을 모듈 수준에서 구현.

#### 2.3.3 Dialogue Module — "The Frontstage"

학생과 실제로 대화하는 **유일한 모듈**. Tier 3 경계의 보호 대상.

| 내부 에이전트 | 역할 | 정답 접근 |
|--------------|------|----------|
| **Tutor** | `student_gap.json`만 읽고 소크라테스식 질문 생성 | ❌ |

**핵심 특성**: 정답을 받는 입력 포트 자체가 없다. Analysis Module이 넘겨준 Gap 아티팩트와 Review Module의 피드백만 받는다. 구조적으로 정답 유출이 불가능하다.

#### 2.3.4 Review Module — "The Quality Filter"

Dialogue Module이 내뱉는 모든 말을 검사하는 다중 필터. 하네스의 **Sensors + Backpressure 역할을 이 모듈이 전담**한다.

| 내부 에이전트 | 센서 종류 | 판정 기준 |
|--------------|----------|----------|
| **Q-Critic** | Advisory (soft) | "질문이 교육적으로 훌륭한가?" — 형식 · 수위 · 방향성 · 타깃팅 |
| **Validator** | Deterministic (hard) | "금지 단어가 포함됐는가?" — `forbidden_content` 매칭 |

**병렬 AND 게이트 구조**:

```
                     ┌──────────┐
                     │ Q-Critic │ ─── verdict_a
            ┌───────>│ Advisory │
            │        └──────────┘
   Question │                        ┌─── AND ───> approved / rejected
   Draft ───┤                        │
            │        ┌──────────────┐│
            └───────>│  Validator   │┘── verdict_b
                     │Deterministic │
                     └──────────────┘
```

- 두 센서가 동시에 pass해야 질문이 학생에게 전달된다.
- 둘 중 하나라도 reject하면 즉시 Backpressure 발동 → Dialogue Module에 "다시 만들어" 명령.
- 재시도 N회 초과 시 Context Reset 트리거(Week 5 Context Rot 대응 연계).

**왜 병렬인가**: 두 센서의 판정 기준이 독립적이고(주관·맥락 기반 vs 규칙 기반) 실패 모드가 서로 다르므로, 직렬로 쌓는 것보다 병렬 AND 결합이 상호 보완 효과를 극대화한다.

#### 2.3.5 Logging Module — "The Observer"

대화 전체를 관찰하며 학습 궤적과 시스템 품질 지표를 기록한다. 다른 모듈에 개입하지 않으며, 정답·학생 코드 원문은 보지 않고 **메타데이터만** 수집한다.

| 내부 에이전트 | 역할 | 정답 접근 |
|--------------|------|----------|
| **Path Tracker** | 턴별 이벤트(hint_level 변화, Review reject 횟수, Aha-moment)를 수집해 `PATH.md` · `metrics.json` 생성 | ⚠️ 메타만 |

### 2.4 MCP 도구 / 외부 연동

| 도구 | 제공자 | 용도 |
|------|--------|------|
| **Filesystem MCP** | 공식 | `student_gap.json`, `PATH.md`, `metrics.json` 아티팩트 I/O |
| **Sandboxed Python Executor (자체 구현 MCP)** | 자체 | Analysis Module이 학생 코드를 격리 환경에서 실행하여 실제 오류 재현 |
| **Anthropic Messages API** | Anthropic | 세 LLM(Opus/Sonnet/Haiku) 호출, prompt caching 활성화 |
| **SQLite (로컬)** | — | 학생별 대화 이력, Validator forbidden_list 저장 |

**외부 네트워크 미사용 원칙**: 학생 코드를 외부 실행 환경에 보내지 않고 로컬 sandbox(Docker + subprocess timeout)에서만 실행하여 프라이버시/비용 양쪽을 통제.

### 2.5 아티팩트 핸드오프 설계 (Week 5·7 참조)

모듈 간 핸드오프는 **JSON 스키마**로 엄격히 명시한다. 각 모듈이 필요 이상의 정보를 보지 못하게 하는 것이 곧 **Tier 3 구조적 경계의 구현**이다. 본 절은 두 핵심 아티팩트 스키마와 전체 흐름을 정의한다.

#### 2.5.1 `student_gap.json` 스키마 (Compact JSON, Week 7 원칙)

Analysis Module이 생성하고 Dialogue / Review Module이 읽는, **Tier 3 구조적 경계의 핵심 매개체**. Compact JSON 설계 원칙에 따라 평탄한 구조가 아닌 의미 단위로 중첩한다.

```json
{
  "req_id": "LAB-06-SOCRATES",
  "student_status": {
    "current_error": "IndexError",
    "misconception": "loop_boundary_confusion",
    "iteration_count": 4,
    "last_hint_level": 2
  },
  "pedagogical_goal": "Make the student check the length of the list using len()",
  "forbidden_content": ["len(arr)-1", "range(len(arr))"]
}
```

**필드별 역할 및 Tier 3 증거**

| 필드 | 역할 | 접근 모듈 |
|------|------|----------|
| `req_id` | 세션·요청 추적 ID (Logging 연계) | Analysis → Dialogue → Review → Logging |
| `student_status.current_error` | 학생 코드 실행 결과의 에러 타입만 전달 (스택트레이스 원문 X) | Dialogue가 "어디서 왜 실패했는지"를 추상 수준으로 파악 |
| `student_status.misconception` | Analysis가 분류한 오개념 카테고리 | Dialogue가 질문 방향 결정 |
| `student_status.iteration_count` | 현재까지 오답 턴 수 | 힌트 수위 자동 상향 트리거 |
| `student_status.last_hint_level` | 직전 턴 힌트 Level (1~3) | Dialogue가 동일 수위 반복 방지 (난제 ① 대응) |
| `pedagogical_goal` | 이번 질문이 달성해야 할 학습 목표 (자연어) | Q-Critic 평가 기준 |
| `forbidden_content` | Validator 규칙 매칭용 금지 문자열 목록 | Validator (Dialogue는 읽지 않음) |

**스키마에 명시적으로 존재하지 않는 필드**: `reference_solution`, `correct_code`, `full_student_code` — Dialogue Module은 정답 문자열·원본 코드를 **물리적으로 볼 수 없다**. 이것이 Tier 3 구조적 경계의 증명.

#### 2.5.2 `review_report.json` 스키마 (Review Module → Dialogue Module)

Review Module의 **병렬 AND 판정**을 하나의 아티팩트로 통합한다. Dialogue는 reject를 받으면 이 JSON을 그대로 feedback으로 받아 다시 생성한다.

```json
{
  "question_draft": "리스트의 마지막 요소에 접근할 때 어떤 인덱스를 써야 할까요?",
  "advisory_verdict": {
    "source": "Q-Critic",
    "result": "reject",
    "reasons": ["hint_level_overshoot: Level 2 허용인데 Level 3 스캐폴딩에 근접"]
  },
  "deterministic_verdict": {
    "source": "Validator",
    "result": "pass",
    "matched_forbidden": []
  },
  "final_verdict": "reject",
  "retry_hint": "인덱스 대신 '범위'라는 추상 개념으로 질문을 재구성할 것"
}
```

**AND 연산 규칙**: `final_verdict = "pass"` iff `advisory_verdict.result == "pass" AND deterministic_verdict.result == "pass"`.
둘 중 하나라도 reject면 `final_verdict = "reject"`이고, Dialogue 재생성을 위해 `retry_hint`가 합성된다. 두 센서의 `reasons` / `matched_forbidden`을 merge 규칙으로 결합 (Advisory 우선, Deterministic 부속).

**Dialogue Module이 받는 feedback의 제약**: `retry_hint`는 **자연어 지시**여야 하며, 절대 정답을 암시하는 어휘를 포함해서는 안 된다. 이를 위해 retry_hint 생성 단계 자체도 Validator를 한 번 더 거친다 (이중 필터).

#### 2.5.3 모듈 단위 핸드오프 흐름

```
[학생 코드 제출]
      │
      ▼
╔═══════════════════════════════════════════╗
║  ① Analysis Module (The Truth Center)     ║
║  ┌──────────┐          ┌────────────┐    ║
║  │  Judge   │ ───────> │  Planner   │    ║
║  └──────────┘          └─────┬──────┘    ║
║  (정답 접근 ✅)               │           ║
╚══════════════════════════════╪═══════════╝
                                │ student_gap.json
                                │ ◀── Tier 3 경계 발생 지점
                                ▼
╔═══════════════════════════════════════════╗
║  ② Dialogue Module (The Frontstage)       ║
║  ┌──────────┐                              ║
║  │  Tutor   │ ◀─── review_report (feedback)║
║  └─────┬────┘                              ║
║  (정답 접근 ❌)                             ║
╚════════╪═══════════════════════════════════╝
         │ question_draft
         ▼
╔═══════════════════════════════════════════╗
║  ③ Review Module (The Quality Filter)     ║
║  ┌──────────┐   ∥   ┌────────────┐        ║
║  │ Q-Critic │       │ Validator  │        ║
║  │(Advisory)│       │(Determin.) │        ║
║  └────┬─────┘       └─────┬──────┘        ║
║       └──── AND ──────────┘                ║
╚════════╪═══════════════════════════════════╝
         │ final_verdict
         ├── reject ──> ② Dialogue 재생성 (Backpressure)
         │
         └── pass ───>  [학생에게 전달]
                              │
                              ▼
╔═══════════════════════════════════════════╗
║  ④ Logging Module (The Observer)          ║
║  ┌──────────────┐                          ║
║  │ Path Tracker │                          ║
║  └──────────────┘                          ║
╚═══════════════════════════════════════════╝
```

**핵심 설계 포인트**

1. **Tier 3 경계 발생 지점**은 `student_gap.json`이 Analysis 모듈을 빠져나가는 화살표다. 이 지점 이후 정답 원문은 시스템 어디에도 존재하지 않는다.
2. **Dialogue ↔ Review 루프**는 아티팩트로 닫혀 있다 (`question_draft` → `review_report.retry_hint` → 새 `question_draft`). 대화체 피드백이 아닌 구조화된 JSON이므로 Context Rot(난제 ①)에 강하다.
3. **Logging Module은 아티팩트를 "관찰"만 한다**. 다른 모듈은 Logging의 존재를 모른 채 동작하며 (Observer 패턴), 관찰이 파이프라인 성능을 왜곡하지 않는다.
4. **Compaction 전략**: 장시간 세션에서는 Logging Module이 과거 `student_gap.json` 시퀀스를 요약하여 Analysis Module에 `prior_turns_summary` 필드로 재주입 → Week 5 Context Rot 방지.

### 2.6 컨텍스트 랏(Context Rot) 방지 전략

소크라테스 튜터링은 대화가 길어지기 때문에, Dialogue Module의 컨텍스트 창이 학생의 오답과 이전 힌트로 가득 차면서 Tutor가 Tier 1(선언적 경계)을 망각할 위험이 크다. Review Module(Tier 2)이 있어도 Dialogue 초안 품질이 급격히 떨어지면 재생성 횟수가 폭증하는 2차 문제가 생긴다.

| 전략 | 내용 | 관련 Tier / 모듈 |
|------|------|-----------------|
| **Fresh Context 리셋** | N턴마다 Dialogue Module 세션 초기화 | Tier 1 재주입 |
| **State Externalization** | 대화 이력은 컨텍스트가 아닌 Logging Module에 저장 | Tier 3 확장 |
| **Compaction** | 이전 힌트들을 요약본으로 압축, Analysis Module만 참조 | — |
| **Role Reinforcement** | 세션 재진입 시 SOCRATES.md 상단 원칙을 우선 주입 | Tier 1 강화 |
| **재생성 임계값** | Review reject 3회 초과 시 자동 Fresh Context 리셋 | Tier 2 → Backpressure |

**효과**: 수십 번의 질문이 오가도 튜터가 일관된 교육 목표를 유지하며, 학생의 오개념을 닮아가는 Conception Drift를 방지. Review Module의 재생성 횟수를 컨텍스트 오염 감지 센서로도 활용.

---

## 3. 기술 스택

| 범주 | 선택 | 근거 |
|------|------|------|
| LLM (Analysis) | Claude Opus 4.7 (effort=high) | 정답 풀이·오개념 분류 정확도 중요 (Week 5 모델 라우팅) |
| LLM (Dialogue) | Claude Sonnet 4.6 (effort=medium) | 대화 빈도 높음 → 비용/품질 균형 |
| LLM (Q-Critic) | Claude Sonnet 4.6 (effort=low) | 판정만 하므로 저비용 |
| LLM (Logging 요약) | Claude Haiku 4.5 | 요약은 저렴한 모델로 충분 |
| 프레임워크 | Claude Agent SDK (Python) + Custom Modules | `.claude/agents/` 디렉토리에 모듈별 서브에이전트 정의 |
| 언어 | Python 3.12 | Anthropic SDK 공식 + 교육 대상 언어와 일치 |
| 테스트 | pytest + pytest-asyncio | Review Module 병렬 AND 게이트 테스트 |
| 컨테이너 | Docker (학생 코드 sandbox) | 무한 루프 / 파일 시스템 접근 격리 |
| 배포 | GitHub Actions + Streamlit Cloud | 무료 티어, 조교 데모 충분 |
| 관측 | SQLite + 자체 `metrics.json` | 외부 관측 SaaS 불필요 |

### 3.1 구현 예시 (Python/MCP) — 모듈 기반 스켈레톤

각 모듈을 캡슐화된 클래스로 구현하여, 상위 오케스트레이터는 모듈 단위로만 상호작용한다.

```python
# socratic_tutor.py

class SocraticTutor:
    MAX_RETRY = 3  # Review 재생성 한도 (Backpressure 임계값)

    def __init__(self):
        self.analysis = AnalysisModule()   # Judge + Planner (정답 접근 ✅)
        self.dialogue = DialogueModule()   # Tutor (정답 접근 ❌ ← Tier 3)
        self.review   = ReviewModule()     # Q-Critic ∥ Validator
        self.logging  = LoggingModule()    # Path Tracker

    def interact(self, student_code, student_message):
        # ① Analysis Module: 정답 영역에서 Gap 아티팩트 생성
        analysis_out = self.analysis.process(student_code, student_message)
        if analysis_out.rejected:  # Judge가 정답 베낌 감지
            return self._reject_with_warning()

        # ②③ 내부 루프: Dialogue 생성 → Review 검증 → (실패 시) 재생성
        question = self._generate_validated_question(analysis_out.gap)

        # ④ Logging Module
        self.logging.log(analysis_out, question)
        return question

    def _generate_validated_question(self, gap):
        """내부 루프: Review Module이 AND 게이트로 승인할 때까지 Dialogue 재생성"""
        feedback = None
        for attempt in range(self.MAX_RETRY):
            # Dialogue Module은 gap + (선택적) feedback만 본다 (정답 X, Tier 3)
            draft = self.dialogue.generate(gap=gap, feedback=feedback)

            # Review Module: Advisory ∥ Deterministic 병렬 AND 판정
            report = self.review.check(draft=draft, gap=gap)

            if report.final_verdict == "pass":
                return report.approved_question

            # 실패 시 피드백 누적, 다음 시도 (Backpressure)
            feedback = report.retry_hint

        # 재생성 한도 초과 → 컨텍스트 리셋 트리거 (Tier 1 재주입)
        return self._fallback_after_context_reset(gap)


class ReviewModule:
    """Advisory 센서와 Deterministic 센서를 병렬로 실행, AND로 결합"""
    def __init__(self):
        self.q_critic  = QCriticAgent()     # Advisory
        self.validator = ValidatorGate()    # Deterministic

    def check(self, draft, gap):
        import asyncio
        # 두 센서를 병렬로 호출 (독립 판정)
        advisory, deterministic = asyncio.run(asyncio.gather(
            self.q_critic.evaluate(draft, gap),
            self.validator.filter(draft, gap["forbidden_content"]),
        ))

        final = "pass" if (advisory.ok and deterministic.ok) else "reject"
        return ReviewReport(
            question_draft        = draft,
            advisory_verdict      = advisory,
            deterministic_verdict = deterministic,
            final_verdict         = final,
            retry_hint            = self._merge_hints(advisory, deterministic),
            approved_question     = draft if final == "pass" else None,
        )
```

### 3.2 모듈별 정답 접근 매트릭스 (Tier 3 구현 증거)

이 표가 곧 **Tier 3 구조적 경계의 증명**이다. 정답에 접근할 수 있는 모듈이 최소화되어 있고, 학생과 직접 소통하는 Dialogue Module은 정답을 물리적으로 볼 수 없다.

| 모듈 | 정답 코드 | 학생 코드 | Gap 아티팩트 | 질문 초안 |
|------|:--------:|:--------:|:------------:|:--------:|
| ① Analysis | ✅ | ✅ | ✍️ (생성) | — |
| ② Dialogue | ❌ | ❌ | ✅ | ✍️ (생성) |
| ③ Review | ❌ (forbidden만) | ❌ | ✅ | ✅ (평가) |
| ④ Logging | ⚠️ (메타만) | ⚠️ (메타만) | ⚠️ (메타만) | ✅ (메타만) |

---

## 4. 수업 기법 적용 매핑

"들어봤다"가 아닌 **"이 프로젝트에서 이렇게 쓴다"**로 기술.

| 주차 | 기법 | 적용 방식 | 검증 지표 |
|------|------|----------|----------|
| Week 1 | HOTL 거버넌스 | 교수는 매 대화에 개입하지 않고, Review reject 3회 초과 이벤트만 대시보드에서 확인 | 주당 수동 개입 건수 ≤ 3건 |
| Week 3 | MCP 서버 | 학생 코드 실행을 자체 MCP 서버로 캡슐화하여 Analysis Module이 호출 | MCP 툴콜 응답 시간 p95 < 1.5s |
| Week 4 | Ralph Loop (이중) | 외부 루프(학생 ↔ 시스템) + 내부 루프(Dialogue ↔ Review) 이중 구조 | 내부 루프 평균 재생성 횟수 ≤ 1.3회 |
| Week 5 | Context Rot 방지 | `student_gap.json` 아티팩트 + `prior_turns_summary` 압축 + N=10턴마다 Dialogue Fresh Context 리셋 | 30턴 이상 대화에서도 SOCRATES.md 원칙 위반율 0% |
| Week 5 | 모델 라우팅 | Opus(Analysis) / Sonnet(Dialogue · Q-Critic) / Haiku(Logging 요약) 3-tier | 세션당 토큰 비용 ≤ $0.80 |
| Week 6 | Instruction Tuning (SOCRATES.md) | Guides 층 기준 문서 작성, Advisory/Deterministic 제약 분리 명시 | Validator reject 0%, Q-Critic reject 10~15% (적정) |
| Week 6 | 3-tier Boundary System | Tier 1 선언적 · Tier 2 검증적 · Tier 3 구조적 중첩 | Tier 3 누출 assertion 테스트 100% 통과 |
| Week 6 | Harness (Guides/Sensors/Backpressure) | SOCRATES.md + Review + 재생성 루프로 닫힌 제어 루프 구성 | 하네스 피드백 지연 < 1회 턴 |
| Week 7 | 게이트드 파이프라인 + Critic 패턴 | Review가 AND 게이트, Critic과 Validator가 독립 판정 | AND 게이트 통과율 85% 이상 |
| Week 7 | 중앙 집중형 조율 + 아티팩트 스키마 | `SocraticTutor` 오케스트레이터가 4모듈을 조율, JSON 스키마로 핸드오프 | pydantic 스키마 검증 실패율 0% |
| Week 9 (예상) | QA 에이전트 독립성 | Q-Critic은 Dialogue와 다른 세션/프롬프트, 학생 메시지에 오염되지 않음 | Q-Critic-Dialogue 공모 케이스 0건 |

---

## 5. 개발 일정

| 주차 | 마일스톤 | 산출물 | Definition of Done |
|------|---------|--------|-------------------|
| Week 13 (2026-06-01 ~ 06-07) | Analysis + Dialogue + SOCRATES.md 스켈레톤 | `design.md`, `SOCRATES.md`, `src/analysis.py`, `src/dialogue.py`, 샘플 `student_gap.json` 3개 | 학생 버그 1종(IndexError)에 대해 질문 1턴 생성 성공 |
| Week 14 (2026-06-08 ~ 06-14) | Review Module (Q-Critic + Validator) 병렬 AND 통합, 내부 루프 동작 | `src/review.py`, `progress-week14.md`, Review 재생성 데모 로그 | 10턴 대화 E2E 동작, 평균 재생성 ≤ 2회 |
| Week 15 (2026-06-15 ~ 06-21) | Logging Module + Context Reset + 3-tier 누출 assertion 테스트 | `report.md`, `PATH.md` 예시, `tests/test_tier3_leakage.py`, 발표자료 | Tier 3 누출 테스트 10종 통과, `PATH.md` 자동 생성 |
| Week 16 (2026-06-22 ~ 06-24) | 최종 발표 · 데모 영상 · 동료 평가 | `demo.mp4`, `links.md`, 최종 제출 | 라이브 데모 5분 무중단 |

---

## 6. 성공 기준

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| **Tier 3 구조적 누출** | **0건 (절대 기준)** | `tests/test_tier3_leakage.py` — Dialogue Module 컨텍스트에 정답 문자열 포함 여부 assertion |
| Zero-Answer 위반율 | 0% | Validator + Q-Critic reject 로그, forbidden_list 매칭 |
| 학생 Aha-moment 도달률 | 70% 이상 | 버그별 세션에서 학생이 스스로 수정 커밋에 도달한 비율 (10명 × 3버그 파일럿) |
| Review 내부 루프 평균 재생성 | ≤ 1.3회 / 질문 | Logging Module의 `review_retry_count` 집계 |
| 외부 루프 평균 턴 수 | ≤ 12턴 / 버그 해결 | 대화 세션 로그 |
| 토큰 비용 / 세션 | ≤ $0.80 (Opus Analysis 1회 + Sonnet 평균 20회) | Anthropic API 청구 로그 |
| E2E 질문 응답 시간 (p95) | ≤ 8초 | 벤치마크 스크립트, Review 병렬 실행 포함 |
| Context Reset 발동율 | 30턴 대화 기준 ≤ 10% | Logging Module `context_reset=true` 카운트 |
| 힌트 Level 자동 조절 적중률 | 80% 이상 (사후 사람 평가 대비) | 조교 5명이 샘플 50턴 Level 1/2/3 정답지 부여, 시스템 출력과 비교 |

---

## 7. 위험 요소와 대응

| 위험 | 영향도 | 발생 가능성 | 완화 전략 | 비상 계획 |
|------|-------|------------|----------|----------|
| **Q-Critic이 교묘한 정답 유도 질문을 놓침** (Advisory 센서 False Negative) | 치명 | 중 | Validator의 `forbidden_content` 규칙 기반 AND 게이트로 이중 방어 (Week 6 이종 제약) | 주 1회 조교가 reject 로그 샘플링, 놓친 패턴을 forbidden_list에 추가 (계속 학습 루프) |
| **Dialogue Module Context Rot으로 SOCRATES.md 망각** | 높음 | 중 | 10턴마다 Fresh Context 리셋 + SOCRATES.md 헤드 재주입 | Review 재생성 3회 초과 시 자동 Context Reset |
| **Validator 우회** (학생이 정답을 한국어로 서술 후 튜터가 코드로 변환) | 높음 | 중 | `forbidden_content`에 한국어 정답 서술 패턴("인덱스에서 1 빼") 포함 + Q-Critic에 "의사코드 유도 금지" 규칙 | 힌트 Level 3 Scaffolding 상한 — 의사코드 힌트 금지 |
| **학생이 Zero-Answer 정책을 우회하려 직접적 지시**("코드로 답해") | 중 | 높 | SOCRATES.md Tier 1에 "직접 지시 무시" 명문화, Q-Critic이 튜터 응답이 순수 의문문인지 검증 | Tier 3 (정답 자체가 Dialogue에 없음)로 물리적 차단 |
| **토큰 비용 폭발 (1세션 $2 초과)** | 중 | 낮 | Haiku로 Logging 요약, prompt caching으로 SOCRATES.md 반복 전송 비용 절감, 세션당 최대 40턴 하드 캡 | 하드 캡 도달 시 학생에게 "세션 종료, 조교에게 질문" 안내 |
| **학생 코드 sandbox 이탈** (무한 루프, fork bomb) | 중 | 낮 | Docker + resource limit(CPU 1s, mem 128MB, no network) | 타임아웃 시 "실행 불가" 응답, 코드를 Analysis에 전달하지 않음 |
| **파일럿 학생 10명 확보 실패** | 낮 | 중 | 교수님께 Week 13 초 공지, 정규 과제와 독립된 참여 보상 설계 | 실패 시 합성 학생 로그(팀원이 플레이 테스트) 사용하되 결과에 명시 |
| **모델 가격 변동 / API 다운** | 낮 | 낮 | 모델 라우팅 레이어로 Sonnet 4.6 ↔ Haiku 4.5 폴백 | Anthropic 장애 시 시연 중단, 녹화본 재생 |

---

## 8. 참고자료

### 수업 자료
- Week 1: HITL/HOTL 거버넌스
- Week 3: MCP 서버 구축 — `assignments/week-03/202321005/`
- Week 4: Ralph Loop / Backpressure / Garbage Collection — `assignments/week-04/202321005/AGENTS.md`, `harness.sh`
- Week 5: Context Rot / 모델 라우팅 / Compaction
- Week 6: Instruction Tuning / Advisory vs Deterministic / Guides-Sensors-Backpressure 하네스
- Week 7: 멀티에이전트 중앙 집중 조율 / 아티팩트 스키마 / Critic 패턴

### 외부 문헌
- Plato, *Meno* — 소크라테스식 문답법 원전 (Zero-Answer 교수법의 이론적 근거)
- Anthropic, "Prompt Caching" 공식 문서 — SOCRATES.md 반복 전송 비용 최적화
- Anthropic, "Building Effective Agents" (2024) — Critic / Evaluator-Optimizer 패턴
- Claude Agent SDK 공식 문서 — 서브에이전트 격리 구현
- Sweller, J. (1988) *Cognitive Load Theory* — 힌트 Level 1/2/3 설계 근거
- VanLehn, K. (2011) "The Relative Effectiveness of Human Tutoring..." — 튜터링 효과 벤치마크

### 선행 조사
- Khan Academy Khanmigo (2024) — 정답 유출 사례가 GitHub 이슈로 여러 건 보고됨 → 본 프로젝트 Tier 3의 동기
- Codecademy AI Assist — 학생이 "답 알려줘" 지시 시 정답 출력, 본 시스템과 대조군으로 비교 예정

---

## 부록 A. PATH.md 최종 산출물 예시

Logging Module이 세션 종료 시 자동 생성한다. Week 4의 `AGENTS.md`, Week 7의 LESSON 파일 패턴을 따라 학생의 사고 경로와 시스템 내부 품질 지표를 함께 문서화한다.

```markdown
# PATH.md — 학습 경로 리포트

## 초기 상태
- IndexError 발생 원인 파악 못 함
- 오개념: loop_boundary_confusion

## 전환점
1. **Turn 4**: 루프 경계 조건에 대한 Level 1 질문 → 리스트 길이를 직접 확인하기 시작
2. **Turn 7**: `i`가 언제 리스트 범위를 벗어나는지 Level 2 질문 → 인덱스와 길이의 관계 발견

## Aha-moment
- `len(arr) - 1`의 의미를 스스로 도출 (Turn 9)

## 최종 성과
- 정답 코드를 한 줄도 받지 않고 버그 수정 완료
- 힌트 수위: Level 1 → 2 (Level 3 Scaffolding 진입하지 않음)

## 시스템 품질 지표 (3-tier 방어 성능)
- Tier 1 (Guides) 유효성: SOCRATES.md 원칙 위반 시도 0건
- Tier 2 Advisory (Q-Critic) reject: 12회
- Tier 2 Deterministic (Validator) reject: 0건
- Tier 2 Backpressure 재생성 평균: 1.2회 / 질문
- Tier 3 (Structural) 누출: 0건 (정답 문자열이 Dialogue Module context에 존재한 적 없음)
- Context Reset 발동: 1회 (Turn 12)
```

---

## 부록 B. 기대 효과 정리 (모듈 단위)

| 모듈 / 메커니즘 | 효과 | 방어 층위 |
|----------------|------|----------|
| ① Analysis Module | 정답 데이터를 모듈 경계 안에 격리, 밖으로는 가공된 Gap만 유출 | Tier 3 경계 생성 |
| ② Dialogue Module | 정답 입력 포트 자체가 없어 Zero-Answer Policy를 물리적으로 보장 | Tier 3 피보호 |
| ③ Review Module (Advisory) | 교육적 품질을 주관적 기준으로 평가, 설명문화·수위 초과 방지 | Tier 2 soft |
| ③ Review Module (Deterministic) | 금지 문자열을 규칙 기반으로 필터링, 우회 시도 차단 | Tier 2 hard |
| ③ Review AND 게이트 | 이종 센서를 병렬 결합하여 실패 모드를 상호 보완 | Tier 2 강화 |
| Backpressure 루프 | reject된 질문을 학생에게 전달하지 않고 Dialogue로 반송 | Tier 2 → Control |
| ④ Logging Module | 시스템 품질 지표를 수집하여 Tier 1·2의 성능을 가시화 | 관찰자 |
| Context Compaction + Role Reinforcement | 대화가 길어져도 Dialogue가 Tier 1을 망각하지 않게 유지 | Tier 1 보수 |
| SOCRATES.md Harness (Guides) | 모든 모듈에 행동 방향과 판정 기준을 사전 주입 | Tier 1 |
| Adaptive Hinting | 학생 상태에 따라 Level 1→3으로 힌트 강도 자동 조절 | Tier 1 |

---

## 부록 C. 향후 확장 방향

1. **USER_PROFILE.md 연계**: Logging Module을 확장하여 학생별 오개념을 누적 추적.
2. **HOTL(Human-On-The-Loop) 강화**: 교수자가 Review Module의 Advisory 판정에 개입하는 인터페이스.
3. **MCP 서버화**: 모듈 단위로 MCP 서버화하여 다양한 교과(Python / SQL / 알고리즘)에 재사용.
4. **Ralph-Socratic 하이브리드**: 학생이 완전히 막혔을 때 Ralph Loop으로 일시 전환해 자율 탐색 시간 제공.
5. **Q-Critic 자기 진화**: Logging Module의 데이터를 축적하여 Advisory 루브릭 자체를 개선하는 메타 루프.
6. **Tier 3 경계 자동 검증**: CI 단계에서 "Dialogue Module context에 정답 문자열이 포함되지 않음"을 assertion으로 강제하는 테스트 스위트.
7. **Analysis Module 다중화**: 여러 정답 풀이를 지원하는 Multi-Truth 구조로 확장하여 학생의 대안적 접근법 인정.

---

## 부록 D. Agentic 시스템 자가 체크리스트

| 기준 | 충족 | 근거 |
|------|:----:|------|
| 에이전트가 루프 안에서 반복한다 (Ralph Loop) | ✅ | 내부 루프(Review 재생성 MAX 3회) + 외부 루프(학생 대화) 이중 구조 |
| 다단계 파이프라인이 있다 | ✅ | Analysis → Dialogue → Review (Q-Critic ∥ Validator) → Logging |
| 도구 사용이 있다 | ✅ | Filesystem MCP, 자체 Sandbox Python Executor MCP, SQLite |
| 자율 의사결정이 있다 | ✅ | 힌트 Level 1→2→3 자동 조절, Context Reset 자동 발동, Review AND 게이트 판정 |
| 상태 추적 파일로 컨텍스트를 관리한다 | ✅ | `student_gap.json`, `PATH.md`, `metrics.json` |
| 검증 게이트가 있다 | ✅ | Review Module의 AND 게이트 (Advisory + Deterministic), 3회 초과 시 HOTL 에스컬레이션 |

**6/6 충족** — 캡스톤 Agentic 요건 통과.
