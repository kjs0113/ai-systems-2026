#!/usr/bin/env bash
# Ralph harness: backpressure, garbage collection (checkpoint restore), stuck split,
# metrics, error log packaging. MOCK_AGENT=1 uses scripts/mock_agent.py for CI / grading.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

LOG_FILE="${LOG_FILE:-loop_log.txt}"
MOCK_AGENT="${MOCK_AGENT:-1}"
AI_CLI="${AI_CLI:-claude}"
MAX_GLOBAL_ITER="${MAX_GLOBAL_ITER:-48}"
STUCK_THRESHOLD="${STUCK_THRESHOLD:-3}"
BACKOFF_BASE_SEC="${BACKOFF_BASE_SEC:-1}"
METRICS_CSV="${METRICS_CSV:-metrics/loop_metrics.csv}"
METRICS_JSON="${METRICS_JSON:-metrics/loop_metrics.json}"
USE_GIT_GC="${USE_GIT_GC:-0}"

STATE_DIR="$ROOT/state"
CKPT_DIR="$STATE_DIR/checkpoints"
ERR_DIR="$STATE_DIR/error_logs"
mkdir -p "$CKPT_DIR" "$ERR_DIR" metrics scratch

# --- logging ---------------------------------------------------------------
log() {
  # shellcheck disable=SC2329
  echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

# --- state -----------------------------------------------------------------
init_state_json() {
  local p="$STATE_DIR/state.json"
  if [[ ! -f "$p" ]]; then
    printf '%s\n' '{"current_task":1,"failures_on_task":0,"global_iteration":0}' >"$p"
  fi
}

read_state() {
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1],encoding="utf-8")); print(d["current_task"]); print(d["failures_on_task"])' \
    "$STATE_DIR/state.json"
}

write_state() {
  local task="$1" fails="$2" giter="$3"
  printf '{"current_task":%s,"failures_on_task":%s,"global_iteration":%s}\n' \
    "$task" "$fails" "$giter" >"$STATE_DIR/state.json"
}

# --- prompt injection (AGENTS.md must influence the next run) --------------
build_injected_prompt() {
  local out="$STATE_DIR/injected_prompt.txt"
  {
    echo "# Merged prompt for this iteration"
    echo
    cat PROMPT.md
    echo
    echo "## Accumulated learning (AGENTS.md)"
    cat AGENTS.md 2>/dev/null || true
    echo
    if [[ -f "$STATE_DIR/task_shard.txt" ]]; then
      echo "## Stuck-split micro-task (narrow scope)"
      cat "$STATE_DIR/task_shard.txt"
    fi
  } >"$out"
}

# --- backpressure ----------------------------------------------------------
backoff_sleep() {
  local n="$1"
  local sec=$((BACKOFF_BASE_SEC * n))
  log "[harness] backpressure: sleeping ${sec}s (consecutive_failures=${n})"
  sleep "$sec"
}

maybe_stall_backpressure() {
  local gi="${1:-0}"
  if [[ ! -f "$LOG_FILE" ]]; then
    return 0
  fi
  if ((gi < 10)); then
    return 0
  fi
  if python3 backpressure.py stall-check --log "$LOG_FILE" 2>/dev/null; then
    return 0
  fi
  log "[harness] stall-check: possible stall — extra cool-down 8s"
  sleep 8
}

# --- garbage collection ----------------------------------------------------
save_checkpoint() {
  local tag="$1"
  cp -f src/calculator.py "$CKPT_DIR/task${tag}.py"
  log "[harness] GC: saved checkpoint task${tag}.py"
}

