# Docs-Code Drift Detector

**한 줄 요약**: README, docstring, API 문서의 **타입 및 파라미터** 정의를 실제 코드(AST 기반)와 비교하여 불일치를 탐지하고, **문서 수정 PR**을 자동 생성하는 멀티에이전트 시스템 (코드 수정은 추천만 제공)

**학번 / 이름**: 202321010 / 박진우

---

## 1. 문제 정의

### 1.1 현재 상황

소프트웨어 개발에서 문서와 코드 간 불일치(drift)는 매우 빈번하게 발생하는 문제이다. 특히 API를 제공하는 라이브러리나 SDK의 경우, 문서는 사용자와의 계약 역할을 수행하기 때문에 정확성이 매우 중요하다.

예를 들어 다음과 같은 상황이 발생할 수 있다.

* 문서: `parse_json(str) -> dict`
* 실제 코드: `list` 반환

이러한 불일치는 개발 과정에서 자연스럽게 발생한다. 코드가 변경될 때마다 문서를 동시에 수정해야 하지만, 실제 개발 환경에서는 기능 구현과 버그 수정이 우선시되기 때문에 문서 업데이트는 종종 누락된다.

이 문제의 주요 원인은 다음과 같다.

* 코드 변경 시 문서 업데이트는 수동으로 이루어짐
* 코드 리뷰 과정에서 문서 검증은 거의 수행되지 않음
* README 및 docstring은 테스트 대상이 아님

이로 인해 다음과 같은 비효율이 발생한다.

* 문서 업데이트 누락
* API 오용 증가
* 협업 비용 증가
* 문서 신뢰도 저하

결과적으로 문서는 **검증되지 않은 계약 상태**로 유지되며, 이는 개발자 경험과 시스템 안정성 모두에 부정적인 영향을 미친다.

---

### 1.2 왜 에이전틱 접근인가

이 문제는 단순한 규칙 기반 스크립트나 단일 LLM 호출로 해결하기 어렵다. 그 이유는 문제 자체가 여러 단계의 추론과 판단을 요구하기 때문이다.

1. **문서 해석 문제**
   자연어로 작성된 문서는 표현 방식이 다양하며, 동일한 의미를 서로 다른 방식으로 기술할 수 있다. 따라서 이를 구조화된 스펙으로 변환하는 과정이 필요하다.

2. **코드 의미 추론 문제**
   코드에는 조건문, 반복문, 함수 호출 등 다양한 흐름 제어 구조가 존재한다. 단순 AST 분석만으로는 실제 반환값이나 동작을 완전히 파악하기 어렵기 때문에 추가적인 heuristic 또는 실행 기반 검증이 필요하다.

3. **판단 문제 (핵심)**
   문서와 코드 간 불일치가 발견되었을 때, 어느 쪽이 올바른지 판단해야 한다. 이는 단순 비교가 아닌 정책 기반 의사결정 문제이다.

따라서 이 문제는 여러 단계의 분석과 판단이 연결된 **에이전틱 시스템 구조**로 접근하는 것이 적합하다.

---

### 1.3 Governance Rule (핵심 추가)

Drift 발견 시 수정 방향을 결정하기 위해 다음과 같은 정책을 적용한다.

1. 테스트가 존재하는 경우 → **코드 기준**
2. typing annotation 존재 → **코드 우선**
3. 명시적 docstring 계약 존재 → **문서 우선 고려**
4. 불확실한 경우 → **PR 생성 + Human 승인**

이러한 규칙은 자동화 과정에서 발생할 수 있는 잘못된 수정 리스크를 줄이고, 시스템의 신뢰도를 유지하는 데 중요한 역할을 한다.

---

### 1.4 수업 개념 적용 (확장)

* **Week 1 (AI 시스템 패러다임 전환 / HOTL)**
  단일 모델 호출이 아닌, 분석·판단·수정이 분리된 에이전틱 구조를 사용하며, 최종 PR은 인간 승인(Human-in-the-loop)을 통해 반영된다.

* **Week 2 (Governance-as-Code)**
  drift 발생 시 코드 vs 문서 중 어떤 것을 기준으로 수정할지 정책(Governance Rule)으로 명시하여 자동 의사결정을 제어한다.

* **Week 3 (MCP 아키텍처)**
  GitHub, 파일 시스템, pytest 등을 외부 도구로 연결하여 실제 실행 가능한 파이프라인을 구성한다.

* **Week 4 (루프 패러다임)**
  detect → fix → validate 과정을 반복하여 단일 판단이 아닌 점진적 개선 방식으로 정확도를 향상시킨다.

