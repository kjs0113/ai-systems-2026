from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StateTracker:
    path: Path = field(default_factory=lambda: Path("progress_state.json"))
    state: dict[str, Any] = field(default_factory=dict)

    def load(self) -> dict[str, Any]:
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.state = {}
        return self.state

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update(self, **kwargs: Any) -> dict[str, Any]:
        self.state.update(kwargs)
        return self.state

    def reset(self) -> None:
        self.state = {}
        self.save()
