# Lab-05 컨텍스트 관리 실습 

## 개요

본 프로젝트는 Lab-05 과제 요구사항에 맞춰 컨텍스트 관리 기능을 구현한 실습입니다.
`python main.py` 실행 시 전체 데모가 자동으로 진행되며, 다음 기능을 확인할 수 있습니다.

-  토큰 사용량 추적
- Rolling Window 기반 컨텍스트 압축
- 실행 상태 저장 및 복원
- `claude-progress.txt` 자동 생성

---

## 파일 구성

- `main.py` : 전체 데모 실행 및 통합 테스트 진행
- `token_counter.py` : 입력/출력 토큰 수 및 예상 비용 계산
- `context_manager.py` : 오래된 메시지를 압축하는 Rolling Window 기능 구현
- `state_tracker.py` : 실행 진행 상태 저장 및 복원 기능 구현
- `progress_state.json` : 실행 중 임시 상태 저장 파일
- `claude-progress.txt` : 실행 완료 후 생성되는 최종 결과 보고서

---

## 실행 방법

Python 3 환경에서 아래 명령어를 실행합니다.

```bash
python main.py
```

---

## 실행 시 동작 과정

`python main.py` 실행 시 다음 과정이 자동으로 수행됩니다.

1. 20턴 이상의 데모 대화를 순차적으로 처리합니다.
2. 각 메시지마다 토큰 사용량을 계산합니다.
3. 활성 컨텍스트 크기를 초과하면 오래된 메시지를 압축합니다.
4. 압축 발생 시 로그를 콘솔에 출력합니다.
5. 진행 상태를 `progress_state.json` 파일에 지속적으로 저장합니다.
6. 실행 완료 후 `claude-progress.txt` 파일을 생성합니다.
7. 최종 토큰 사용량 및 비용 보고서를 출력합니다.

---

## Ctrl + C 중단 후 복원 기능

본 프로젝트는 실행 중단 후 이어서 실행하는 기능을 지원합니다.

1. `python main.py` 실행
2. 실행 도중 `Ctrl + C` 입력
3. 다시 `python main.py` 실행

이후 `progress_state.json` 파일을 불러와 이전 작업 위치부터 이어서 실행합니다.

---

## Rolling Window 동작 방식

컨텍스트 관리 모듈은 최신 메시지만 활성 컨텍스트에 유지합니다.
메시지 수가 많아질 경우 오래된 메시지는 요약 또는 압축되어 새로운 메시지를 위한 공간을 확보합니다.

콘솔 출력 예시:

```text
[rolling-window] compression #7: compressed 2 messages, active_context=7
```

---

## 토큰 및 비용 출력 예시

실행 종료 후 아래와 같은 결과가 출력됩니다.

```text
Token Usage Report
- model: gpt-4o-mini
- input_tokens: 713
- output_tokens: 840
- total_tokens: 1553
- estimated_cost_usd: $0.000611
```

---

## 생성 파일 결과

실행 완료 후 다음 파일이 생성됩니다.

- `claude-progress.txt` : 최종 결과 보고서, 활성 컨텍스트, 압축 로그 저장
- `progress_state.json` : 완료 후 초기화되어 다음 실행 시 새롭게 시작 가능