* **Week 5 (컨텍스트 관리)**
  함수 단위로 분석을 수행하여 context overflow를 방지하고, 불필요한 정보 누적을 제거한다.

* **Week 6 (인스트럭션 튜닝)**
  문서 구조화 및 drift 판단 시 일관된 결과를 얻기 위해 프롬프트 구조를 정형화한다.

* **Week 7 (멀티에이전트 SDLC)**
  Doc / Code / Drift / Fix / QA / PR 역할을 분리하여 협업형 에이전트 시스템으로 설계한다.

---


### 1.5 목표 사용자 / 사용 맥락

**대상 사용자**

* API 및 SDK 개발자
* 오픈소스 유지보수자
* 내부 플랫폼 팀

**사용 시점**

* Pull Request 생성 시 자동 검사
* 릴리즈 전 검증 단계
* 주기적 코드베이스 점검

---

## 2. 시스템 설계

### 2.1 에이전트 구성

| 에이전트           | 역할          | 입력                  | 출력                |
| -------------- | ----------- | ------------------- | ----------------- |
| Doc Analyzer   | 문서 구조화      | README, docstring   | doc_spec.json     |
| Code Analyzer  | 코드 구조 분석    | source code         | code_spec.json    |
| Drift Detector | 불일치 탐지 및 분류 | doc_spec, code_spec | drift_report.json |
| Fix Generator  | 수정 제안 생성    | drift_report        | patch.diff        |
| QA Agent       | 수정 검증       | patch, repo         | qa_result.json    |
| PR Agent       | PR 생성       | patch               | GitHub PR         |

---

### 2.2 Drift 유형 분류 (현실적 범위 축소)

**자동 탐지 범위 (In Scope)**

* **Type mismatch**: 반환 타입 불일치 (예: 문서 `dict` vs 코드 `list`)
* **Parameter mismatch**: 입력 파라미터 정의 불일치 (개수, 타입, 기본값)
* **Return structure mismatch**: 구조적 차이 (예: `dict` vs `list of dict`)

**제외 범위 (Out of Scope)**

* **Semantic mismatch**: 동작 의미 차이 (예: "returns sorted list"인데 실제로 정렬 안 함)
  - **제외 이유**: AST로 탐지 불가능, LLM도 확신 어려움 → false positive 폭발 위험
  - 이는 테스트 코드가 담당해야 할 영역

이러한 명확한 범위 설정을 통해 **precision을 유지**하면서 실용적인 시스템을 구축한다.

---

### 2.3 파이프라인

        ┌──────────────────────────────┐
        │ README / docstring / API docs│
        └──────────────┬───────────────┘
                       ▼
               ┌──────────────┐
               │ Doc Analyzer │
               └──────┬───────┘
                      │ doc_spec.json

        ┌──────────────────────────────┐
        │      Python Source Code      │
        └──────────────┬───────────────┘
                       ▼
               ┌──────────────┐
               │ Code Analyzer│
               └──────┬───────┘
                      │ code_spec.json
                      ▼

               ┌──────────────┐
               │ Drift Detector│
               └──────┬───────┘
                      │ drift_report.json
                      ▼

               ┌──────────────┐
               │ Governance   │
               │ (policy +    │
               │ confidence)  │
               └──────┬───────┘
                      │ decision
                      ▼

               ┌──────────────┐
               │ Fix Generator│
               └──────┬───────┘
                      │ patch.diff
                      ▼

               ┌──────────────┐
               │ QA Loop      │◄──────────────┐
               │ (pytest, max 5)              │
               └──────┬───────┘               │
                      │ qa_result.json        │
                      ▼                       │
               ┌──────────────┐               │
               │ PR Agent     │               │
               └──────┬───────┘               │
                      │ GitHub PR             │
                      ▼                       │
               ┌──────────────┐               │
               │ Human Approval│──────────────┘
               └──────────────┘
---

### 2.4 Code Analyzer 설계

Code Analyzer는 시스템의 핵심 구성 요소 중 하나로, 다음과 같은 방식으로 동작한다.

* Python AST 기반 구조 분석을 통해 함수 정의 및 반환 구문 추출
* typing annotation을 활용하여 예상 반환 타입 추론
* 여러 return path를 분석하여 실제 반환값 분포 파악
* 필요 시 간단한 실행 기반 검증을 통해 동적 동작 확인

LLM은 보조적으로 활용되며, 주요 분석은 구조 기반으로 수행된다.

---

### 2.5 상태 전달 예시

```json
{
  "function": "parse_json",
  "drift_type": "return_type_mismatch",
  "doc_return": "dict",
  "code_return": "list",
  "confidence": 0.91,
  "evidence": {
    "doc": "returns dict",
    "code": "list detected in all return paths"
  }
}
```

