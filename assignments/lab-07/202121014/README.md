# Lab-07 멀티에이전트 파이프라인

## 과제 개요

이 과제는 멀티에이전트 구조를 단순한 형태로 설계하고, `Planner -> Coder` 2단계 파이프라인을 실제로 실행 가능한 수준으로 구현하는 것이 목표이다.  
각 에이전트는 JSON 스키마에 맞는 구조화된 출력을 만들고, `pipeline.py`는 두 에이전트를 순서대로 연결한다.

## 파일 설명

- `schemas/planner_output.json`: Planner 출력 스키마
- `schemas/coder_output.json`: Coder 출력 스키마
- `base_agent.py`: 공통 기반 에이전트 클래스
- `planner_agent.py`: 목표를 서브태스크 계획으로 분해하는 Planner
- `coder_agent.py`: 계획을 기반으로 변경 내역을 만드는 Coder
- `pipeline.py`: Planner와 Coder를 연결해 실행하는 스크립트
- `pipeline_design.md`: 5단계 전체 멀티에이전트 설계 문서
- `README.md`: 구현 내용과 실행 방법 정리

## Planner 동작 방식

Planner는 아래 입력을 받는다.

- `objective`
- `codebase_summary`

Planner는 목표를 받아 다음 내용을 포함한 계획을 생성한다.

- `task_id`
- `objective`
- `subtasks`
- `constraints`

기본 fallback 계획은 `researcher -> coder -> qa -> reviewer` 순서로 서브태스크를 만들며, 최소 1개의 coder 태스크를 포함한다.

## Coder 동작 방식

Coder는 Planner가 만든 계획을 입력으로 받는다.  
출력은 `CoderOutput` 형식이며 다음 항목을 포함한다.

- `task_id`
- `changes`
- `test_command`
- `status`

추가로 CLI 연동 구조를 유지하기 위해 `AI_CLI` 환경변수를 읽는다.  
예를 들어 `claude`, `gemini`, `codex` 중 하나를 선택하도록 작성했다.

하지만 현재 환경에서 실제 CLI 호출이 실패하거나 실행 파일이 없으면 프로그램이 중단되지 않고 fallback 결과를 생성한다.

## pipeline.py 실행 방법

아래 명령으로 실행할 수 있다.

```bash
python pipeline.py
```

실행하면 Planner 결과와 Coder 결과가 JSON 형태로 출력된다.

## jsonschema 사용 이유

멀티에이전트 구조에서는 각 단계의 출력 형식이 흔들리면 다음 단계가 불안정해진다.  
그래서 Planner와 Coder 출력에 대해 JSON 스키마를 두고, 기반 클래스에서 검증하도록 했다.

현재 환경에는 `jsonschema` 패키지가 없을 수 있으므로, 코드에서는 아래 원칙을 사용했다.

- 패키지가 있으면 `jsonschema.validate`를 사용
- 패키지가 없으면 필수 필드 중심의 fallback 검증 수행

이렇게 하면 제출 환경이 단순해도 파이프라인이 멈추지 않는다.

## API 키 없을 때 fallback 방식

이 과제는 API 키가 없어도 동작해야 한다.  
따라서 다음과 같이 fallback 경로를 제공한다.

- `ANTHROPIC_API_KEY`가 없어도 Planner는 자동 계획 생성
- 실제 AI CLI(`claude`, `gemini`, `codex`)가 없어도 Coder는 시뮬레이션 결과 생성
- subprocess 실패 시에도 `status`, `changes`, `test_command`를 포함한 결과 반환

## 멀티에이전트 장점

- Planner가 큰 목표를 구조화해 주므로 구현 단계가 단순해진다.
- Coder는 계획에 맞춰 변경 내역과 테스트 명령을 정리할 수 있다.
- 구조화된 출력 덕분에 다음 단계가 예측 가능해진다.
- 이후 Researcher, QA, Reviewer를 추가하기 쉬운 형태다.

## 향후 확장 과제

- Researcher 에이전트를 실제로 구현해 관련 파일 탐색 자동화
- QA 에이전트를 추가해 테스트 결과를 다시 Planner에 전달
- Reviewer 에이전트를 추가해 문서 품질과 제출 상태 자동 점검
- 실제 Claude API 또는 로컬 CLI 응답을 파싱해 더 정교한 Coder 결과 생성
- 스키마 검증 실패 시 자동 복구 루프 추가
