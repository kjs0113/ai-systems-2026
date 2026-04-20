# 실시간 지식 독점 방지 및 협업 넛지 에이전트

**한 줄 요약**: GitHub PR 발생 시 실시간으로 버스 팩터를 계산하여 지식 독점을 감지하고, AI 인터뷰를 통해 설계 맥락을 추출하여 적합한 팀원에게 지식을 분산시키는 능동형 협업 에이전트

**학번 / 이름**: 202321006 / 김준서

**GitHub 저장소**: https://github.com/kjs0113

---

## 1. 문제 정의

### 1.1 현재 상황

소프트웨어 팀에서 지식 독점 문제는 퇴사 이후에야 발견된다. 이미 늦은 시점이다.

- 특정 모듈을 오직 한 명만 이해하고 있어, 그 사람이 없으면 수정·디버깅이 불가능
- 코드에 왜 이렇게 짰는지 이유가 남아있지 않아 신규 입사자가 파악하는 데 수개월 소요
- 기존 해결책("문서 써주세요")은 귀찮아서 아무도 안 함
- 결국 퇴사 통보를 받고 나서야 공백의 크기를 실감하는 패닉 상황 반복

**핵심 문제**: 지식 독점은 퇴사 전부터 PR 하나하나가 쌓이면서 만들어진다. 그런데 아무도 그 순간을 감지하지 않는다.

### 1.2 왜 에이전틱 접근인가

기존 도구(GitHub Insights, SonarQube)는 사후에 통계를 보여줄 뿐, 지식 독점이 생기는 순간에 개입하지 않는다. 이 시스템은 PR이 올라오는 순간 실시간으로 개입한다.

- PR 감지 → 위험도 분석 → 인터뷰 → 지식 공유 → 게이트 통제까지 자율적으로 처리
- 인터뷰 답변이 모호하면 재질문하는 Ralph Loop가 핵심
- 사람이 "문서를 쓰는 고통" 대신 "질문에 답하는 자연스러운 대화"로 지식을 추출
- Week 1 HOTL: 최적 리뷰어 추천과 병합 통제는 사람이 최종 결정

### 1.3 목표 사용자 / 사용 맥락

- **사용자**: 개발팀 전체 (작성자, 리뷰어, 팀장)
- **사용 시점**: PR이 올라올 때마다 자동 실행
- **기대 결과**: 버스 팩터 1인 모듈 40% 감소, 리뷰 다양성 증가, 온보딩 속도 향상

---

## 2. 제안 시스템 설계

### 2.1 에이전트 구성

| 에이전트 | 역할 | 입력 아티팩트 | 출력 아티팩트 | 사용 모델 |
|----------|------|--------------|--------------|-----------|
| StreamWatcher | PR 이벤트 실시간 감지 | GitHub Webhook | pr_event.json | Haiku 4.5 |
| RiskEvaluator | 지식 편중도 실시간 분석 | pr_event.json + knowledge_graph.json | risk_score.json | Sonnet 4.6 |
| Interviewer | 설계 맥락(Rationale) 추출 | risk_score.json | rationale.json | Sonnet 4.6 |
| NudgeManager | 협업 유도 및 지식 배포 | rationale.json | nudge_comment.md | Sonnet 4.6 |
| GateKeeper | 병합 통제 및 검증 | nudge_comment.md | merge_decision.json | Sonnet 4.6 |

### 2.2 파이프라인 아키텍처

```
[GitHub PR 생성] ← 실시간 트리거 (Webhook)
        │
        ▼
┌──────────────┐
│ StreamWatcher│  PR 작성자, 변경 파일, 코드 diff 파악
│  (Haiku)    │  → pr_event.json
└──────────────┘
        │
        ▼
┌──────────────┐
│ RiskEvaluator│  Knowledge Graph에서 해당 모듈 의존도 계산
│  (Sonnet)   │  "이 모듈 준서님 외 이해도 0%" → 위험 점수 산출
│              │  → risk_score.json
└──────────────┘
        │
        ▼  (위험 점수 70점 이상일 때만 실행)
┌──────────────┐◀─────────────────────────┐
│  Interviewer │  PR 코멘트로 질문 투척     │ Ralph Loop
│  (Sonnet)   │  "왜 이렇게 설계하셨나요?" │ 답변 모호하면
│              │  → rationale.json         │ 재질문 (최대 3회)
└──────────────┘                           │
        │ 고품질 답변 확보                  │
        ▼                                  │
┌──────────────┐                           │
│ NudgeManager │  최적 리뷰어 추천          │
│  (Sonnet)   │  지식 요약본 PR 코멘트 게시 │
│              │  → nudge_comment.md        │
└──────────────┘                           │
        │                                  │
        ▼                                  │
┌──────────────┐                           │
│  GateKeeper  │  지식 공유 완료됐는가? ────┘
│  (Sonnet)   │  미흡하면 → 재인터뷰 요청
│              │  위험 점수 80점 이상 +
│              │  공유 미흡 → Merge 제한
└──────────────┘
        │ 통과
        ▼
  [PR 병합 승인 + Knowledge Graph 업데이트]
  사람 최종 결정 (HOTL 게이트)
```

### 2.3 핵심 시나리오: The "Nudge" Flow

```
1. 김준서가 1년간 혼자 관리하던 Core_Auth 모듈에 PR 올림
        ↓
2. RiskEvaluator: "이 모듈 준서님 외 이해도 0%" → 위험 점수 심각
        ↓
3. Interviewer가 PR 코멘트로 질문:
   "준서님, 왜 기존 라이브러리 대신 커스텀 함수를 쓰셨나요?"
        ↓
4. 준서: "빠르니까요" (모호한 답변)
        ↓
5. Ralph Loop 가동:
   "성능 벤치마크 수치나 참고 레퍼런스가 있다면 공유해주세요."
        ↓
6. 추출된 정보 + 코드 요약 → 가민님 리뷰어 지목
   "가민님, 이 기회에 Auth 모듈 설계 의도를 파악해보세요!"
        ↓
7. GateKeeper: 지식 공유 완료 확인 → 병합 승인
```