---

### 2.6 Fix 전략 (현실적 접근)

**자동 수정 (PR 생성)**

* **문서 수정만** 자동화
* README, docstring, API 문서 업데이트
* 예: `returns: dict` → `returns: list`

**코드 수정 (추천만 제공)**

* 코드 수정은 **자동화하지 않음** (unsafe)
* 대신 PR 코멘트로 "코드 수정 제안" 텍스트만 제공
* 예시 코멘트:
  ```
  Alternative: 코드를 문서에 맞추려면
  - Line 42: `return result` → `return {"data": result}`
  ```

**이유**

* 코드 자동 수정은 동작 변경 위험이 높음
* 문서 수정은 상대적으로 안전 (테스트 통과 여부로 검증 가능)
* Human approval 단계에서 코드 수정 여부는 개발자가 판단

---

### 2.7 QA Loop 종료 조건

* pytest 통과 시 종료
* 최대 반복 횟수 도달 시 종료

---

### 2.8 PR Agent 기능

* PR 제목 자동 생성
* 변경 사항 요약 작성
* 영향 범위 설명
* drift 근거 포함

---

## 3. 기술 스택

* Python 3.12 (AST 분석)
* pytest (테스트)
* Docker (격리 실행)
* GitHub Actions (CI 자동화)
* LLM (문서 해석 및 의미 비교)

---

## 4. 평가 방법

**테스트셋 구성**

* 의도적으로 **type/parameter drift**를 포함한 함수 30개
  - Type mismatch: 10개
  - Parameter mismatch: 10개
  - Return structure mismatch: 10개
* 실제 오픈소스 프로젝트 1~2개 (시간 허용 시)

**평가 지표**

* **Drift detection precision** (핵심): 탐지된 drift 중 실제 drift 비율
* **Drift detection recall**: 실제 drift 중 탐지된 비율
* **False positive rate**: 전체 함수 중 잘못 탐지된 비율
* **PR 생성 성공률**: 생성된 PR이 pytest를 통과한 비율
* **코드 수정 추천 정확도**: 제공된 코드 수정 제안의 유효성 (수동 평가)

---

## 5. 성공 기준 (현실적 목표)

**정확도 (축소된 범위 기준)**

* **Precision ≥ 70%** (type/parameter mismatch만 대상)
  - 기존 80% 목표는 semantic drift 포함 시 달성 어려움
  - 명확한 범위로 축소하여 현실적 목표 설정
* **False Positive ≤ 15%** (전체 함수 기준)
* **PR 생성 성공률 ≥ 85%** (pytest 통과)

**성능 및 비용**

* 실행 시간 ≤ 120초 (함수 30개 기준)
* 비용 ≤ $0.50 (프로젝트당)

**추가 지표**

* 코드 수정 추천 정확도 ≥ 60% (수동 평가)

---

## 6. 위험 요소 및 대응 (현실적 평가)

### 주요 리스크 3가지

**1. Semantic mismatch 미탐지 (HIGH)**

* **문제**: 문서에 "returns sorted list"라고 했는데 실제 정렬 안 함
* **왜 못 잡나**: AST로 정렬 로직 추론 불가능, LLM도 확신 못함
* **대응**: **아예 범위에서 제외** (이건 테스트가 담당해야 함)

**2. 코드 자동 수정의 위험성 (HIGH)**

* **문제**: 자동 코드 수정은 동작 변경 → 프로덕션 위험
* **대응**: **코드는 추천만, 문서만 자동 수정**

**3. Precision 목표 달성 어려움 (MEDIUM)**

* **문제**: 문서 ambiguity, dynamic code, heuristic error
* **대응**: **범위 축소** (type/parameter만) + **precision 목표 하향** (70%)

### 기타 리스크

* **컨텍스트 초과** → function 단위 분리
* **비용 증가** → 모델 라우팅 + 캐싱
* **LLM 오판** → QA loop + human approval

### 프로젝트를 살리는 전략

**BEFORE (원래 계획)**
* semantic drift 포함
* 코드 수정 자동화
* multi-agent full pipeline

**AFTER (현실적 축소)**
* **Type/parameter mismatch만**
* **문서 수정만 자동**, 코드는 추천
* 핵심 pipeline만


---

## 7. 수업 개념 매핑 (구체화)

