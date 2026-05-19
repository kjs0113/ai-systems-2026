from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


AUDIT_LOG_PATH = Path(__file__).resolve().with_name("audit.jsonl")


class ActionRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def log_action(action: str, risk: ActionRisk, approved: bool, reason: str = "") -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "risk": risk.value,
        "approved": approved,
        "reason": reason,
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def require_human_approval(action: str) -> bool:
    print(f"HIGH 위험 액션입니다: {action}")
    answer = input("승인할까요? (yes/no): ").strip().lower()
    return answer == "yes"


def governance_check(action: str, risk: ActionRisk) -> bool:
    if risk == ActionRisk.CRITICAL:
        log_action(action, risk, False, "critical actions are always denied")
        return False

    if risk == ActionRisk.HIGH:
        approved = require_human_approval(action)
        reason = "human approved high risk action" if approved else "human denied high risk action"
        log_action(action, risk, approved, reason)
        return approved

    log_action(action, risk, True, "auto approved")
    return True
