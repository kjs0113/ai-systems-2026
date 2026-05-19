# Lab-03 FastMCP 서버 구현

## 과제 개요

이 과제는 FastMCP 기반 MCP 서버를 직접 구성하고, MCP의 핵심 프리미티브인 Tool, Resource, Prompt를 모두 포함한 서버를 제출 가능한 형태로 정리하는 것이 목표이다.  
추가로 경로 순회(Path Traversal) 방어와 안전한 subprocess 실행 정책을 포함해 기본 보안 요구사항도 반영했다.

## 파일 설명

- `settings.json`: filesystem, git, custom 서버 등록 설정
- `custom_server.py`: FastMCP 기반 사용자 정의 MCP 서버
- `test_sample.py`: pytest로 실행 가능한 샘플 테스트 3개
- `README.md`: 구현 내용과 실행 방법, 보안 검증 내용 정리

## MCP 3대 프리미티브 설명

MCP 서버는 보통 아래 3가지 프리미티브를 중심으로 기능을 제공한다.

- Tool: 실행 가능한 작업 함수
- Resource: 읽기 전용 데이터 제공
- Prompt: 에이전트가 활용할 프롬프트 템플릿

이번 과제에서는 세 가지를 모두 `custom_server.py`에 등록했다.

## Tool / Resource / Prompt 구현 내용

### Tool

두 개의 Tool을 구현했다.

1. `run_pytest(path: str)`
   - 지정 경로에서 `pytest`를 실행한다.
   - `subprocess.run()`을 사용한다.
   - `timeout=60`을 적용했다.
   - `shell=True`는 사용하지 않았다.
   - 실행 결과는 `stdout`, `stderr`, `returncode`를 문자열로 정리해 반환한다.

2. `count_lines(file_path: str)`
   - 지정 파일의 줄 수를 반환한다.
   - 존재하지 않는 파일이나 허용되지 않은 경로는 안전하게 `ERROR` 문자열을 반환한다.

### Resource

- `project://stats`
  - 현재 프로젝트 경로
  - `.py` 파일 개수
  - 총 Python 라인 수
  를 제공한다.

### Prompt

- `code_review(file_path: str)`
  - 보안 취약점
  - 예외 처리
  - 코드 품질
  - 테스트 가능성
  기준으로 리뷰할 수 있도록 템플릿을 반환한다.

## 실행 방법

서버 직접 실행:

```bash
python custom_server.py
```

테스트 실행:

```bash
pytest test_sample.py -v
```

Inspector 실행 예시:

```bash
npx @modelcontextprotocol/inspector python custom_server.py
```

## Inspector 확인 항목

Inspector에서 아래 항목이 확인되도록 설계했다.

- `tools/list`
  - `run_pytest`
  - `count_lines`
- `resources/list`
  - `project://stats`
- `prompts/list`
  - `code_review`

현재 환경에 FastMCP 패키지가 없으면 실제 MCP 프로토콜 구동 대신 fallback 안내 메시지를 출력하도록 작성했다.  
패키지가 설치된 환경에서는 같은 코드 구조로 서버를 실행할 수 있다.

## 경로 순회 차단 테스트 결과

경로 검증 함수 `_validate_path()`는 현재 파일이 위치한 디렉터리를 기준으로 허용 경로를 제한한다.

예를 들어 아래와 같은 요청은 차단된다.

- `../../etc/passwd`
- `..\\..\\secret.txt`

허용 경로 밖의 파일이나 디렉터리를 가리키면 `ValueError`가 발생하고, Tool 함수는 최종적으로 `ERROR` 문자열을 반환한다.

## subprocess 보안 설명

`run_pytest()`는 `subprocess.run()` 호출 시 리스트 인자를 사용한다.

- `["pytest", str(target), "-v"]`

이 방식은 쉘 해석을 거치지 않으므로 명령어 인젝션 위험을 줄인다.  
또한 `shell=True`를 사용하지 않아 과제의 보안 요구사항을 만족한다.

## 실행 결과

기준 명령은 아래와 같다.

```bash
python custom_server.py
pytest test_sample.py -v
```

예상 결과:

- 서버 실행 시 등록된 Tool / Resource / Prompt 목록 확인 가능
- pytest 실행 시 3개 테스트 통과 가능

## 트러블슈팅 기록

1. 현재 환경에는 `mcp.server.fastmcp` 패키지가 설치되어 있지 않았다.
   - 해결: 실제 FastMCP API 형태를 유지하면서, 패키지가 없을 때는 fallback `FastMCP` 클래스로 안내 메시지를 출력하도록 구성했다.

2. Inspector에서 완전한 MCP 통신을 하려면 실제 FastMCP 패키지가 필요하다.
   - 해결: 코드 구조는 그대로 유지하고, 패키지 설치 환경에서 바로 연결 가능한 형태로 작성했다.

3. 파일 경로 입력은 경로 순회 공격 가능성이 있다.
   - 해결: `_validate_path()`에서 `resolve()` 기준으로 허용 경로 밖 접근을 차단했다.

