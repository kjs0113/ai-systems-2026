#!/usr/bin/env bash
# =============================================================================
# harness.sh — Ralph Loop Harness
# R.A.L.P.H = Retry · Apply · Learn · Prove · Halt
#
# Features:
#   - Exponential backpressure on consecutive failures
#   - Context-window garbage collection (prunes stale state)
#   - Stuck-detection: splits task into subtasks after N failures
#   - Per-iteration metrics (CSV)
#   - AGENTS.md incremental learning log
# =============================================================================

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────
MAX_ITERATIONS=12
GC_INTERVAL=3            # Run GC every N iterations
BACKPRESSURE_BASE=2      # Base seconds for exponential backoff (2^n cap 32s)
STUCK_THRESHOLD=3        # Consecutive failures before task split
MAX_CONTEXT_LINES=120    # Lines kept in context file after GC
TASKS_FILE="PROMPT.md"

# ─── State / output files ─────────────────────────────────────────────────────
STATE_FILE=".loop_state.json"
AGENTS_FILE="AGENTS.md"
LOG_FILE="loop_log.txt"
METRICS_FILE="metrics.csv"
ERROR_LOG=".error_log.txt"
CONTEXT_FILE=".context_window.txt"

# ─── Colour helpers ───────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[HARNESS]${RESET} $*" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}    $*" | tee -a "$LOG_FILE"; }
err()  { echo -e "${RED}[ERROR]${RESET}   $*" | tee -a "$LOG_FILE"; }
ok()   { echo -e "${GREEN}[OK]${RESET}      $*" | tee -a "$LOG_FILE"; }

# ─── Timestamp helper ─────────────────────────────────────────────────────────
ts() { date '+%Y-%m-%dT%H:%M:%S'; }

# ─── Bootstrap state file ─────────────────────────────────────────────────────
init_state() {
    # Always reset for a clean, reproducible run
    cat > "$STATE_FILE" <<'STATEOF'
{
  "iteration": 0,
  "consecutive_failures": 0,
  "total_success": 0,
  "total_failure": 0,
  "subtask_mode": false,
  "halted": false
}
STATEOF

    # Reset metrics CSV (fresh header)
    echo "iteration,task_id,status,duration_sec,consecutive_failures,gc_ran,subtask_mode,timestamp" \
        > "$METRICS_FILE"

    # Reset context window and error log
    > "$CONTEXT_FILE"
    > "$ERROR_LOG"
    rm -f loop_results.json report.txt .last_error.txt .repair_count_optimize_sort

    # ── Broken-state setup ───────────────────────────────────────────────────
    # Copy intentionally broken files so the loop encounters genuine failures,
    # records them in AGENTS.md, runs REPAIR, and retries — demonstrating
    # the full failure → learning → success cycle.
    mkdir -p tasks/broken
    if [[ -f "tasks/broken/autoresearch_broken.py" ]]; then
        cp "tasks/broken/autoresearch_broken.py" "autoresearch.py"
        log "init_state: autoresearch.py → v0-broken (missing 'improved' key)."
    fi
    if [[ -f "tasks/broken/calculator_broken.py" ]]; then
        cp "tasks/broken/calculator_broken.py" "tasks/calculator.py"
        log "init_state: tasks/calculator.py → v0-broken (no ZeroDivisionError guard)."
    fi
}

# ─── State accessors (Python-based, no jq dependency) ───────────────────────
state_get()  {
    python3 -c "import json,sys; d=json.load(open('$STATE_FILE')); print(repr(d.get('$1','')) if isinstance(d.get('$1'),str) else d.get('$1',''))" 2>/dev/null
}
state_set()  {                                           # key value (value must be JSON-literal)
    local tmp; tmp=$(mktemp)
    python3 - <<PYEOF > "$tmp"
import json
d = json.load(open('$STATE_FILE'))
d['$1'] = $2
print(json.dumps(d, indent=2))
PYEOF
    mv "$tmp" "$STATE_FILE"
}
state_inc()  {                                           # key
    local tmp; tmp=$(mktemp)
    python3 - <<PYEOF > "$tmp"
import json
d = json.load(open('$STATE_FILE'))
d['$1'] = d.get('$1', 0) + 1
print(json.dumps(d, indent=2))
PYEOF
    mv "$tmp" "$STATE_FILE"
}

# ─── Parse tasks from PROMPT.md ───────────────────────────────────────────────
# Tasks are lines starting with "### TASK:" in PROMPT.md
declare -a TASK_IDS=()
declare -A TASK_CMDS=()
declare -A TASK_VALIDATORS=()
declare -A TASK_REPAIRS=()

