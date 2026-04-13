# Claude Code `/loop` 실행 후 worktree 격리 동작 분석 보고서

**학번**: 202321005  
**환경**: Claude Code 2.1.104, Git 2.34+, Linux 6.8.0  
**실험 일시**: 2026-04-12

---

## 1. 핵심 발견: `/loop`과 worktree는 별개 메커니즘이다

공식 문서와 실험을 통해 확인한 가장 중요한 사실:

- **`/loop`** = 세션 내 **스케줄링** 도구 (cron 기반, 반복 프롬프트 실행)
- **`--worktree` (`-w`)** = **Git worktree 기반 파일시스템 격리** 도구

둘은 독립적이지만 **조합하여** 사용할 수 있다:
```bash
claude --worktree feature-auth   # 격리된 worktree에서 세션 시작
/loop 10m run tests              # 해당 격리 환경 안에서 반복 실행
```

---

## 2. Worktree 격리 실험

### 2.1 실험 설계

본 레포지토리(`ai-systems-2026`, `week03` 브랜치)에서 Git worktree를 수동으로 생성하여 Claude Code의 `--worktree` 플래그가 내부적으로 수행하는 동작을 재현하고 관찰했다.

### 2.2 Worktree 생성

```bash
$ git worktree add .claude/worktrees/test-isolation -b worktree-test-isolation week03
Preparing worktree (new branch 'worktree-test-isolation')
HEAD is now at 26e1dad Week 03: MCP server, gateway, benchmarks, reports
```

**관찰 결과**:
- 경로: `.claude/worktrees/<name>/` — Claude Code가 사용하는 표준 위치
- 브랜치명: `worktree-<name>` 패턴으로 자동 생성
- 기반: 지정한 브랜치(week03)의 HEAD에서 분기

### 2.3 디렉터리 구조 분석

```
.claude/worktrees/test-isolation/
├── .git                    ← 파일(디렉터리가 아님). 메인 repo를 가리키는 포인터
├── assignments/
├── src/
├── README.md
└── ... (전체 tracked 파일 복사본)
```

**`.git` 파일 내용**:
```
gitdir: /raid/home/.../ai-systems-2026/.git/worktrees/test-isolation
```

**메인 repo `.git/worktrees/test-isolation/` 내부**:
```
├── commondir   → "../.."  (objects/refs 공유 경로)
├── gitdir      → worktree의 .git 파일 위치
├── HEAD        → ref: refs/heads/worktree-test-isolation
├── index       → 9,418 bytes (독립 인덱스)
├── logs/       → 독립 reflog
└── refs/       → 독립 ref 저장소
```

### 2.4 격리 검증 — 핵심 실험

**worktree에서 파일 수정 후 메인 브랜치 상태 확인**:

```bash
# Worktree에서 README.md 수정
$ echo "# WORKTREE TEST CHANGE" >> .claude/worktrees/test-isolation/README.md

# Worktree 상태: 변경 감지됨
$ git -C .claude/worktrees/test-isolation diff --stat
 README.md | 1 +
 1 file changed, 1 insertion(+)

# 메인 repo 상태: 변경 없음 ✓
$ git diff --stat README.md
(출력 없음)
```

| 항목 | 메인 repo | Worktree |
|------|-----------|----------|
| HEAD | `ref: refs/heads/week03` | `ref: refs/heads/worktree-test-isolation` |
| 브랜치 | week03 | worktree-test-isolation |
| README.md 변경 | 없음 | 있음 |
| index | 공유 objects, 독립 index | 독립 index |

**결론**: worktree의 변경이 메인 작업 디렉터리에 **전혀 영향을 주지 않음**을 확인.

### 2.5 공유 vs 독립 구성요소

| 구성요소 | 공유 여부 | 설명 |
|----------|-----------|------|
| `.git/objects/` | **공유** | 커밋, 블롭 등 모든 Git 객체는 하나의 저장소 |
| `.git/refs/` | **부분 공유** | 원격 ref는 공유, 로컬 HEAD/ref는 독립 |
| `index` | **독립** | 각 worktree가 자체 스테이징 영역 보유 |
| 작업 파일 | **독립** | 완전히 별도의 파일 복사본 |
| `HEAD` | **독립** | 각 worktree가 다른 브랜치를 checkout 가능 |

