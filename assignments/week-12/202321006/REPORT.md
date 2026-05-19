# [Week 12] 텔레메트리 및 LLM-as-Judge 과제 보고서

**학번:** 202321006  
**이름:** 김준서  
**제출일:** 2026-05-19

## 1. Lab 11: 텔레메트리 (Telemetry)

### 1.1 OpenTelemetry Trace 구현
에이전트 루프(`agent.run`)와 하위 작업들(`model.call`, `tool.invoke` 등)에 대한 span 구조를 설계하고 구현하였습니다.
- **구현 파일:** `telemetry.py`
- **표준 Attribute 적용:** `run.id`, `task.id`, `agent.role`, `model.name`, `tool.name`, `gate.result`, `artifact.path`

### 1.2 Event Store (.events.jsonl)
Agent OS Runtime 형식을 준수하는 append-only event store를 구현하였습니다.
- **기록된 이벤트:** `run.started`, `tool.invoke`, `tool.result`, `test.result`, `judge.result`, `run.closed`
- **Replay 결과:** `replay_snapshot.json`을 통해 최종 상태 및 비용(토큰 사용량) 확인 완료

### 1.3 대시보드 구성 (4-Panel)
- [ ] 패널 1: 모델별 성공률
- [ ] 패널 2: 역할별 토큰 사용량 (p95)
- [ ] 패널 3: Judge 점수 vs Test 통과율 비교
- [ ] 패널 4: 주요 실패 원인 분석

---

## 2. Lab 12: LLM-as-Judge

### 2.1 LLMJudge 구현
- **형식:** Strict JSON 출력 (`scores`, `overall`, `verdict`, `rationale`)
- **평가 코드:** `judge.py`

### 2.2 상관관계 분석 결과
인간 평가자(Gold Set)와 LLM Judge 점수 간의 상관관계를 분석하였습니다.
- **분석 도구:** `correlate.py`
- **상관계수 (Spearman/Pearson):** TODO
- **n:** 10, **p-value:** TODO

### 2.3 Judge Bias 및 대응 전략
- **관찰된 Bias:** (예: Length Bias - 답변이 길수록 점수가 높게 나옴)
- **대응 방안:** (예: Rubric에 간결성 항목 추가 및 프롬프트 튜닝)

---

## 3. 결론 및 고찰
(과제 수행 과정에서의 교훈 및 에이전트 운영 관점에서의 관측성 중요성 기술)