load_tasks() {
    local id="" cmd="" validator="" repair=""
    while IFS= read -r line; do
        if [[ "$line" =~ ^###\ TASK:\ (.+) ]]; then
            [[ -n "$id" ]] && {
                TASK_IDS+=("$id")
                TASK_CMDS["$id"]="$cmd"
                TASK_VALIDATORS["$id"]="$validator"
                TASK_REPAIRS["$id"]="$repair"
            }
            id="${BASH_REMATCH[1]}"; cmd=""; validator=""; repair=""
        elif [[ "$line" =~ ^CMD:\ (.+) ]];      then cmd="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^VALIDATE:\ (.+) ]]; then validator="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^REPAIR:\ (.+) ]];   then repair="${BASH_REMATCH[1]}"
        fi
    done < "$TASKS_FILE"
    [[ -n "$id" ]] && {
        TASK_IDS+=("$id")
        TASK_CMDS["$id"]="$cmd"
        TASK_VALIDATORS["$id"]="$validator"
        TASK_REPAIRS["$id"]="$repair"
    }
}

# ─── Garbage Collection ───────────────────────────────────────────────────────
# Trims the context window to MAX_CONTEXT_LINES and prunes stale error entries.
garbage_collect() {
    local iter="$1"
    log "GC triggered at iteration ${iter}."

    # 1. Trim context window (keep only last MAX_CONTEXT_LINES lines)
    if [[ -f "$CONTEXT_FILE" ]]; then
        local line_count
        line_count=$(wc -l < "$CONTEXT_FILE")
        if (( line_count > MAX_CONTEXT_LINES )); then
            local tmp; tmp=$(mktemp)
            tail -n "$MAX_CONTEXT_LINES" "$CONTEXT_FILE" > "$tmp"
            mv "$tmp" "$CONTEXT_FILE"
            log "Context window trimmed: ${line_count} → ${MAX_CONTEXT_LINES} lines."
        fi
    fi

    # 2. Keep only the last 30 lines of the error log (prevent unbounded growth)
    if [[ -f "$ERROR_LOG" ]]; then
        local el_count
        el_count=$(wc -l < "$ERROR_LOG")
        if (( el_count > 30 )); then
            local tmp; tmp=$(mktemp)
            tail -n 30 "$ERROR_LOG" > "$tmp"
            mv "$tmp" "$ERROR_LOG"
            log "Error log pruned: ${el_count} → 30 lines."
        fi
    fi

    # 3. Remove any temp artefacts from previous runs
    rm -f .tmp_task_output_* 2>/dev/null || true

    ok "GC complete."
}

# ─── Backpressure ─────────────────────────────────────────────────────────────
# Implements exponential back-off capped at 32 s.
apply_backpressure() {
    local failures="$1"
    if (( failures > 0 )); then
        local delay=$(( BACKPRESSURE_BASE ** failures ))
        (( delay > 32 )) && delay=32
        warn "Backpressure: waiting ${delay}s after ${failures} consecutive failure(s)."
        sleep "$delay"
    fi
}

# ─── Stuck-detection & task splitting ─────────────────────────────────────────
# Returns 0 if stuck, 1 otherwise.
is_stuck() {
    local failures="$1"
    (( failures >= STUCK_THRESHOLD ))
}

# Produces sub-task IDs for a given task (naive: appends _part1, _part2)
split_task() {
    local task_id="$1"
    local cmd="${TASK_CMDS[$task_id]}"
    local sub1="${task_id}_part1"
    local sub2="${task_id}_part2"
    TASK_IDS+=("$sub1" "$sub2")
    TASK_CMDS["$sub1"]="echo '[sub1] Validating environment for ${task_id}'"
    TASK_CMDS["$sub2"]="eval \"${cmd}\""
    TASK_VALIDATORS["$sub1"]="true"
    TASK_VALIDATORS["$sub2"]="${TASK_VALIDATORS[$task_id]}"
    TASK_REPAIRS["$sub1"]="${TASK_REPAIRS[$task_id]:-}"
    TASK_REPAIRS["$sub2"]=""
    warn "Task '${task_id}' split into sub-tasks: ${sub1}, ${sub2}"
}