### 2.4 Knowledge Graph 구조

```json
{
  "nodes": [
    { "id": "user:kim", "type": "person", "name": "김준서" },
    { "id": "module:auth", "type": "module", "path": "src/auth/" }
  ],
  "edges": [
    { "from": "user:kim", "to": "module:auth",
      "relation": "sole_owner", "knowledge_score": 0.98,
      "last_updated": "2026-04-20" }
  ],
  "bus_factor": {
    "module:auth": { "score": 1, "risk": "critical" }
  }
}
```

### 2.5 MCP 도구 / 외부 연동

- **GitHub MCP** — PR 이벤트 감지, 코멘트 자동 게시, Merge 통제
- **Filesystem MCP** — Knowledge Graph 파일 읽기/업데이트
- **Slack MCP** (선택) — 위험 점수 80점 이상 시 팀장 알림

### 2.6 상태 추적 / 핸드오프

```
pr_event.json → risk_score.json → rationale.json → nudge_comment.md → merge_decision.json
```

PR이 수백 개 쌓여도 Knowledge Graph를 실시간 업데이트하여 Context Rot을 방지한다 (Week 5).

---

## 3. 기술 스택

| 범주 | 선택 | 근거 |
|------|------|------|
| LLM | Haiku 4.5 (StreamWatcher), Sonnet 4.6 (나머지) | 비용 최적화 |
| 그래프 | NetworkX (Python) | Knowledge Graph 실시간 업데이트 |
| 트리거 | GitHub Webhook | PR 발생 즉시 실행 |
| 프레임워크 | Claude Code + Python Custom Agents | `.claude/agents/` 활용 |
| 언어 | Python 3.12 | GitHub API 연동 용이 |
| 배포 | GitHub Actions | PR 이벤트 트리거 |

---

## 4. 수업 기법 적용 매핑

| 주차 | 기법 | 적용 방식 |
|------|------|----------|
| Week 1 | HOTL 거버넌스 | 리뷰어 추천과 최종 Merge 결정은 사람이 함 |
| Week 3 | MCP 서버 | GitHub MCP로 PR 감지·코멘트 게시·Merge 통제 |
| Week 4 | Ralph Loop | Interviewer가 모호한 답변에 재질문 (최대 3회) — "집요한 인터뷰어" |
| Week 5 | Context Rot 방지 | PR마다 Knowledge Graph 실시간 업데이트, 상태 파일로 컨텍스트 관리 |
| Week 6 | CLAUDE.md 튜닝 | "위험 점수 80점 이상은 Merge 불가", "인터뷰 질문은 비공격적으로" |
| Week 7 | 게이트드 파이프라인 | 지식 공유 미흡 시 GateKeeper가 Merge 제한 |

---

## 5. 개발 일정

| 주차 | 마일스톤 | 산출물 |
|------|---------|--------|
| Week 13 | StreamWatcher + RiskEvaluator 구현, Webhook 연동 테스트 | stream_watcher.py, risk_evaluator.py |
| Week 14 | Interviewer + Ralph Loop 구현, 시나리오 E2E 테스트 | 넛지 플로우 동작 데모 영상 |
| Week 15 | NudgeManager + GateKeeper 통합, Knowledge Graph 실시간 업데이트 | report.md, links.md |
| Week 16 | 최종 발표 준비, 데모 영상 녹화 | links.md (데모 영상 URL), 최종 제출 |

---

## 6. 성공 기준

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 버스 팩터 1 모듈 감소율 | 40% 이상 | 프로젝트 시작 전후 비교 |
| 리뷰 다양성 증가 | 특정 인물 리뷰 집중도 30% 감소 | PR 리뷰어 분포 분석 |
| 인터뷰 재질문 횟수 | 평균 1.5회 이하 | Ralph Loop 로그 분석 |
| 온보딩 속도 향상 | 모듈 파악 시간 50% 단축 | 신규 입사자 테스트 |
| 토큰 비용 / PR 1건 | $0.05 이하 | API 청구 로그 |

---

## 7. 위험 요소와 대응

| 위험 | 영향도 | 대응 전략 |
|------|--------|----------|
| 개발자가 인터뷰 질문을 귀찮아함 | 높음 | 질문 최소화 (핵심 1~2개만), 비공격적 톤 유지 (CLAUDE.md) |
| 오탐으로 인한 불필요한 인터뷰 | 중간 | 위험 점수 임계값 조정, 최근 6개월 커밋 가중치 |
| Merge 제한으로 개발 속도 저하 | 높음 | 위험 점수 80점 이상만 제한, 팀장 긴급 승인 옵션 제공 |
| Knowledge Graph 실시간 업데이트 부하 | 중간 | 변경된 모듈만 증분 업데이트 |
| 인터뷰 내용 개인정보 포함 | 낮음 | CLAUDE.md에 민감 정보 필터링 지침 명시 |

---

## 8. 참고자료

- Week 1: HITL/HOTL 거버넌스
- Week 3: MCP 서버 설계
- Week 4: Ralph Loop 패러다임
- Week 5: Context Rot 방지
- Week 6: CLAUDE.md 인스트럭션 튜닝
- Week 7: 멀티에이전트 SDLC, 게이트드 파이프라인
- Tornhill, A. (2015). *Your Code as a Crime Scene*
- Ferreira et al. (2019). *Measuring Bus Factor in Software Projects*
