# PROMPT.md — Ralph Loop Task Specifications

이 파일은 `harness.sh`가 파싱하여 루프 태스크를 로드하는 명세 파일입니다.
각 태스크는 `### TASK:` 헤더, `CMD:` 실행 명령, `VALIDATE:` 검증 명령으로 구성됩니다.

---

## Task Design Philosophy

Ralph 루프는 **탐색(Explore) → 적용(Apply) → 검증(Prove)** 사이클로 동작합니다.
각 태스크는 독립적으로 실패/성공 가능하며, 실패 시 AGENTS.md에 학습이 기록됩니다.
3회 연속 실패 시 *stuck-detection* 로직이 태스크를 더 작은 단위로 분할합니다.

---

### TASK: optimize_sort
**목표:** 비효율적인 버블 정렬 구현을 Python의 내장 정렬로 대체하고,
입력 크기 1000에서 실행 시간이 개선되었는지 확인합니다.

CMD: python3 autoresearch.py --task optimize_sort --budget 20
VALIDATE: python3 -c "import json,sys; d=json.load(open('loop_results.json')); sys.exit(0 if d.get('optimize_sort',{}).get('improved') else 1)"
REPAIR: bash tasks/broken/repair_optimize_sort.sh

**성공 조건:**
- 최적화된 함수가 원본보다 빠를 것 (`improved: true`)
- `loop_results.json`에 결과가 저장될 것

**실패 시나리오 (학습 대상):**
- `autoresearch.py` 미존재 → 파일 생성 후 재시도
- JSON 키 불일치 → 출력 형식 수정 후 재시도

---

### TASK: fix_divide_zero
**목표:** `tasks/calculator.py`의 0 나누기 버그를 탐지하고 패치합니다.
패치 후 단위 테스트(`tasks/test_calculator.py`)가 통과해야 합니다.

CMD: python3 tasks/test_calculator.py
VALIDATE: python3 -c "import ast,sys; src=open('tasks/calculator.py').read(); assert 'ZeroDivisionError' in src or 'if b == 0' in src; print('Guard detected.')"
REPAIR: bash tasks/broken/repair_fix_divide_zero.sh

**성공 조건:**
- 0 나누기 방어 분기(`if divisor == 0`) 삽입
- 단위 테스트 전부 통과

**실패 시나리오 (학습 대상):**
- `tasks/` 디렉터리 미존재 → 하위 태스크로 분할하여 디렉터리 생성
- 테스트 파일 구문 오류 → 구문 수정 후 재시도

---

### TASK: generate_metrics_report
**목표:** 루프 실행이 완료된 후 `metrics.csv`를 읽어
통계 요약(평균 소요 시간, 성공률, 실패 패턴)을 `report.txt`로 출력합니다.

CMD: python3 -c "import csv,statistics,sys,os; rows=list(csv.DictReader(open('metrics.csv'))); durations=[float(r['duration_sec']) for r in rows if r['duration_sec']]; successes=sum(1 for r in rows if r['status']=='SUCCESS'); total=len(rows); report=f'=== Metrics Report ===\nTotal iterations : {total}\nSuccesses        : {successes}\nFailures         : {total-successes}\nSuccess rate     : {successes/total*100:.1f}%\nAvg duration     : {statistics.mean(durations):.2f}s\nMax duration     : {max(durations):.2f}s\nMin duration     : {min(durations):.2f}s\n'; print(report); open('report.txt','w').write(report)"
VALIDATE: test -f report.txt && grep -q 'Success rate' report.txt

**성공 조건:**
- `report.txt`가 생성될 것
- `Success rate` 항목이 포함될 것

**실패 시나리오 (학습 대상):**
- `metrics.csv` 헤더 불일치 → CSV 재생성 후 재시도
- 빈 파일 처리 예외 → 조건 분기 추가 후 재시도

---

## Bonus Tasks (선택적)

### TASK: autoresearch_demo
**목표:** `autoresearch.py`의 시간 예산 기반 최적화 루프를 30초 예산으로 실행합니다.

CMD: python3 autoresearch.py --task all --budget 30
VALIDATE: test -f loop_results.json

### TASK: worktree_analysis
**목표:** 현재 git worktree 격리 상태를 분석하고 결과를 `worktree_report.txt`에 기록합니다.

CMD: bash -c "git worktree list > worktree_report.txt 2>&1 || echo 'Not a git repo' > worktree_report.txt"
VALIDATE: test -f worktree_report.txt