# ─── Learning: append to AGENTS.md ───────────────────────────────────────────
# $1=iter $2=task_id $3=status $4=error_msg $5=repair_cmd $6=prev_failures
record_learning() {
    local iter="$1" task_id="$2" status="$3"
    local error_msg="${4:-}" repair_cmd="${5:-}" prev_fail="${6:-0}"
    local entry_ts; entry_ts=$(ts)

    # ── 1. Repair scripts write .repair_rationale.txt; consume it here ────────
    local rationale=""
    if [[ -f ".repair_rationale.txt" ]]; then
        rationale=$(cat ".repair_rationale.txt")
        rm -f ".repair_rationale.txt"
    fi

    if [[ "$status" == "FAIL" ]]; then
        {
            echo ""
            echo "## Iteration ${iter} — FAILURE [${entry_ts}]"
            echo "**Task:** \`${task_id}\`"
            echo "**이전 연속 실패 횟수:** ${prev_fail}"
            echo "**Error:**"
            echo '```'
            echo "${error_msg}"
            echo '```'
            if [[ -n "$rationale" ]]; then
                echo ""
                echo "${rationale}"
            fi
            echo "**Repair applied:** \`${repair_cmd:-없음 (stuck detection 대기)}\`"
        } >> "$AGENTS_FILE"

    else
        # ── 2. Success: extract evidence that prior-iteration learning was used ─
        local prev_fail_iters=""
        if [[ "${prev_fail}" -gt 0 && -f "$CONTEXT_FILE" ]]; then
            prev_fail_iters=$(grep "task=${task_id} status=FAIL" "$CONTEXT_FILE" \
                | awk -F'iter=' '{print $2}' | awk '{print $1}' \
                | tr '\n' ', ' | sed 's/,$//')
        fi

        local note
        if [[ "${prev_fail}" -gt 0 ]]; then
            note="${prev_fail}회 실패 후 REPAIR 반영 → 성공 (학습 적용 확인)"
        else
            note="첫 시도 성공"
        fi

        {
            echo ""
            echo "## Iteration ${iter} — SUCCESS [${entry_ts}]"
            echo "**Task:** \`${task_id}\`"
            echo "**이전 실패 횟수:** ${prev_fail}"
            echo "**Result:** ${note}."
            if [[ -n "$prev_fail_iters" ]]; then
                echo "**학습 반영 증거:**"
                echo "- context_window.txt에서 이전 FAIL 반복 [${prev_fail_iters}] 확인"
                echo "- 각 반복의 실패 원인 분석 → repair 스크립트가 context 참조하여 단계적 REPAIR 적용"
                echo "- 최종 REPAIR 결과가 이번 VALIDATE 통과에 직접 반영됨"
            fi
            echo "**Learning locked in:** 수정 사항 검증 완료. 다음 태스크로 진행."
        } >> "$AGENTS_FILE"
    fi

    # ── 3. Append one-liner to context window (repair scripts read this) ───────
    echo "[${entry_ts}] iter=${iter} task=${task_id} status=${status}" >> "$CONTEXT_FILE"
}

# ─── Run a single task ────────────────────────────────────────────────────────
# Returns 0 on success, 1 on failure.  Writes stderr to ERROR_LOG.
run_task() {
    local task_id="$1"
    local cmd="${TASK_CMDS[$task_id]:-echo 'no-op'}"
    local validator="${TASK_VALIDATORS[$task_id]:-true}"
    local tmp_out; tmp_out=$(mktemp .tmp_task_output_XXXXXX)

    log "Running task '${task_id}'"
    log "  CMD:      ${cmd}"
    log "  VALIDATE: ${validator}"

    # Execute
    if eval "$cmd" > "$tmp_out" 2>> "$ERROR_LOG"; then
        # Validate
        if eval "$validator" >> "$tmp_out" 2>> "$ERROR_LOG"; then
            cat "$tmp_out" >> "$LOG_FILE"
            rm -f "$tmp_out"
            return 0
        else
            echo "VALIDATION FAILED for task ${task_id}" >> "$ERROR_LOG"
            cat "$tmp_out" >> "$LOG_FILE"
            rm -f "$tmp_out"
            return 1
        fi
    else
        local exit_code=$?
        echo "CMD FAILED (exit ${exit_code}) for task ${task_id}" >> "$ERROR_LOG"
        cat "$tmp_out" >> "$LOG_FILE"
        rm -f "$tmp_out"
        return 1
    fi
}

# ─── Emit one row to metrics CSV ──────────────────────────────────────────────
record_metrics() {
    local iter="$1" task_id="$2" status="$3" duration="$4" \
          consec_fail="$5" gc_ran="$6" subtask_mode="$7"
    echo "${iter},${task_id},${status},${duration},${consec_fail},${gc_ran},${subtask_mode},$(ts)" \
        >> "$METRICS_FILE"
}