restore_checkpoint() {
  local task="$1"
  local prev=$((task - 1))
  if ((prev < 0)); then prev=0; fi
  cp -f "$CKPT_DIR/task${prev}.py" src/calculator.py
  log "[harness] GC: restored src/calculator.py from checkpoint task${prev}.py"
  rm -rf .pytest_cache src/__pycache__ tests/__pycache__ 2>/dev/null || true
  rm -rf scratch/* 2>/dev/null || true
  if [[ "$USE_GIT_GC" == "1" ]] && [[ -d .git ]]; then
    git checkout -- src/calculator.py 2>/dev/null || true
    git clean -fd scratch 2>/dev/null || true
  fi
}

# --- errors packaging ------------------------------------------------------
package_errors() {
  local slug
  slug="$(date +%Y%m%d_%H%M%S)"
  if [[ -f "$STATE_DIR/last_pytest.log" ]]; then
    cp -f "$STATE_DIR/last_pytest.log" "$ERR_DIR/pytest_${slug}.log"
    log "[harness] packaged error log -> state/error_logs/pytest_${slug}.log"
  fi
}

append_agents() {
  local giter="$1" task="$2"
  {
    echo
    echo "## Loop ${giter} — task ${task} failure"
    echo "Timestamp: $(date -Iseconds)"
    echo
    echo "### Pytest tail"
    echo '```text'
    tail -n 80 "$STATE_DIR/last_pytest.log" 2>/dev/null || echo "(no log)"
    echo '```'
    echo
    echo "### Takeaway for next attempt"
    echo "- Re-read failing assertion names and match them to a single function change."
    echo "- Keep edits minimal; do not modify files under tests/."
  } >>AGENTS.md
}

# --- stuck split -----------------------------------------------------------
maybe_stuck_split() {
  local task="$1"
  local fails="$2"
  if ((fails < STUCK_THRESHOLD)); then
    return 0
  fi
  if [[ -f "$STATE_DIR/task_shard.txt" ]]; then
    return 0
  fi
  cat >"$STATE_DIR/task_shard.txt" <<EOF
You are stuck on task ${task}. Work on the **smallest** slice only:
- For task 1: only add a zero check to divide(); leave fibonacci and clamp untouched.
- Run pytest on tests/test_task1_divide.py mentally before editing.
EOF
  log "[harness] STUCK SPLIT activated after ${fails} consecutive failures (task ${task})"
}

clear_shard() {
  rm -f "$STATE_DIR/task_shard.txt"
}

# --- agent runner ----------------------------------------------------------
run_agent() {
  build_injected_prompt
  if [[ "$MOCK_AGENT" == "1" ]]; then
    log "[harness] agent: mock (scripts/mock_agent.py)"
    python3 scripts/mock_agent.py 2>&1 | tee -a "$LOG_FILE"
    return 0
  fi
  log "[harness] agent: ${AI_CLI} (live CLI)"
  case "$AI_CLI" in
    claude)
      # shellcheck disable=SC2094
      claude --print --no-color --dangerously-skip-permissions \
        "$(cat "$STATE_DIR/injected_prompt.txt")" 2>&1 | tee -a "$LOG_FILE"
      ;;
    gemini)
      gemini <"$STATE_DIR/injected_prompt.txt" 2>&1 | tee -a "$LOG_FILE"
      ;;
    codex)
      codex --approval-mode full-auto "$(cat "$STATE_DIR/injected_prompt.txt")" 2>&1 | tee -a "$LOG_FILE"
      ;;
    *)
      log "[harness] unknown AI_CLI=${AI_CLI}"
      return 1
      ;;
  esac
}

# --- tests -----------------------------------------------------------------
pytest_for_task() {
  local task="$1"
  case "$task" in
    1) pytest -q tests/test_task1_divide.py ;;
    2) pytest -q tests/test_task1_divide.py tests/test_task2_fibonacci.py ;;
    3) pytest -q tests/test_task1_divide.py tests/test_task2_fibonacci.py tests/test_task3_clamp.py ;;
    *) return 1 ;;
  esac
}

run_tests_capture() {
  local task="$1"
  set +e
  pytest_for_task "$task" >"$STATE_DIR/last_pytest.log" 2>&1
  local code=$?
  set -e
  return "$code"
}

# --- metrics ---------------------------------------------------------------
approx_tokens() {
  local bytes
  bytes="$(wc -c <"$STATE_DIR/injected_prompt.txt" 2>/dev/null || echo 0)"
  echo $((bytes / 4))
}

record_metrics() {
  local giter="$1" task="$2" passed="$3" elapsed="$4" tok="$5" cf="$6"
  mkdir -p "$(dirname "$METRICS_CSV")"
  if [[ ! -f "$METRICS_CSV" ]]; then
    echo "global_iteration,task,passed,elapsed_sec,tokens_est,consecutive_failures" >"$METRICS_CSV"
  fi
  echo "${giter},${task},${passed},${elapsed},${tok},${cf}" >>"$METRICS_CSV"
  python3 -c "
import json, pathlib, time
path = pathlib.Path('${METRICS_JSON}')
row = {
    'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'global_iteration': int('${giter}'),
    'task': int('${task}'),
    'passed': bool(int('${passed}')),
    'elapsed_sec': float('${elapsed}'),
    'tokens_est': int('${tok}'),
    'consecutive_failures': int('${cf}'),
}
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        data = []
except Exception:
    data = []
data.append(row)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
"
}

# --- optional git snapshot -------------------------------------------------
git_snapshot() {
  [[ "$USE_GIT_GC" == "1" ]] || return 0
  [[ -d .git ]] || return 0
  git add src/calculator.py AGENTS.md PROMPT.md harness.sh 2>/dev/null || true
  git commit -m "checkpoint task snapshot" --allow-empty 2>/dev/null || true
}

# --- main loop -------------------------------------------------------------
main() {
  : >"$LOG_FILE"
  init_state_json
  if [[ ! -f "$CKPT_DIR/task0.py" ]]; then
    save_checkpoint 0
  fi

  log "[harness] Ralph harness start (MOCK_AGENT=${MOCK_AGENT}, STUCK_THRESHOLD=${STUCK_THRESHOLD})"
  log "[harness] Logs: ${LOG_FILE} | metrics: ${METRICS_CSV}"

  local consecutive_failures=0
  local giter=0

  while ((giter < MAX_GLOBAL_ITER)); do
    giter=$((giter + 1))
    local task fails
    mapfile -t _st < <(read_state)
    task="${_st[0]}"
    fails="${_st[1]}"
    write_state "$task" "$fails" "$giter"

    if ((task > 3)); then
      log "[harness] all tasks complete — exiting OK"
      exit 0
    fi

    log "[harness] === global iteration ${giter}/${MAX_GLOBAL_ITER} | task ${task} | failures_on_task=${fails} ==="

    maybe_stall_backpressure "$giter"

    if ((fails >= STUCK_THRESHOLD)); then
      maybe_stuck_split "$task" "$fails"
    fi

    if ((giter > 1)); then
      backoff_sleep "$consecutive_failures"
    fi

    local t0 t1 elapsed tok passed
    t0=$(date +%s.%N)
    run_agent
    t1=$(date +%s.%N)
    elapsed=$(python3 -c "print(round(float('$t1')-float('$t0'),3))")

    if run_tests_capture "$task"; then
      passed=1
      consecutive_failures=0
      tok=$(approx_tokens)
      record_metrics "$giter" "$task" 1 "$elapsed" "$tok" 0
      log "[harness] tests PASSED for task ${task}"
      save_checkpoint "$task"
      clear_shard
      git_snapshot
      local next=$((task + 1))
      write_state "$next" 0 "$giter"
      {
        echo
        echo "## Task ${task} completed at global iteration ${giter}"
        echo "- Pytest for this stage is green; carry regressions forward."
      } >>AGENTS.md
      continue
    fi

    passed=0
    consecutive_failures=$((consecutive_failures + 1))
    tok=$(approx_tokens)
    record_metrics "$giter" "$task" 0 "$elapsed" "$tok" "$consecutive_failures"
    log "[harness] tests FAILED for task ${task}"
    package_errors
    append_agents "$giter" "$task"
    fails=$((fails + 1))
    write_state "$task" "$fails" "$giter"
    restore_checkpoint "$task"
  done

  log "[harness] MAX_GLOBAL_ITER reached — failing"
  exit 1
}

main "$@"
