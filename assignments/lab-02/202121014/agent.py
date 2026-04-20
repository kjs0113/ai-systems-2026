from __future__ import annotations

import os
from pathlib import Path

from governance import ActionRisk, governance_check


def load_env_file() -> None:
    env_path = Path(__file__).resolve().with_name(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def call_claude(user_input: str) -> str:
    load_env_file()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return user_input

    try:
        from anthropic import Anthropic  # type: ignore

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=128,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Return one short suggested action for this request. "
                        "Do not explain. Request: " + user_input
                    ),
                }
            ],
        )
        parts = []
        for block in response.content:
            text = getattr(block, "text", "")
            if text:
                parts.append(text)
        suggestion = " ".join(parts).strip()
        return suggestion or user_input
    except Exception:
        return user_input


def classify_risk(action: str) -> ActionRisk:
    lowered = action.lower()

    critical_keywords = ["rm -rf", "format", "shutdown"]
    high_keywords = ["delete", "remove", "drop database"]
    medium_keywords = ["write", "modify", "update", "create", "save"]
    low_keywords = ["read", "list", "show", "print", "파일 읽기"]

    if any(keyword in lowered for keyword in critical_keywords):
        return ActionRisk.CRITICAL
    if any(keyword in lowered for keyword in high_keywords):
        return ActionRisk.HIGH
    if any(keyword in lowered for keyword in medium_keywords):
        return ActionRisk.MEDIUM
    if any(keyword in lowered for keyword in low_keywords):
        return ActionRisk.LOW
    return ActionRisk.MEDIUM


def main() -> None:
    print("AI 코딩 에이전트를 시작합니다. 종료하려면 exit 를 입력하세요.")

    while True:
        user_input = input("요청> ").strip()
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("에이전트를 종료합니다.")
            break

        action = call_claude(user_input)
        risk = classify_risk(action)
        print(f"제안된 액션: {action}")
        print(f"분류된 위험도: {risk.value}")

        approved = governance_check(action, risk)
        if approved:
            print(f"실행 결과: 승인됨. '{action}' 작업을 실행한 것으로 처리합니다.")
        else:
            print("실행 결과: 거버넌스 정책에 의해 차단되었습니다.")


if __name__ == "__main__":
    main()
