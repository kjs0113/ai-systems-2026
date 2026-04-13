#!/usr/bin/env bash
set -euo pipefail

MAX_ITER=${MAX_ITER:-5}
SLEEP_SEC=${SLEEP_SEC:-2}

PROMPT_FILE="PROMPT.md"
LOG_FILE="harness.log"
PASS_MARKER="DONE.md"

NODE_EXE="/mnt/c/Program Files/nodejs/node.exe"
CODEX_JS="C:/Users/whkgu/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"
PYTHON_EXE="/mnt/c/Users/whkgu/AppData/Local/Microsoft/WindowsApps/python.exe"

export PYTHONIOENCODING=utf-8
export LANG=C.UTF-8

if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "init"
fi

rm -f "$LOG_FILE" "$PASS_MARKER"

iter=0
echo "[START LOOP]" | tee "$LOG_FILE"

while [ $iter -lt $MAX_ITER ]; do
  iter=$((iter + 1))
  echo "=== ITER $iter ===" | tee -a "$LOG_FILE"

  if [ $iter -gt 1 ]; then
    echo "[harness] backpressure: sleeping ${SLEEP_SEC}s" | tee -a "$LOG_FILE"
    sleep "$SLEEP_SEC"
  fi

  # ITER 1: 1차 실패 상태 주입
  if [ $iter -eq 1 ]; then
    cat > src/calculator.py <<'PY'
def divide(a: float, b: float) -> float:
    return a / b  # ZeroDivisionError 미처리

def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
PY
    echo "[harness] injected fail state 1 (ZeroDivisionError)" | tee -a "$LOG_FILE"
  fi

  # ITER 2: 2차 실패 상태 주입 후 일부러 codex 없이 실패만 기록
  if [ $iter -eq 2 ]; then
    cat > src/calculator.py <<'PY'
def divide(a: float, b: float) -> float:
    if b == 0:
        raise Exception("error")  # wrong exception on purpose
    return a / b

def fibonacci(n: int) -> int:
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
PY
    echo "[harness] injected fail state 2 (wrong exception)" | tee -a "$LOG_FILE"
    echo "[harness] forcing failure without codex" | tee -a "$LOG_FILE"
    "$PYTHON_EXE" -m pytest tests/ -q --tb=no 2>&1 | tee -a "$LOG_FILE"
    echo "RETRY..." | tee -a "$LOG_FILE"
    continue
  fi

  echo "[harness] running tests before codex" | tee -a "$LOG_FILE"
  if "$PYTHON_EXE" -m pytest tests/ -q --tb=no 2>&1 | tee -a "$LOG_FILE"; then
    echo "[harness] already passing before codex" | tee -a "$LOG_FILE"
    echo "TEST PASS" | tee -a "$LOG_FILE"
    exit 0
  fi

  echo "[harness] codex fixing..." | tee -a "$LOG_FILE"
  "$NODE_EXE" "$CODEX_JS" exec \
    "Read PROMPT.md and AGENTS.md, then fix the code in src/ to pass all tests. Follow PROMPT.md exactly." \
    2>&1 | tee -a "$LOG_FILE"

  if [ -f "$PASS_MARKER" ]; then
    echo "DONE FOUND" | tee -a "$LOG_FILE"
    exit 0
  fi

  echo "[harness] running tests after codex" | tee -a "$LOG_FILE"
  if "$PYTHON_EXE" -m pytest tests/ -q --tb=no 2>&1 | tee -a "$LOG_FILE"; then
    echo "TEST PASS" | tee -a "$LOG_FILE"
    exit 0
  fi

  echo "RETRY..." | tee -a "$LOG_FILE"
done

echo "FAILED" | tee -a "$LOG_FILE"
exit 1