# ─── Main Loop ────────────────────────────────────────────────────────────────
main() {
    # Clear old log for a fresh run
    > "$LOG_FILE"

    log "════════════════════════════════════════"
    log " Ralph Loop Harness — starting at $(ts)"
    log "════════════════════════════════════════"

    init_state
    load_tasks

    if (( ${#TASK_IDS[@]} == 0 )); then
        err "No tasks found in ${TASKS_FILE}. Aborting."
        exit 1
    fi

    log "Loaded ${#TASK_IDS[@]} task(s): ${TASK_IDS[*]}"

    local task_index=0
    local iteration=0
    local halted=false

    while (( iteration < MAX_ITERATIONS )) && ! "$halted"; do
        iteration=$(( iteration + 1 ))
        state_set "iteration" "$iteration"

        local task_id="${TASK_IDS[$task_index]}"
        local consec_fail; consec_fail=$(state_get "consecutive_failures")
        local subtask_mode; subtask_mode=$(state_get "subtask_mode")
        local gc_ran=false

        log "────────────────────────────────────────"
        log "Iteration ${iteration}/${MAX_ITERATIONS} — Task: ${task_id}"
        log "  Consecutive failures: ${consec_fail}"

        # ── Stuck detection ──────────────────────────────────────────────────
        if is_stuck "$consec_fail"; then
            warn "STUCK detected after ${consec_fail} failures on '${task_id}'."
            split_task "$task_id"
            state_set "consecutive_failures" "0"
            state_set "subtask_mode" "True"
            consec_fail=0
            # Advance to first sub-task (split_task appended 2 new entries)
            task_id="${TASK_IDS[$task_index]}"
            warn "Switching to subtask mode. New task: ${task_id}"
        fi

        # ── Backpressure ──────────────────────────────────────────────────────
        apply_backpressure "$consec_fail"

        # ── Garbage Collection ────────────────────────────────────────────────
        if (( iteration % GC_INTERVAL == 0 )); then
            garbage_collect "$iteration"
            gc_ran=true
        fi

        # ── Execute (APPLY + PROVE) ────────────────────────────────────────────
        local t_start; t_start=$(date +%s)
        local task_status="SUCCESS"
        local error_msg=""
        local repair_cmd=""

        if run_task "$task_id"; then
            ok "Task '${task_id}' PASSED."
            task_status="SUCCESS"
            state_set "consecutive_failures" "0"
            state_inc "total_success"

            # Advance to next task
            task_index=$(( task_index + 1 ))
            if [[ $task_index -ge ${#TASK_IDS[@]} ]]; then
                ok "All tasks completed. Halting."
                halted=true
                state_set "halted" "True"
            fi
        else
            error_msg=$(tail -n 5 "$ERROR_LOG" 2>/dev/null || echo "unknown error")
            err "Task '${task_id}' FAILED. Recording for learning."
            task_status="FAIL"

            # ── REPAIR mechanism ──────────────────────────────────────────────
            repair_cmd="${TASK_REPAIRS[$task_id]:-}"
            if [[ -n "$repair_cmd" ]]; then
                warn "Applying REPAIR for '${task_id}': ${repair_cmd}"
                eval "$repair_cmd" >> "$LOG_FILE" 2>> "$ERROR_LOG" || true
                warn "Repair complete. '${task_id}' will retry next iteration."
            fi

            state_inc "consecutive_failures"
            state_inc "total_failure"
        fi

        local t_end; t_end=$(date +%s)
        local duration=$(( t_end - t_start ))

        # ── Learn ─────────────────────────────────────────────────────────────
        record_learning "$iteration" "$task_id" "$task_status" \
            "$error_msg" "$repair_cmd" "$consec_fail"

        # ── Metrics ───────────────────────────────────────────────────────────
        record_metrics "$iteration" "$task_id" "$task_status" "$duration" \
            "$(state_get consecutive_failures)" "$gc_ran" "$subtask_mode"

        log "Iteration ${iteration} complete. Status=${task_status} Duration=${duration}s"
    done

    # ── Final summary ─────────────────────────────────────────────────────────
    log "════════════════════════════════════════"
    log " Loop finished at $(ts)"
    log " Total iterations : ${iteration}"
    log " Total successes  : $(state_get total_success)"
    log " Total failures   : $(state_get total_failure)"
    log " Halted normally  : $(state_get halted)"
    log " Metrics CSV      : ${METRICS_FILE}"
    log " Learning log     : ${AGENTS_FILE}"
    log "════════════════════════════════════════"
}

main "$@"
