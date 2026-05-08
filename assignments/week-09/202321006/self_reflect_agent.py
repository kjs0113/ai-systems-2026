import anthropic
import json
import os

class SelfReflectAgent:
    """코더 에이전트의 자기 리뷰 — /reflect 패턴 구현"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def reflect(self, code: str, original_requirement: str) -> dict:
        """구현 결과를 요구사항과 대조하여 자기 검토"""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system="""당신은 방금 코드를 작성한 개발자다. 냉정하게 자기 검토하라.

확인 항목:
1. 요구사항의 모든 항목이 구현됐는가?
2. 명백한 버그나 오타가 있는가?
3. 테스트가 실제 요구사항을 검증하는가?
4. 모호하거나 가정에 의존한 부분이 있는가?

반드시 JSON으로만 응답하라.
출력: {
  "obvious_issues": [...],
  "ambiguous_requirements": [...],
  "questions_for_qa": [...],
  "self_confidence": 0-10
}""",
            messages=[{
                "role": "user",
                "content": f"요구사항:\n{original_requirement}\n\n내가 작성한 코드:\n{code}"
            }]
        )
        try:
            return json.loads(response.content[0].text)
        except:
            # JSON 파싱 실패 시 기본 응답
            return {"obvious_issues": ["JSON parsing failed"], "self_confidence": 0}

    def should_proceed_to_review(self, reflect_result: dict) -> bool:
        """자기 리뷰 결과로 독립 리뷰 진행 여부 결정"""
        if reflect_result.get("obvious_issues"):
            return False
        if reflect_result.get("self_confidence", 0) < 4:
            return False
        return True
