from __future__ import annotations

import os
import time
from pathlib import Path

from context_manager import ContextManager
from state_tracker import StateTracker
from token_counter import TokenCounter


STATE_FILE = Path("progress_state.json")
PROGRESS_FILE = Path("claude-progress.txt")
TOTAL_TURNS = 24
TURN_DELAY_SECONDS = 0.10


def build_demo_messages() -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a coding assistant running a Lab-05 context management demo.",
        }
    ]
    for turn in range(1, TOTAL_TURNS + 1):
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Turn {turn}: keep track of progress, preserve resumable state, "
                    f"and explain whether rolling context compression is needed."
                ),
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Turn {turn}: processed successfully. I saved progress, updated token usage, "
                    f"and kept the newest messages available for the active context window."
                ),
            }
        )
    return messages


def write_progress_report(
    state: dict[str, object],
    context_messages: list[dict[str, str]],
    counter: TokenCounter,
) -> None:
    lines = [
        "Lab-05 Context Management Report",
        "",
        f"status: {state.get('status', 'unknown')}",
        f"processed_messages: {state.get('processed_messages', 0)}",
        f"total_messages: {state.get('total_messages', 0)}",
        f"compression_events: {state.get('compression_events', 0)}",
        "",
        counter.report(),
        "",
        "Active Context:",
    ]

    for index, message in enumerate(context_messages, start=1):
        lines.append(f"{index}. [{message['role']}] {message['content']}")

    logs = state.get("compression_logs", [])
    if isinstance(logs, list) and logs:
        lines.append("")
        lines.append("Compression Logs:")
        lines.extend(str(log) for log in logs)

    PROGRESS_FILE.write_text("\n".join(lines), encoding="utf-8")


def persist_state(
    tracker: StateTracker,
    *,
    status: str,
    next_index: int,
    total_messages: int,
    counter: TokenCounter,
    context_manager: ContextManager,
) -> None:
    tracker.update(
        status=status,
        next_index=next_index,
        processed_messages=next_index,
        total_messages=total_messages,
        token_counter=counter.snapshot(),
        context_manager=context_manager.snapshot(),
        compression_events=context_manager.compression_events,
        compression_logs=context_manager.logs,
    )
    tracker.save()


def restore_runtime(tracker: StateTracker) -> tuple[TokenCounter, ContextManager, int]:
    saved_state = tracker.load()
    counter = TokenCounter.from_snapshot(saved_state.get("token_counter"))
    context_manager = ContextManager.from_snapshot(saved_state.get("context_manager"))
    next_index = int(saved_state.get("next_index", 0))
    return counter, context_manager, next_index


def main() -> None:
    tracker = StateTracker(path=STATE_FILE)
    messages = build_demo_messages()
    total_messages = len(messages)
    interrupt_at = int(os.environ.get("LAB05_INTERRUPT_AT", "0"))

    counter, context_manager, start_index = restore_runtime(tracker)
    resuming = start_index > 0 and start_index < total_messages

    if resuming:
        print(f"Restored previous state. Resuming from message {start_index + 1}/{total_messages}.")
    else:
        counter = TokenCounter()
        context_manager = ContextManager(max_messages=8, keep_recent=6)
        start_index = 0
        tracker.update(
            status="starting",
            next_index=0,
            processed_messages=0,
            total_messages=total_messages,
            token_counter=counter.snapshot(),
            context_manager=context_manager.snapshot(),
            compression_events=0,
            compression_logs=[],
        )
        tracker.save()
        print("Starting Lab-05 context management demo.")

    try:
        for index in range(start_index, total_messages):
            message = messages[index]
            tokens = counter.add_message(message["role"], message["content"])
            compression_logs = context_manager.add_message(message["role"], message["content"])

            print(
                f"[turn {index + 1:02d}/{total_messages}] role={message['role']} "
                f"tokens={tokens} active_context={len(context_manager.get_messages())}"
            )
            for log_line in compression_logs:
                print(log_line)

            persist_state(
                tracker,
                status="running",
                next_index=index + 1,
                total_messages=total_messages,
                counter=counter,
                context_manager=context_manager,
            )
            if interrupt_at and index + 1 == interrupt_at:
                raise KeyboardInterrupt
            time.sleep(TURN_DELAY_SECONDS)
    except KeyboardInterrupt:
        persist_state(
            tracker,
            status="interrupted",
            next_index=int(tracker.state.get("next_index", start_index)),
            total_messages=total_messages,
            counter=counter,
            context_manager=context_manager,
        )
        print("\nExecution interrupted. Saved progress for resume on the next run.")
        print(counter.report())
        raise SystemExit(130)

    persist_state(
        tracker,
        status="completed",
        next_index=total_messages,
        total_messages=total_messages,
        counter=counter,
        context_manager=context_manager,
    )
    write_progress_report(tracker.state, context_manager.get_messages(), counter)

    print(counter.report())
    print(f"claude-progress.txt created: {PROGRESS_FILE.resolve()}")

    if tracker.state.get("status") == "completed":
        tracker.reset()


if __name__ == "__main__":
    main()