| 주차     | 개념                 | 적용 방식                                                |
| ------ | ------------------ | ---------------------------------------------------- |
| Week 1 | AI 시스템 패러다임 전환     | 단일 모델이 아닌 에이전트 기반 파이프라인 구조                           |
| Week 1 | HOTL               | 자동 생성 PR은 human 승인 후 merge                           |
| Week 2 | Governance-as-Code | 코드 vs 문서 수정 방향을 정책으로 명시 + 범위 제한 (semantic 제외)     |
| Week 3 | MCP                | GitHub, pytest, filesystem을 도구로 연결                   |
| Week 4 | Loop               | QA Loop를 통한 반복적 검증 (최대 5회)                          |
| Week 5 | Context 관리         | 함수 단위 분석으로 context 분리                               |
| Week 6 | Instruction tuning | 문서 파싱 및 drift 판단 프롬프트 최적화                           |
| Week 7 | Multi-agent SDLC   | 역할 기반 에이전트 분리 구조 (Doc/Code/Drift/Fix/QA/PR)        |

---

## 9. 프로젝트 강점 (냉정 평가)

이 프로젝트의 **차별점**:

* **문제 정의 명확**: 실제 DevOps 문제를 다룸
* **Governance rule**: 수정 방향 결정 정책이 있음 (차별점)
* **Pipeline 구조**: 각 단계가 명확히 분리됨
* **Evaluation metric**: 정량적 평가 기준 설정
* **실용성**: 실제 CI/CD에 통합 가능

→ 즉, **"연구 + 시스템 설계 둘 다 잡은 주제"**

---

## 8. 개발 일정 (현실적 조정)

**기존 계획의 문제점**

* Analyzer만 1주에 끝내기 → 무리
* Fix + QA + PR까지 → 과부하

**조정된 일정**

* **Week 13**: Code Analyzer + Doc Analyzer 구현
  - AST 기반 타입 추출
  - 문서 파싱 및 구조화
* **Week 14**: Drift Detector (type/parameter만)
  - 불일치 탐지 로직
  - Governance rule 적용
* **Week 15**: Fix Generator + PR Agent
  - 문서 수정 자동화
  - 코드 수정 추천 텍스트 생성
  - GitHub PR 생성
* **Week 16**: Polish + Evaluation
  - 테스트셋 평가
  - 메트릭 측정
  - 발표 준비

**버퍼 전략**: Week 16에 통합 작업 포함하여 여유 확보

## 10. 참고자료

### 1. 코드 분석 및 시스템 구현

* Python Software Foundation.
  *ast — Abstract Syntax Trees.*
  https://docs.python.org/3/library/ast.html
  → Python 코드 구조 분석 및 정적 분석 구현에 활용

* pytest Documentation.
  https://docs.pytest.org
  → patch 적용 후 동작 검증을 위한 테스트 프레임워크

* GitHub.
  *GitHub Actions Documentation.*
  https://docs.github.com/actions
  → CI 기반 자동 PR 생성 및 검증 파이프라인 구축

---

### 2. LLM 및 코드 이해

* Chen, M. et al. (2021).
  *Evaluating Large Language Models Trained on Code.*
  → LLM의 코드 이해 및 생성 능력 분석

* Yao, S. et al. (2022).
  *ReAct: Synergizing Reasoning and Acting in Language Models.*
  → reasoning + action 기반 에이전트 구조 설계 참고

* OpenAI.
  *GPT-4 Technical Report.*
  → LLM의 추론 능력 및 코드 처리 성능 근거

---

### 3. 문서-코드 관계 및 문제 배경

* Parnin, C. et al. (2013).
  *Crowd Documentation: Exploring the Coverage and the Dynamics of API Discussions on Stack Overflow.*
  → API 문서 불일치 및 유지 문제 사례 연구

* Zhong, Z. et al. (2020).
  *Are API Documentation and Code Always Consistent?*
  → 문서-코드 불일치(drift) 문제에 대한 실증 연구

---

### 4. 산업 사례 및 유사 시스템

* GitHub.
  *Dependabot Documentation.*
  https://docs.github.com/code-security/dependabot
  → 자동 코드 변경 제안 시스템의 대표 사례

* Microsoft.
  *Pyright Static Type Checker.*
  https://github.com/microsoft/pyright
  → 정적 분석 기반 코드 검증 도구

---

### 5. 시스템 설계 및 아키텍처 참고

* Anthropic. (2024).
  *Building Effective Agents.*
  → multi-agent 구조 및 evaluator-optimizer 패턴 설계

* Anthropic.
  *Prompt Caching Documentation.*
  → 반복 컨텍스트 최적화 전략

---

### 6. 프로젝트 설계 동기

* 오픈소스 프로젝트 GitHub Issues 사례
  → 문서-코드 불일치로 인한 버그 및 사용자 혼란 사례 다수 보고
