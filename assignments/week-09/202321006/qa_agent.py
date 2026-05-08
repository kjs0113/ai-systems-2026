import subprocess
import anthropic
import json
import os
from pathlib import Path

class QAAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def run_tests(self, test_file: str) -> dict:
        """pytest 실행 및 결과 파싱"""
        # 실제 환경에 pytest-json-report가 없을 수 있으므로 기본 pytest 결과 사용
        result = subprocess.run(
            ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True, text=True
        )
        return {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }

    def code_review(self, diff: str) -> str:
        """Claude를 통한 코드 리뷰"""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system="""당신은 시니어 소프트웨어 엔지니어입니다.
코드 diff를 검토하고 다음을 확인하세요:
1. 논리적 오류
2. 엣지 케이스 미처리
3. 보안 취약점
4. 성능 문제
5. 테스트 누락

출력: JSON {"approved": bool, "issues": [...], "suggestions": [...]}""",
            messages=[{"role": "user", "content": f"코드 리뷰 요청:\n{diff}"}]
        )
        return response.content[0].text

    def review_pr(self, pr_diff: str, test_file: str) -> dict:
        """PR 전체 검증"""
        test_result = self.run_tests(test_file)
        review_raw = self.code_review(pr_diff)
        
        try:
            review_json = json.loads(review_raw)
        except:
            review_json = {"approved": False, "issues": ["Review format error"]}

        return {
            "tests_passed": test_result["passed"],
            "test_output": test_result["output"],
            "code_review": review_json,
            "approved": test_result["passed"] and review_json.get("approved", False)
        }
