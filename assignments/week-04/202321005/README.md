# Lab 04: Ralph 루프 구현

**학번**: 202321005  
**제출 경로**: `assignments/week-04/202321005/`  
**과제 설명**: 코스 문서 `src/content/docs/labs/lab-04.mdx` 및 `weeks/week-04.mdx`와 동일 목표

## 디렉터리 구조

```
202321005/
├── harness.sh              # Ralph 하네스 (백프레셔 + GC + stuck split + 메트릭)
├── PROMPT.md               # 역할 / 제약 / 태스크 3개 이상
├── AGENTS.md               # 루프가 append-only로 누적한 실패·성공 학습
├── loop_log.txt            # 터미널 캡처 (실패 → 학습 → 재시도 흔적)
├── backpressure.py         # stall 감지 + autoresearch(가산) + RLM 축약(가산)
├── README.md               # 본 문서
├── requirements.txt
├── pytest.ini
├── src/calculator.py       # 에이전트가 수리한 최종 구현
├── tests/                  # 단계별 pytest (수정 금지)
├── scripts/mock_agent.py   # MOCK_AGENT=1 일 때 결정론적 대체 에이전트
├── state/
│   ├── checkpoints/        # GC용 마지막 녹색 스냅샷 (task0…task3)
│   ├── error_logs/         # 실패 시 패키징된 pytest 로그
│   └── injected_prompt.txt # PROMPT.md + AGENTS.md (+ shard) 병합본
├── metrics/
│   ├── loop_metrics.csv
│   └── loop_metrics.json
├── experiments/            # RLM 장문 실험 스크립트 (가산)
└── reports/
    └── loop_worktree_analysis.md  # `/loop` worktree 격리 분석 (가산)
```

## 실행 방법

```bash
cd assignments/week-04/202321005
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 결정론적 시연 (API 불필요)
rm -rf state metrics loop_log.txt
PATH="$PWD/.venv/bin:$PATH" MOCK_AGENT=1 bash harness.sh

# 실제 Claude Code CLI (환경에 claude 가 있을 때)
# PATH="$PWD/.venv/bin:$PATH" MOCK_AGENT=0 AI_CLI=claude bash harness.sh
```

성공 시 세 단계 테스트가 모두 통과하고 `loop_log.txt`에 실패·stuck split·성공 흐름이 남는다.

## 하네스 설계 결정

1. **백프레셔**  
   - **pytest**를 단계별로 좁혀 실행해 “컴파일러/테스트가 거부하면 진행 불가” 패턴을 재현한다.  
   - 연속 실패에 **선형 증가 sleep**(`BACKOFF_BASE_SEC × consecutive_failures`)을 걸어 API·CPU 폭주를 완만하게 만든다.  
   - `backpressure.py stall-check`는 로그에 동일 실패 패턴이 과도하게 반복될 때 **추가 8s 쿨다운**을 넣는다(초반 9회 이터레이션은 스킵해 오탐을 줄임).

2. **가비지 컬렉션(GC)**  
   - 실패 후 `src/calculator.py`를 **마지막 녹색 체크포인트**(`state/checkpoints/task{n-1}.py`)로 복구한다.  
   - `scratch/`, `__pycache__`, `.pytest_cache`를 정리한다.  
   - 선택적으로 `USE_GIT_GC=1`이면 `git checkout -- src/calculator.py`도 호출한다.

3. **Stuck split (가산)**  
   - 동일 태스크에서 `STUCK_THRESHOLD`(기본 3)회 연속 실패하면 `state/task_shard.txt`를 생성해 **편집위를 나눈다**(Task 1 예: divide만).  
   - 본 제출의 mock 에이전트는 Task 1에서 **3번 실패 후 shard가 생긴 뒤**에만 패치를 적용해, 로그에 stuck → 재시도 → 성공이 드러나게 했다.

4. **AGENTS.md 누적 → 다음 루프 반영 (평가 포인트)**  
   - 매 실패마다 `AGENTS.md`에 pytest tail과 takeaway를 append한다.  
   - `build_injected_prompt`가 **매 이터레이션** `PROMPT.md` + 전체 `AGENTS.md`(+ shard)를 `state/injected_prompt.txt`로 병합한다.  
   - 라이브 CLI 모드에서는 이 병합본을 에이전트 입력으로 넘겨 **이전 실패 맥락이 다음 호출에 실제로 주입**된다.

5. **에러 로그 패키징**  
   - 실패 시 `state/last_pytest.log`를 `state/error_logs/pytest_<timestamp>.log`로 복사한다.

## Test-time compute scaling과의 연결

- **추론 시점에 반복·검증을 늘리는 것**이 곧 본 루프의 병렬 축이 아닌 **순차 축** 확장이다: 같은 고정 가중치 모델이라도 “한 번에 맞히기” 대신 **실패 신호(테스트)를 받고 행동을 수정**할 기회를 늘린다.  
- **백프레셔**는 무한한 test-time 시도를 **시간·비용 측면에서 유한**하게 만들고, **GC**는 나쁜 궤적을 잘라 **탐색 공간을 다시 열어준다**.  
- **autoresearch**(`backpressure.py::autoresearch_optimize`)는 작은 하이퍼파라미터 탐색에 **고정 시간 예산**을 걸어, “추론 중 탐색”을 미니어처로 보여 준다.

## 가산점 구현 요약

| 항목 | 위치 |
|------|------|
| Autoresearch (고정 시간 예산) | `backpressure.py::autoresearch_optimize`, CLI `autoresearch-demo` |
| Stuck 탐지 + 태스크 분할 | `harness.sh` + `state/task_shard.txt`, mock Task 1 시나리오 |
| 루프 메트릭 CSV/JSON | `metrics/loop_metrics.{csv,json}` |
| `/loop` worktree 분석 | `reports/loop_worktree_analysis.md` |
| RLM식 장문 축약 실험 | `experiments/rlm_chunk_demo.py`, `backpressure.py::rlm_reduce_document` |

### RLM 장문 실험 — 짧은 고찰

전체 문서를 한 번에 읽는 대신 **청크로 나누고**, 키워드(여기서는 “손실”)에 대한 국소 점수로 상위 청크만 이어 붙이는 방식은, 대규모 언어 모델이 사용하는 **분할·읽기·병합** 패턴의 극도로 단순한 대용물이다. 한계는 분명하다: 의미 이해가 아니라 **통계적 필터**에 가깝고, 동의어나 간접 표현에는 약하다. 그럼에도 “장문 → 부분 증거 → 상위 요약”이라는 **추론 시 계산을 늘리는 축**은 test-time scaling 논의와 같은 맥락에 놓을 수 있다.

## 실제 루프 결과 (MOCK_AGENT=1)

- **글로벌 이터레이션**: 10회 만에 종료 (`metrics/loop_metrics.csv` 참고).  
- **Task 1**: 3회 실패 후 stuck split → 4회차에 성공.  
- **Task 2·3**: 각 2회 실패 후 성공(강화된 fib 테스트로 잘못된 점화식 탐지).  
- 상세 터미널 로그: **`loop_log.txt`**.

## 제약·주의

- `tests/`는 수정하지 않는다.  
- `--dangerously-skip-permissions` 류 플래그는 **실습 전용 디렉터리**에서만 사용한다.