### 2.6 정리(Cleanup) 동작

```bash
# 변경사항 복원 후 worktree 제거
$ git worktree remove .claude/worktrees/test-isolation

# Worktree는 삭제되었지만 브랜치는 남아있음
$ git branch --list worktree-test-isolation
  worktree-test-isolation    ← 여전히 존재

# 수동으로 브랜치 삭제 필요
$ git branch -D worktree-test-isolation
Deleted branch worktree-test-isolation (was 26e1dad).
```

**Claude Code의 자동 정리 정책** (공식 문서 기반):
- 변경 없는 worktree → 자동 삭제 (worktree + 브랜치 모두)
- 변경 있는 worktree → 사용자에게 유지/삭제 선택 프롬프트
- 고아 서브에이전트 worktree → `cleanupPeriodDays` 이후 자동 삭제 (미커밋 변경·미푸시 커밋이 없는 경우만)

---

## 3. `/loop` 스케줄링 메커니즘 분석

### 3.1 동작 원리

`/loop`는 세션 내부의 **cron 기반 스케줄러**이다:

```
/loop 5m <prompt>    # 고정 5분 간격
/loop <prompt>       # Claude가 동적으로 간격 결정 (1분~1시간)
/loop                # loop.md 또는 내장 유지보수 프롬프트 실행
```

**스케줄러 특성**:
- 1초마다 due 태스크 확인
- 낮은 우선순위로 큐잉 (사용자 턴 사이에 실행)
- 놓친 간격은 catch-up 없이 1회만 실행
- **7일 자동 만료** — 잊힌 루프의 무한 실행 방지
- 세션당 최대 50개 태스크

### 3.2 `loop.md` 재로딩

- `.claude/loop.md` (프로젝트) > `~/.claude/loop.md` (사용자) 우선순위
- **매 이터레이션마다 재로딩** → 외부에서 수정한 지시가 다음 루프에 즉시 반영
- 25,000 bytes 초과 시 truncate
- 명시적 프롬프트 지정 시 `loop.md` 무시됨

### 3.3 `/loop` + worktree 조합 워크플로

```bash
# 1. 격리 환경 생성
claude --worktree my-refactor

# 2. 해당 세션 안에서 반복 루프 설정
/loop 5m run pytest and fix any failures

# 세션이 .claude/worktrees/my-refactor/에서 실행됨
# 모든 변경은 worktree-my-refactor 브랜치에 격리
# 메인 브랜치는 영향 없음
```

---

## 4. 본 Lab 하네스(`harness.sh`)와의 대비

| 측면 | Claude Code `/loop` + `--worktree` | 본 제출 하네스 |
|------|-------------------------------------|----------------|
| **격리 단위** | Git worktree (OS 수준 디렉터리 격리) | 체크포인트 파일 복원 (`state/checkpoints/task*.py`) |
| **격리 강도** | 전체 파일트리 격리 | 단일 파일(`calculator.py`) 롤백 |
| **백프레셔** | 에이전트가 스스로 CI 실행 (프롬프트에 포함) | pytest 단계별 강제 실행 + sleep 백오프 |
| **학습 누적** | CLAUDE.md / loop.md 재로딩 | `AGENTS.md` + `state/injected_prompt.txt` 병합 |
| **스케줄** | cron 기반 (`--every`, 동적 간격) | while 루프 + 지수적 백오프 sleep |
| **실패 복구** | worktree 삭제 = "통째로 버리기" | `restore_checkpoint` = 마지막 녹색으로 롤백 |
| **만료/종료** | 7일 자동 만료, 세션 종료 시 소멸 | `MAX_GLOBAL_ITER` 하드 리미트 |
| **상태 추적** | 세션 내 컨텍스트 유지 | `state/` 디렉터리 (에러로그, 샤드, 체크포인트) |

### 4.1 GC 전략 비교

**Worktree 방식** (Claude Code):
```
실패 → worktree 통째로 삭제 → 깨끗한 새 worktree 생성
장점: 완전한 격리, 부분 실패의 잔존 상태가 없음
단점: 매번 전체 파일 복사, 디스크 사용량 증가
```

**체크포인트 방식** (본 하네스):
```
실패 → src/calculator.py를 마지막 녹색 스냅샷으로 교체
장점: 빠른 복원, 최소 디스크 사용
단점: 다른 파일의 부수 변경은 GC 대상이 아님
```

