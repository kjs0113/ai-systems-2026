# Lab-02 HOTL 거버넌스 에이전트

## 과제 개요

이 과제는 anthropic Python SDK를 활용할 수 있는 간단한 AI 코딩 에이전트를 만들고, 그 위에 HOTL(Human-On-The-Loop) 거버넌스 레이어와 감사 로그 시스템을 결합하는 것이 목표이다.  
핵심은 위험도가 높은 액션을 자동으로 통제하고, 모든 판단 결과를 추적 가능한 형태로 남기는 것이다.

## 파일 설명

- `governance.py`: 4단계 위험 분류와 승인 정책, 감사 로그 기록 기능을 담당한다.
- `agent.py`: 사용자 입력을 받고, Claude 제안 또는 fallback 액션을 거버넌스에 통과시킨 뒤 결과를 출력한다.
- `test_governance.py`: 정책 동작을 검증하는 pytest 테스트 파일이다.
- `audit.jsonl`: JSON Lines 형식의 감사 로그 예시 파일이다.
- `README.md`: 설계 결정, 실행 방법, 테스트 방법을 정리한 문서이다.

## governance.py 설계 결정

`ActionRisk` Enum은 다음 4단계를 사용한다.

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

정책 결정은 아래 원칙을 따른다.

- `LOW`, `MEDIUM`: 자동 승인
- `HIGH`: 사람 승인(HOTL) 필요
- `CRITICAL`: 자동 거부

`log_action()` 함수는 모든 액션을 `audit.jsonl`에 한 줄씩 기록한다. 각 줄은 독립된 JSON 객체이며 `timestamp`, `action`, `risk`, `approved`, `reason` 필드를 포함한다.

## agent.py 동작 방식

에이전트는 사용자 요청을 입력받고, 가능하면 `ANTHROPIC_API_KEY`를 사용해 Claude에게 짧은 액션 제안을 받는다.  
하지만 API 키가 없거나 SDK 호출이 실패하면 프로그램이 종료되지 않고, 사용자의 입력값 자체를 액션으로 사용한다.

그 다음 단순한 키워드 기반 규칙으로 위험도를 분류한다.

- `rm -rf`, `format`, `shutdown` → `CRITICAL`
- `delete`, `remove`, `drop database` → `HIGH`
- `write`, `modify`, `update`, `create`, `save` → `MEDIUM`
- `read`, `list`, `show`, `print`, `파일 읽기` → `LOW`

## HIGH에서 HOTL이 어떻게 동작하는지

`HIGH` 위험 액션은 `require_human_approval()`에서 사용자에게 `yes/no` 입력을 요청한다.  
사용자가 `yes`를 입력한 경우에만 승인되며, 승인 여부는 즉시 `audit.jsonl`에 기록된다.

## CRITICAL이 자동 거부되는 이유

`CRITICAL` 액션은 시스템 손상이나 돌이킬 수 없는 삭제를 일으킬 수 있으므로, 사람 승인 절차 없이도 즉시 차단한다.  
예를 들어 `rm -rf`, `format`, `shutdown` 같은 액션은 실수 한 번으로 큰 피해를 만들 수 있기 때문에 과제 요구사항에 맞게 무조건 자동 거부하도록 설계했다.

## audit.jsonl이 JSON Lines 형식인 이유

JSON Lines 형식은 로그 한 줄이 하나의 JSON 객체이므로, 다음 장점이 있다.

- 줄 단위 append가 쉽다.
- 나중에 파싱과 필터링이 쉽다.
- 로그 일부가 손상되어도 다른 줄은 계속 읽을 수 있다.
- 감사 기록을 순서대로 저장하기에 적합하다.

## 테스트 방법

아래 명령으로 정책 테스트를 실행한다.

```bash
pytest test_governance.py -v
```

포함된 테스트:

- `test_critical_always_denied`
- `test_low_auto_approved`
- `test_audit_log_is_jsonl`

## 실행 방법

에이전트 실행:

```bash
python agent.py
```

종료:

```text
exit
```

## 확인 결과

- `HIGH` 위험 액션은 승인 입력을 요구한다.
- `CRITICAL` 위험 액션은 자동 거부된다.
- 모든 액션은 `audit.jsonl`에 JSON Lines 형식으로 기록된다.
- 테스트 파일에는 최소 3개의 정책 테스트가 포함되어 있다.


