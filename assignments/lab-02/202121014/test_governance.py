from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from governance import AUDIT_LOG_PATH, ActionRisk, governance_check


def reset_audit_log() -> None:
    Path(AUDIT_LOG_PATH).write_text("", encoding="utf-8")


def load_entries() -> list[dict[str, object]]:
    lines = Path(AUDIT_LOG_PATH).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_critical_always_denied() -> None:
    reset_audit_log()
    approved = governance_check("rm -rf /", ActionRisk.CRITICAL)
    entries = load_entries()

    assert approved is False
    assert len(entries) == 1
    assert entries[0]["risk"] == "critical"
    assert entries[0]["approved"] is False


def test_low_auto_approved() -> None:
    reset_audit_log()
    approved = governance_check("read config file", ActionRisk.LOW)
    entries = load_entries()

    assert approved is True
    assert len(entries) == 1
    assert entries[0]["risk"] == "low"
    assert entries[0]["approved"] is True


def test_audit_log_is_jsonl() -> None:
    reset_audit_log()
    governance_check("show project files", ActionRisk.LOW)
    governance_check("update README", ActionRisk.MEDIUM)
    with patch("builtins.input", return_value="yes"):
        governance_check("delete temp file", ActionRisk.HIGH)

    lines = Path(AUDIT_LOG_PATH).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    for line in lines:
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "action" in entry
        assert "risk" in entry
        assert "approved" in entry
        assert "reason" in entry
