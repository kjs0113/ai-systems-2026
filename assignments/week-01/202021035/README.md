# Codex CLI 설치 및 실행 보고서


## 환경

- OS: Windows
- Node.js Version: v24.14.0
- CLI Tool: Codex CLI

---

## 설치 과정

### 1. Node.js 설치
- Node.js 공식 홈페이지에서 LTS 버전 설치
- 설치 후 아래 명령어로 정상 설치 확인

```bash
node -v
npm -v
```

---

### 2. Codex CLI 설치

```bash
npm install -g @openai/codex
```

---

## 설치 과정에서 발생한 문제

### 1. PowerShell 실행 정책 오류

**문제**
- npm 실행 시 보안 정책으로 인해 실행 차단됨

**해결 방법**

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### 2. 환경 변수 설정 오류

**문제**
- Windows 환경에서 `export` 명령어 사용 → 오류 발생

**원인**
- `export`는 Linux/macOS 전용 명령어

**해결 방법 (CMD 기준)**

```cmd
set OPENAI_API_KEY=your_api_key
```

---

## 실행 및 동작 확인

### Codex 실행

```bash
codex
```

- OpenAI 계정 로그인 진행
- CLI 정상 실행 확인

---

## 실행 테스트

### 입력 명령

```
Hello! 이 디렉토리에 간단한 Python hello world 파일을 만들어줘.
```

---

### 실행 결과

- Codex CLI가 현재 디렉토리를 분석
- `hello.py` 파일 자동 생성

파일 경로:

```
.../test-project/hello.py
```

파일 내용:

```python
print("Hello, world!")
```

---

## 결과 확인

- Python 파일 정상 생성 확인
- CLI를 통한 코드 생성 기능 정상 동작

---

## 디렉토리 구조

```
test-project/
 └── hello.py
```

---

## 결론

Codex CLI는 Node.js 환경에서 간단한 설치 과정만으로 사용할 수 있다.

다만 Windows 환경에서는 PowerShell 보안 정책 및 환경 변수 설정 방식의 차이로 인해  
초기 설정 과정에서 주의가 필요하다.

