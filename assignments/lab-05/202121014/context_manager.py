from __future__ import annotations

from dataclasses import dataclass, field


Message = dict[str, str]


@dataclass
class ContextManager:
    max_messages: int = 8
    keep_recent: int = 6
    summary_role: str = "system"
    messages: list[Message] = field(default_factory=list)
    compression_events: int = 0
    logs: list[str] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> list[str]:
        self.messages.append({"role": role, "content": content})
        return self._compress_if_needed()

    def get_messages(self) -> list[Message]:
        return [message.copy() for message in self.messages]

    def _compress_if_needed(self) -> list[str]:
        emitted_logs: list[str] = []
        while len(self.messages) > self.max_messages:
            emitted_logs.append(self._compress_once())
        return emitted_logs

    def _compress_once(self) -> str:
        older_messages = self.messages[:-self.keep_recent]
        recent_messages = self.messages[-self.keep_recent :]
        prior_summary = self._extract_prior_summary(older_messages)
        raw_messages = self._strip_summary_message(older_messages)
        summary = self._build_summary(prior_summary, raw_messages)

        self.messages = [{"role": self.summary_role, "content": summary}, *recent_messages]
        self.compression_events += 1

        log_line = (
            f"[rolling-window] compression #{self.compression_events}: "
            f"compressed {len(raw_messages)} messages, active_context={len(self.messages)}"
        )
        self.logs.append(log_line)
        return log_line

    def _extract_prior_summary(self, messages: list[Message]) -> str:
        if messages and messages[0]["role"] == self.summary_role and messages[0]["content"].startswith("Rolling summary:"):
            return messages[0]["content"]
        return ""

    def _strip_summary_message(self, messages: list[Message]) -> list[Message]:
        if messages and messages[0]["role"] == self.summary_role and messages[0]["content"].startswith("Rolling summary:"):
            return messages[1:]
        return messages

    def _build_summary(self, prior_summary: str, messages: list[Message]) -> str:
        lines = ["Rolling summary:"]
        if prior_summary:
            cleaned = prior_summary.replace("Rolling summary:", "").replace("- prior:", "").strip()
            lines.append(f"- prior: {self._condense(cleaned)}")
        if not messages:
            lines.append("- no older raw messages to summarize")
        else:
            for message in messages[-4:]:
                lines.append(f"- {message['role']}: {self._condense(message['content'])}")
        return "\n".join(lines)

    def _condense(self, text: str, limit: int = 72) -> str:
        single_line = " ".join(text.split())
        if len(single_line) <= limit:
            return single_line
        return f"{single_line[: limit - 3]}..."

    def snapshot(self) -> dict[str, object]:
        return {
            "max_messages": self.max_messages,
            "keep_recent": self.keep_recent,
            "summary_role": self.summary_role,
            "messages": self.messages,
            "compression_events": self.compression_events,
            "logs": self.logs,
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, object] | None) -> "ContextManager":
        manager = cls(
            max_messages=int((snapshot or {}).get("max_messages", 8)),
            keep_recent=int((snapshot or {}).get("keep_recent", 6)),
            summary_role=str((snapshot or {}).get("summary_role", "system")),
        )
        messages = (snapshot or {}).get("messages", [])
        manager.messages = list(messages) if isinstance(messages, list) else []
        manager.compression_events = int((snapshot or {}).get("compression_events", 0))
        logs = (snapshot or {}).get("logs", [])
        manager.logs = list(logs) if isinstance(logs, list) else []
        return manager
