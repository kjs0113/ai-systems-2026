import concurrent.futures
import anthropic
import json
import os
from dataclasses import dataclass, asdict
from typing import Literal

@dataclass
class ReviewResult:
    dimension: str
    passed: bool
    severity: Literal["critical", "major", "minor", "info"]
    issues: list[str]
    score: int  # 0-10

class ParallelReviewer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def _call_claude(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return response.content[0].text

    def review_correctness(self, code: str, tests: str) -> ReviewResult:
        """정확성 리뷰: 논리 오류, 엣지 케이스, 테스트 충분성"""
        result = self._call_claude(
            system="""코드의 정확성만 검토하라. 스타일은 무시한다.
확인 항목: 논리 오류, 엣지 케이스 미처리, 테스트 커버리지 공백.
반드시 JSON으로 응답하라: {"score": 0-10, "severity": "critical|major|minor|info", "issues": [...]}""",
            user=f"코드:\n{code}\n\n테스트:\n{tests}"
        )
        data = json.loads(result)
        return ReviewResult(
            dimension="correctness",
            passed=data["score"] >= 4 and data["severity"] != "critical",
            severity=data["severity"],
            issues=data["issues"],
            score=data["score"]
        )

    def review_quality(self, code: str) -> ReviewResult:
        """품질 리뷰: 코딩 컨벤션, 가독성, 유지보수성"""
        result = self._call_claude(
            system="""코드 품질만 검토하라. 기능 정확성은 무시한다.
확인 항목: 네이밍, 함수 길이, 중복, 주석 충분성.
반드시 JSON으로 응답하라: {"score": 0-10, "severity": "critical|major|minor|info", "issues": [...]}""",
            user=f"코드:\n{code}"
        )
        data = json.loads(result)
        return ReviewResult(
            dimension="quality",
            passed=data["score"] >= 4 and data["severity"] != "critical",
            severity=data["severity"],
            issues=data["issues"],
            score=data["score"]
        )

    def review_architecture(self, code: str, context: str) -> ReviewResult:
        """아키텍처 리뷰: 설계 결정, 의존성, 확장성"""
        result = self._call_claude(
            system="""아키텍처 관점에서만 검토하라.
확인 항목: 단일 책임 원칙, 의존성 방향, 인터페이스 설계, 확장 가능성.
반드시 JSON으로 응답하라: {"score": 0-10, "severity": "critical|major|minor|info", "issues": [...]}""",
            user=f"컨텍스트:\n{context}\n\n코드:\n{code}"
        )
        data = json.loads(result)
        return ReviewResult(
            dimension="architecture",
            passed=data["score"] >= 4 and data["severity"] != "critical",
            severity=data["severity"],
            issues=data["issues"],
            score=data["score"]
        )

    def parallel_review(self, code: str, tests: str, context: str) -> dict:
        """3-병렬 리뷰 실행 및 결과 통합"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_correctness = executor.submit(self.review_correctness, code, tests)
            f_quality = executor.submit(self.review_quality, code)
            f_architecture = executor.submit(self.review_architecture, code, context)

            results = [
                f_correctness.result(),
                f_quality.result(),
                f_architecture.result()
            ]

        # 심각도 기반 PASS/FAIL 게이트
        has_critical = any(r.severity == "critical" for r in results)
        all_pass = all(r.passed for r in results)
        avg_score = sum(r.score for r in results) / len(results)

        return {
            "overall_passed": all_pass and not has_critical,
            "average_score": avg_score,
            "results": [asdict(r) for r in results],
            "blocking_issues": [
                issue
                for r in results if r.severity == "critical"
                for issue in r.issues
            ]
        }
