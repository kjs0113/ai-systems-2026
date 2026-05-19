from __future__ import annotations

from dataclasses import dataclass, field


def _estimate_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // 4)


@dataclass
class TokenCounter:
    model_name: str = "gpt-4o-mini"
    input_cost_per_million: float = 0.15
    output_cost_per_million: float = 0.60
    input_tokens: int = 0
    output_tokens: int = 0
    history: list[dict[str, int | str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._encoder = self._load_encoder(self.model_name)

    def _load_encoder(self, model_name: str):
        try:
            import tiktoken  # type: ignore

            return tiktoken.encoding_for_model(model_name)
        except Exception:
            return None

    def count_text(self, text: str) -> int:
        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text))
            except Exception:
                pass
        return _estimate_tokens(text)

    def add_message(self, role: str, content: str) -> int:
        tokens = self.count_text(content)
        bucket = "output" if role == "assistant" else "input"
        if bucket == "output":
            self.output_tokens += tokens
        else:
            self.input_tokens += tokens
        self.history.append(
            {
                "role": role,
                "tokens": tokens,
                "bucket": bucket,
                "running_total": self.total_tokens,
            }
        )
        return tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost(self) -> float:
        input_cost = (self.input_tokens / 1_000_000) * self.input_cost_per_million
        output_cost = (self.output_tokens / 1_000_000) * self.output_cost_per_million
        return input_cost + output_cost

    def report(self) -> str:
        return "\n".join(
            [
                "Token Usage Report",
                f"- model: {self.model_name}",
                f"- input_tokens: {self.input_tokens}",
                f"- output_tokens: {self.output_tokens}",
                f"- total_tokens: {self.total_tokens}",
                f"- estimated_cost_usd: ${self.estimated_cost:.6f}",
            ]
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "input_cost_per_million": self.input_cost_per_million,
            "output_cost_per_million": self.output_cost_per_million,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "history": self.history,
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, object] | None) -> "TokenCounter":
        counter = cls(
            model_name=str((snapshot or {}).get("model_name", "gpt-4o-mini")),
            input_cost_per_million=float((snapshot or {}).get("input_cost_per_million", 0.15)),
            output_cost_per_million=float((snapshot or {}).get("output_cost_per_million", 0.60)),
        )
        counter.input_tokens = int((snapshot or {}).get("input_tokens", 0))
        counter.output_tokens = int((snapshot or {}).get("output_tokens", 0))
        history = (snapshot or {}).get("history", [])
        counter.history = list(history) if isinstance(history, list) else []
        return counter