본 하네스의 `restore_checkpoint`는 사실상 **단일 파일에 대한 미니 worktree**와 동일한 역할을 수행한다.

### 4.2 누적 학습 전달 비교

**Claude Code**:
- `CLAUDE.md`: 프로젝트 수준 지속 지침 → 세션 시작 시 자동 로딩
- `loop.md`: 루프 전용 지시 → 매 이터레이션마다 재로딩
- 세션 내 컨텍스트: 이전 턴의 결과가 자연스럽게 유지

**본 하네스**:
- `AGENTS.md`: 실패/성공마다 append → `state/injected_prompt.txt`로 병합
- 매 이터레이션마다 전체 AGENTS.md를 에이전트 입력에 포함
- **명시적** 학습 전달 (Claude Code의 암묵적 컨텍스트 유지와 대조)

---

## 5. 설계적 교훈

### 5.1 격리 수준의 트레이드오프

```
강한 격리 (worktree)  ←——————→  약한 격리 (체크포인트)
  안전하지만 무거움                가볍지만 부수효과 잔존 가능
```

- Ralph 루프에서 **에이전트가 예측 불가능한 파일을 건드릴 수 있을 때** → worktree가 안전
- **수정 대상이 명확하고 한정적일 때** → 체크포인트가 효율적

### 5.2 스케줄링의 의미

`/loop`의 cron 기반 스케줄링은 "일정 간격으로 상태를 점검하는" 패턴에 적합하다. 반면 본 하네스의 while 루프는 "실패 시 즉시 재시도"하는 패턴이다. Ralph 원리에서:

- **`/loop`** → 모니터링·유지보수 (CI 확인, PR 리뷰, 코드 정리)
- **while 루프** → 수렴 지향 태스크 (테스트 통과까지 반복)

### 5.3 공통 원리

둘 다 **비결정적 에이전트를 결정론적 외곽 루프**로 감싸는 Ralph 철학을 공유한다:
1. 에이전트 실행 → 2. 검증(테스트/CI) → 3. 실패 시 상태 복원 → 4. 학습 주입 → 1로 복귀

---

## 6. 실험 로그 요약

| 단계 | 명령어 | 관찰 |
|------|--------|------|
| worktree 생성 | `git worktree add .claude/worktrees/test-isolation -b worktree-test-isolation` | 전체 tracked 파일이 복사됨, .git은 포인터 파일 |
| 격리 검증 | worktree에서 README.md 수정 후 메인 `git diff` 확인 | 메인 repo에 변경 없음 ✓ |
| HEAD 분리 | `cat .git/HEAD` vs worktree HEAD | 각각 다른 브랜치 ref를 가리킴 ✓ |
| index 독립성 | 양쪽 index 파일 크기 비교 | 동일 크기지만 독립 파일 (경로 다름) ✓ |
| objects 공유 | `commondir` 내용 확인 | `../..` → 메인 repo objects 공유 ✓ |
| 정리 | `git worktree remove` + `git branch -D` | worktree 삭제 후 브랜치는 수동 삭제 필요 |

---

## 7. 결론

1. **`/loop`과 `--worktree`는 직교하는 두 축**이다. `/loop`은 시간 축(언제 실행할까), `--worktree`는 공간 축(어디서 실행할까)을 제어한다.
2. **Worktree 격리는 OS 수준의 파일시스템 분리**를 제공하며, 실패한 에이전트의 잔존 상태가 메인 브랜치를 오염시키지 않도록 보장한다.
3. 본 Lab의 체크포인트 기반 GC는 worktree의 **경량화된 대안**으로, 수정 대상이 명확할 때 더 효율적이다.
4. 실무에서는 `claude --worktree feature -p "fix the auth bug"` 후 `/loop 5m run tests`로 **격리 + 반복**을 조합하는 것이 가장 안전한 Ralph 패턴이다.

---

## 참고 자료

- Claude Code 공식 문서: Scheduled Tasks, Common Workflows, CLI Reference
- 강의 자료: `src/content/docs/weeks/week-04.mdx`
- 용어집: `src/content/docs/reference/glossary.md`
- 본 실험: `ai-systems-2026` 레포지토리, `week03` 브랜치 기반
