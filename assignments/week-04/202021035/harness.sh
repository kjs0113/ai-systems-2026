#!/usr/bin/env bash
# Ralph loop harness for Lab 04
#
# This script implements a simplified version of the Ralph Wiggum loop.
# It reads a list of tasks from `tasks.json`, then repeatedly spawns
# execution contexts (simulated by `run_task.py`) until all tasks
# succeed or a maximum number of iterations is reached.  Between
# iterations it applies backpressure (waits after consecutive
# failures) and performs garbage collection on archived state files.

set -euo pipefail

# Maximum number of iterations.  Can be overridden by the first
# command‑line argument.
MAX_ITERATIONS=${1:-10}

# Paths to important files and directories relative to this script.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

TASKS_FILE="tasks.json"
STATE_DIR="state"
PROGRESS_FILE="$STATE_DIR/progress.json"
AGENTS_FILE="AGENTS.md"
LOG_FILE="loop_log.txt"
METRICS_FILE="metrics.csv"
ARCHIVE_DIR="archive"
MAX_ARCHIVES=3

mkdir -p "$STATE_DIR" "$ARCHIVE_DIR"

# Initialise progress.json if this is the first run.  We copy
# the initial tasks list so that subsequent runs modify the
# copied file rather than the canonical tasks definition.
if [ ! -f "$PROGRESS_FILE" ]; then
  cp "$TASKS_FILE" "$PROGRESS_FILE"
fi

# Initialise the metrics CSV file on first run.  This file
# collects basic per‑iteration metrics such as the simulated token
# count and execution time for each task.  These metrics are
# useful when analysing scaling behaviour of the harness at
# test‑time.
if [ ! -f "$METRICS_FILE" ]; then
  echo "iteration,task_id,tokens,time_ms,success" > "$METRICS_FILE"
fi

# Fail streak counter used for backpressure.  If failures
# accumulate over multiple iterations the harness slows down
# subsequent retries to prevent runaway resource consumption.
FAIL_STREAK=0

for ((iter=1; iter<=MAX_ITERATIONS; iter++)); do
  echo "========== Iteration $iter ==========" | tee -a "$LOG_FILE"

  # Read the current state of tasks from progress.json.  Using
  # jq lets us extract just the tasks that have not yet passed.
  # Extract the list of unfinished task identifiers.  Do not attempt
  # to extract titles here because jq output would be split on
  # whitespace and produce incorrect arrays.  Titles are queried per
  # task inside the loop below.
  mapfile -t TASK_IDS < <(jq -r '.[] | select(.passes==false) | .id' < "$PROGRESS_FILE")

  # If there are no remaining tasks, the loop is complete.
  if [ ${#TASK_IDS[@]} -eq 0 ]; then
    echo "All tasks complete." | tee -a "$LOG_FILE"
    break
  fi

  # Track whether any task failed this iteration.  Used for
  # backpressure and to decide whether to increment fail streak.
  ITERATION_FAIL=false

  for index in "${!TASK_IDS[@]}"; do
    task_id="${TASK_IDS[$index]}"
    # Look up the task title on demand to avoid word splitting issues.
    title=$(jq -r --argjson id "$task_id" '.[] | select(.id == $id) | .title' < "$PROGRESS_FILE")
    echo "[Task $task_id] $title" | tee -a "$LOG_FILE"

    # Measure start time to compute a simple duration metric.  The
    # built‑in `date` command with nanoseconds is not POSIX but
    # available on most systems; using milliseconds suffices here.
    start_time=$(date +%s%3N)

    # Run the task via the Python helper.  The helper simulates
    # success or failure based on the iteration number and task id.
    # We must temporarily disable `set -e` to capture a non‑zero
    # return code without exiting the harness.
    set +e
    python3 run_task.py "$task_id" "$iter" >> "$LOG_FILE" 2>&1
    exit_code=$?
    set -e

    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))

    # Simulate token usage for metrics.  A random integer between
    # 150 and 300 approximates the number of tokens consumed when
    # invoking a large language model.  This helps illustrate
    # compute scaling in the README.
    tokens=$(python3 - <<'PY'
import random; print(random.randint(150,300))
PY
)

    if [ "$exit_code" -eq 0 ]; then
      echo " -> SUCCESS" | tee -a "$LOG_FILE"
      # Update the progress file to mark this task as passed.
      tmp=$(mktemp)
      jq --argjson id "$task_id" 'map(if .id == $id then .passes = true else . end)' "$PROGRESS_FILE" > "$tmp"
      mv "$tmp" "$PROGRESS_FILE"
      success=1
      # Record a success learning in AGENTS.md.  Future iterations
      # read these learnings to avoid repeating mistakes.
      echo "- iteration $iter: Task $task_id succeeded; consolidated best practices for ${title}." >> "$AGENTS_FILE"
    else
      echo " -> FAIL" | tee -a "$LOG_FILE"
      ITERATION_FAIL=true
      success=0
      # Record a failure learning in AGENTS.md.  Failures are
      # valuable – they point to gaps in understanding or missing
      # edge cases.
      echo "- iteration $iter: Task $task_id failed; reviewed implementation and identified algorithmic improvements." >> "$AGENTS_FILE"
    fi

    # Append metrics for this task execution.  Metrics include the
    # iteration number, task id, simulated token count, wall‑clock
    # duration in milliseconds, and success flag.
    echo "$iter,$task_id,$tokens,$duration,$success" >> "$METRICS_FILE"
  done

  # If any task failed, increment the failure streak and apply
  # backpressure.  Backpressure here simply inserts a short sleep
  # after multiple consecutive failures to throttle the loop.  In a
  # real system this might integrate with queue depths or memory
  # usage metrics.
  if [ "$ITERATION_FAIL" = true ]; then
    FAIL_STREAK=$((FAIL_STREAK + 1))
    echo "Failure detected in iteration $iter.  Learning and retrying..." | tee -a "$LOG_FILE"
    if [ $FAIL_STREAK -ge 3 ]; then
      echo "Backpressure engaged after $FAIL_STREAK consecutive failures; pausing before next iteration." | tee -a "$LOG_FILE"
      sleep 1
    fi
  else
    # Reset fail streak on a fully successful iteration.
    FAIL_STREAK=0
  fi

  # Garbage collection: archive the current progress file.  Only a
  # limited number of archives are kept to avoid unbounded growth
  # over time.  Older archives are removed once the limit is
  # exceeded.
  cp "$PROGRESS_FILE" "$ARCHIVE_DIR/progress_iter_${iter}.json"
  archive_count=$(ls "$ARCHIVE_DIR" | wc -l)
  if [ "$archive_count" -gt "$MAX_ARCHIVES" ]; then
    oldest=$(ls "$ARCHIVE_DIR" | sort | head -n 1)
    rm -f "$ARCHIVE_DIR/$oldest"
  fi
done