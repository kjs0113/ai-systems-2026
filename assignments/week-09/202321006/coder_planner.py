import anthropic
import os
import json

class PlannerAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def plan(self, requirement: str) -> str:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system="당신은 시니어 시스템 아키텍트입니다. 요구사항을 분석하여 아키텍처 설계를 작성하세요.",
            messages=[{"role": "user", "content": requirement}]
        )
        return response.content[0].text

class CoderAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def write_code(self, plan: str, requirement: str, feedback: str = "") -> dict:
        prompt = f"계획:\n{plan}\n\n요구사항:\n{requirement}"
        if feedback:
            prompt += f"\n\n이전 QA 피드백 (수정 필요):\n{feedback}"

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system="당신은 전문 파이썬 개발자입니다. 요구사항에 맞는 코드와 pytest 테스트 코드를 작성하세요. JSON 형식으로 응답하세요: {'code': '...', 'test': '...'}",
            messages=[{"role": "user", "content": prompt}]
        )
        # 텍스트에서 JSON 추출 (단순화된 방식)
        content = response.content[0].text
        try:
            return json.loads(content)
        except:
            # 마크다운 태그 제거 시도 등 추가 처리 가능
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"code": "", "test": ""}
