"""
MCP 서버 단위 테스트.

테스트 항목:
- 입력 검증 (GPU 인덱스, threshold 범위)
- TBAC 접근 제어
- 도구 정상 호출
- 에러 처리
"""

import json
import sys
import os

# venv의 모듈을 사용하기 위해 경로 추가
sys.path.insert(0, os.path.dirname(__file__))

from mcp_server import (
    validate_gpu_index,
    validate_threshold,
    check_tbac,
    set_role,
    get_mig_status,
    get_gpu_metrics,
    admin_reset_gpu,
    set_session_role,
    _mock_gpu_info,
)


# ── 입력 검증 테스트 ─────────────────────────────────────────────────

class TestInputValidation:
    """입력 검증 테스트."""

    def test_valid_gpu_index(self):
        """정상 GPU 인덱스는 에러 없이 통과."""
        validate_gpu_index(0)
        validate_gpu_index(3)
        validate_gpu_index(7)

    def test_negative_gpu_index(self):
        """음수 GPU 인덱스는 ValueError."""
        try:
            validate_gpu_index(-1)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "non-negative" in str(e)

    def test_too_large_gpu_index(self):
        """범위 초과 GPU 인덱스는 ValueError."""
        try:
            validate_gpu_index(100)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "out of range" in str(e) or "exceeds" in str(e)

    def test_invalid_gpu_index_type(self):
        """문자열 GPU 인덱스는 TypeError."""
        try:
            validate_gpu_index("abc")
            assert False, "Should have raised TypeError"
        except TypeError as e:
            assert "integer" in str(e)

    def test_valid_threshold(self):
        """정상 threshold 값은 에러 없이 통과."""
        validate_threshold(0)
        validate_threshold(50.5)
        validate_threshold(100)

    def test_negative_threshold(self):
        """음수 threshold는 ValueError."""
        try:
            validate_threshold(-10)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "between 0 and 100" in str(e)

    def test_over_100_threshold(self):
        """100 초과 threshold는 ValueError."""
        try:
            validate_threshold(200)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "between 0 and 100" in str(e)

    def test_invalid_threshold_type(self):
        """문자열 threshold는 TypeError."""
        try:
            validate_threshold("high")
            assert False, "Should have raised TypeError"
        except TypeError as e:
            assert "number" in str(e)


# ── TBAC 접근 제어 테스트 ────────────────────────────────────────────

class TestTBAC:
    """TBAC 기반 접근 제어 테스트."""

    def test_student_monitoring_allowed(self):
        """student는 monitoring 도구 사용 가능."""
        set_role("student")
        check_tbac("get_mig_status")  # 에러 없으면 통과

    def test_student_admin_denied(self):
        """student는 administration 도구 사용 불가."""
        set_role("student")
        try:
            check_tbac("admin_reset_gpu")
            assert False, "Should have raised PermissionError"
        except PermissionError as e:
            assert "not authorized" in str(e)
            assert "administration" in str(e)

    def test_admin_all_allowed(self):
        """admin은 모든 도구 사용 가능."""
        set_role("admin")
        check_tbac("get_mig_status")
        check_tbac("admin_reset_gpu")

    def test_researcher_monitoring_allowed(self):
        """researcher는 monitoring/analysis 가능."""
        set_role("researcher")
        check_tbac("get_mig_status")

    def test_researcher_admin_denied(self):
        """researcher는 administration 불가."""
        set_role("researcher")
        try:
            check_tbac("admin_reset_gpu")
            assert False, "Should have raised PermissionError"
        except PermissionError as e:
            assert "not authorized" in str(e)

    def test_invalid_role(self):
        """존재하지 않는 역할은 ValueError."""
        try:
            set_role("superuser")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid role" in str(e)


# ── 도구 호출 테스트 ─────────────────────────────────────────────────

class TestTools:
    """도구 정상 호출 테스트."""

    def test_get_mig_status_returns_json(self):
        """get_mig_status는 유효한 JSON을 반환."""
        set_role("student")
        result = get_mig_status(gpu_index=0)
        data = json.loads(result)
        assert "gpu_index" in data
        assert data["gpu_index"] == 0

    def test_get_mig_status_invalid_index(self):
        """잘못된 인덱스에 안전한 에러 JSON 반환."""
        set_role("student")
        result = get_mig_status(gpu_index=-5)
        data = json.loads(result)
        assert data["error"] == "validation_error"

    def test_get_gpu_metrics_with_alerts(self):
        """threshold를 낮게 설정하면 alert 발생."""
        set_role("student")
        result = get_gpu_metrics(gpu_index=0, threshold_pct=10.0)
        data = json.loads(result)
        assert "alerts" in data
        assert data["alert_count"] > 0

    def test_get_gpu_metrics_invalid_threshold(self):
        """범위 밖 threshold에 안전한 에러 반환."""
        set_role("student")
        result = get_gpu_metrics(gpu_index=0, threshold_pct=-10)
        data = json.loads(result)
        assert data["error"] == "validation_error"

    def test_get_gpu_metrics_threshold_200(self):
        """threshold 200에 안전한 에러 반환."""
        set_role("student")
        result = get_gpu_metrics(gpu_index=0, threshold_pct=200)
        data = json.loads(result)
        assert data["error"] == "validation_error"

    def test_admin_reset_denied_for_student(self):
        """student가 admin_reset_gpu 호출 시 permission_denied."""
        set_role("student")
        result = admin_reset_gpu(gpu_index=0)
        data = json.loads(result)
        assert data["error"] == "permission_denied"

    def test_admin_reset_allowed_for_admin(self):
        """admin은 admin_reset_gpu 호출 가능."""
        set_role("admin")
        result = admin_reset_gpu(gpu_index=0)
        data = json.loads(result)
        assert data["status"] == "success"

    def test_set_session_role_valid(self):
        """유효한 역할 설정."""
        result = set_session_role(role="researcher")
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["role"] == "researcher"

    def test_set_session_role_invalid(self):
        """존재하지 않는 역할 설정 시 에러."""
        result = set_session_role(role="hacker")
        data = json.loads(result)
        assert data["error"] == "validation_error"


# ── Mock 데이터 테스트 ───────────────────────────────────────────────

class TestMockData:
    """Mock 데이터 구조 검증."""

    def test_mock_gpu_info_structure(self):
        """Mock 데이터가 올바른 구조를 가짐."""
        info = _mock_gpu_info(0)
        assert info["gpu_index"] == 0
        assert info["mig_mode"] is True
        assert len(info["mig_instances"]) == 7
        assert info["_mock"] is True

    def test_mock_mig_instances(self):
        """MIG 인스턴스가 7개이고 올바른 프로파일."""
        info = _mock_gpu_info(0)
        for inst in info["mig_instances"]:
            assert inst["profile"] == "1g.10gb"
            assert inst["sm_count"] == 16
            assert inst["memory_gb"] == 10


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)
