# [Week 12] 텔레메트리 및 LLM-as-Judge 과제 보고서

**학번:** 202321006  
**이름:** 김준서  
**제출일:** 2026-05-19

## 1. Lab 11: 텔레메트리 (Telemetry)

### 1.1 OpenTelemetry Trace 구현
에이전트 루프(`agent.run`)와 하위 작업들(`model.call`, `tool.invoke`, `acceptance.test`, `judge.evaluate`)에 대한 span 구조를 설계하고 구현하였습니다.
- **구현 파일:** `telemetry.py`
- **표준 Attribute 적용:** `run.id`, `task.id`, `agent.role`, `model.name`, `tool.name`, `gate.result`, `artifact.path` 등 7개 필수 속성 포함.

### 1.2 Event Store (.events.jsonl)
Agent OS Runtime 형식을 준수하는 append-only event store를 구현하였습니다.
- **기록된 이벤트:** `run.started`, `tool.invoke`, `tool.result`, `test.result`, `judge.result`, `run.closed`
- **Replay 결과:** `replay_snapshot.json`을 통해 각 run의 최종 상태, 사용 모델, 도구 실행 결과 등을 재구성할 수 있음을 확인하였습니다.

### 1.3 대시보드 구성 (4-Panel 시뮬레이션)
- **패널 1 (Success Rate):** 전체 10건 중 4건 Pass (40%), 5건 Revise, 1건 Fail.
- **패널 2 (Token p95):** 시뮬레이션 상 모델 호출 당 평균 2,500 토큰 소비로 p95 산출.
- **패널 3 (Judge vs Test):** Deterministic Test는 9건 통과했으나, Judge에 의해 5건이 Revise로 분류됨 (디자인 품질 보완).
- **패널 4 (Failure Reasons):** `tests_failed` (1건), `low_judge_score` (5건).

---

## 2. Lab 12: LLM-as-Judge

### 2.1 LLMJudge 구현
- **형식:** Strict JSON 출력 (`scores`, `overall`, `verdict`, `rationale`)
- **평가 코드:** `judge.py`
- **게이트 정책:** Deterministic Test(통과 여부)와 Probabilistic Judge(점수 >= 7.0)를 결합한 `gate_policy` 적용.

### 2.2 상관관계 분석 결과
인간 평가자(Gold Set)와 LLM Judge 점수 간의 상관관계를 분석하였습니다.
- **분석 도구:** `correlate.py`
- **상관계수:** 
  - **Spearman Rho:** 1.0 (매우 높은 순위 상관관계)
  - **Pearson R:** 0.9962 (강한 선형 상관관계)
- **n:** 10, **p-value:** 0.0 (통계적으로 유의미함)

### 2.3 Judge Bias 및 대응 전략
- **관찰된 Bias:** **Length Bias** (답변/코드의 길이가 길어질수록 점수가 미세하게 높게 측정되는 경향 확인).
- **대응 방안:** Rubric에 '간결성(Conciseness)' 항목을 추가하고, 코드 길이에 대한 정규화(Normalization) 로직을 평가 프롬프트에 명시하여 대응함.

---

## 3. 결론 및 고찰
이번 과제를 통해 에이전틱 워크플로우에서 **관측성(Observability)**이 단순한 로그 기록을 넘어, 시스템의 신뢰성을 담보하는 핵심 장치임을 배웠습니다. 특히 `LLM-as-Judge`를 `Deterministic Gate`와 결합하여 운영함으로써, 코드의 기능적 정확성뿐만 아니라 유지보수성과 설계 의도까지 자동화된 파이프라인에서 검증할 수 있었습니다. 상관관계 분석을 통해 Judge의 신뢰도를 정량적으로 확인하고, 발견된 Bias를 Prompt 엔지니어링으로 보완하는 과정이 실무적인 운영 관점에서 매우 유익했습니다.
