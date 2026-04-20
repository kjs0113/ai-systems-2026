from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[2]
DEFAULT_LOG_PATH = BASE_DIR / "harness.log"
DEFAULT_REPORT_PATH = BASE_DIR / "error_report.md"
WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s`]+")


@dataclass(frozen=True)
class PatternRule:
    category: str
    label: str
    description: str
    patterns: tuple[str, ...]


PATTERN_RULES = (
    PatternRule(
        category="syntax",
        label="encoding_or_text_corruption",
        description="Corrupted text or mojibake created brittle matching and patching behavior.",
        patterns=("encoding-corrupted", "non-ASCII", "mojibake", "I?셫", "I?셪l", "??"),
    ),
    PatternRule(
        category="logic",
        label="failing_test_or_wrong_behavior",
        description="The log shows a real behavior mismatch such as failing pytest output or wrong exception behavior.",
        patterns=("FAILED ", "failed, ", "AssertionError", "ZeroDivisionError", "exact message"),
    ),
    PatternRule(
        category="timeout",
        label="slow_or_timeout_signal",
        description="The log contains timeout or long-running execution signals.",
        patterns=("timeout", "timed out", "deadline exceeded"),
    ),
    PatternRule(
        category="api",
        label="tool_router_or_patch_failure",
        description="Tool invocation or patch application failed at the API/tooling layer.",
        patterns=("ERROR codex_core::tools::router", "Exit code: 1", "apply_patch verification failed"),
    ),
    PatternRule(
        category="other",
        label="warnings_or_misc",
        description="Warnings or other non-blocking issues appeared in the run.",
        patterns=("warning", "warnings summary", "PytestCacheWarning"),
    ),
)


def load_log(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sanitize_text(text: str) -> str:
    sanitized = text.replace(str(DEFAULT_LOG_PATH), "harness.log")
    sanitized = sanitized.replace(str(DEFAULT_REPORT_PATH), "error_report.md")
    sanitized = sanitized.replace(str(REPO_ROOT) + "\\", "")

    def replace_windows_path(match: re.Match[str]) -> str:
        raw = match.group(0)
        normalized = raw.replace("\\", "/")
        marker = "/assignments/"
        index = normalized.lower().find(marker)
        if index != -1:
            return normalized[index + 1 :]
        return "[local-path]"

    return WINDOWS_PATH_RE.sub(replace_windows_path, sanitized)


def classify_lines(text: str) -> dict[str, object]:
    lines = text.splitlines()
    matches: dict[str, list[dict[str, object]]] = {
        rule.category: [] for rule in PATTERN_RULES
    }

    for line_number, line in enumerate(lines, start=1):
        lowered = line.lower()
        for rule in PATTERN_RULES:
            if any(pattern.lower() in lowered for pattern in rule.patterns):
                matches[rule.category].append(
                    {
                        "line": line_number,
                        "label": rule.label,
                        "text": sanitize_text(line.strip()),
                    }
                )

    pattern_counts = {
        category: len(entries) for category, entries in matches.items() if entries
    }
    return {
        "source": DEFAULT_LOG_PATH.name,
        "total_lines": len(lines),
        "pattern_counts": pattern_counts,
        "matches": matches,
    }


def build_report(analysis: dict[str, object]) -> str:
    source = analysis["source"]
    total_lines = analysis["total_lines"]
    counts = analysis["pattern_counts"]
    matches = analysis["matches"]

    lines = [
        "# Error Report",
        "",
        f"- Source log: `{source}`",
        f"- Total lines scanned: `{total_lines}`",
        "",
        "## Pattern Summary",
    ]

    if counts:
        for rule in PATTERN_RULES:
            count = counts.get(rule.category, 0)
            if count:
                lines.append(f"- `{rule.category}`: {count} matches")
    else:
        lines.append("- No configured patterns were detected.")

    lines.extend(["", "## Findings"])

    for rule in PATTERN_RULES:
        entries = matches.get(rule.category, [])
        if not entries:
            continue
        lines.append(f"### {rule.category}")
        lines.append(rule.description)
        for entry in entries[:5]:
            snippet = str(entry["text"]).replace("`", "'")
            lines.append(f"- line {entry['line']} [{entry['label']}]: `{snippet}`")
        if len(entries) > 5:
            lines.append(f"- ... {len(entries) - 5} additional matches omitted")
        lines.append("")

    lines.extend(
        [
            "## Recommendations",
            "- Keep failing-test diagnosis separate from tool-level patch failures.",
            "- Re-read exact source lines before patching when corrupted text appears in the log.",
            "- Preserve exact exception behavior when tests compare both type and message.",
            "- Treat warnings as secondary signals unless they block completion.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report_text: str, output_path: Path) -> None:
    output_path.write_text(report_text, encoding="utf-8")


def analyze_log(log_path: Path) -> dict[str, object]:
    analysis = classify_lines(load_log(log_path))
    analysis["source"] = log_path.name
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze harness.log and classify errors by assignment categories.")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG_PATH, help="Path to harness.log")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Path to write error_report.md")
    parser.add_argument("--json", action="store_true", help="Print analysis as JSON")
    args = parser.parse_args()

    analysis = analyze_log(args.log)
    report_text = build_report(analysis)
    write_report(report_text, args.report)

    if args.json:
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        print(f"Analyzed: {args.log}")
        print(f"Report written: {args.report}")
        for name, count in analysis["pattern_counts"].items():
            print(f"- {name}: {count}")


if __name__ == "__main__":
    main()
