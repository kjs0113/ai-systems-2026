"""
FastMCP 서버: MIG GPU 모니터링 + TBAC 접근 제어

3대 MCP 프리미티브 (Tools, Resources, Prompts) 구현:
- Tools: get_mig_status, get_gpu_metrics, admin_reset_gpu
- Resources: mig://gpu/{id}/status, mig://gpu/{id}/metrics
- Prompts: gpu_analysis_prompt

보안 기능:
- 입력 검증 (GPU 인덱스, threshold 범위)
- pynvml 초기화 실패 안전 처리
- TBAC (Task-Based Access Control) 3계층
- stderr 로깅 (stdout 오염 방지)
"""

from __future__ import annotations

import json
import logging
import sys
from contextlib import contextmanager
from enum import Enum
from typing import Any

from fastmcp import FastMCP

# ── stderr 로깅 설정 (stdout 오염 방지) ──────────────────────────────
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-mig-server")

# ── pynvml 안전 초기화 ──────────────────────────────────────────────
_nvml_available = False
try:
    import pynvml

    pynvml.nvmlInit()
    _nvml_available = True
    logger.info("pynvml initialized successfully")
except Exception as e:
    logger.warning("pynvml initialization failed: %s (using mock data)", e)


def _nvml_shutdown():
    if _nvml_available:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass


@contextmanager
def _safe_nvml():
    """pynvml 호출을 안전하게 감싸는 컨텍스트 매니저."""
    if not _nvml_available:
        raise RuntimeError(
            "NVML not available. "
            "Ensure NVIDIA drivers are installed and GPU is accessible."
        )
    yield


# ── TBAC (Task-Based Access Control) ────────────────────────────────

class Role(str, Enum):
    STUDENT = "student"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class TaskCategory(str, Enum):
    MONITORING = "monitoring"        # 조회 전용
    ANALYSIS = "analysis"            # 분석 작업
    ADMINISTRATION = "administration"  # 관리 작업 (리셋 등)


# 역할별 허용 태스크 카테고리
ROLE_PERMISSIONS: dict[Role, set[TaskCategory]] = {
    Role.STUDENT: {TaskCategory.MONITORING, TaskCategory.ANALYSIS},
    Role.RESEARCHER: {TaskCategory.MONITORING, TaskCategory.ANALYSIS},
    Role.ADMIN: {TaskCategory.MONITORING, TaskCategory.ANALYSIS, TaskCategory.ADMINISTRATION},
}

# 도구별 태스크 카테고리 매핑
TOOL_TASK_MAP: dict[str, TaskCategory] = {
    "get_mig_status": TaskCategory.MONITORING,
    "get_gpu_metrics": TaskCategory.MONITORING,
    "analyze_gpu_usage": TaskCategory.ANALYSIS,
    "admin_reset_gpu": TaskCategory.ADMINISTRATION,
}

# 현재 세션의 역할 (실제 환경에서는 JWT/토큰으로 결정)
_current_role: Role = Role.STUDENT


def set_role(role: str) -> None:
    """세션 역할 설정."""
    global _current_role
    try:
        _current_role = Role(role.lower())
        logger.info("Role set to: %s", _current_role.value)
    except ValueError:
        raise ValueError(f"Invalid role: {role}. Must be one of: {[r.value for r in Role]}")


def check_tbac(tool_name: str) -> None:
    """TBAC 기반 접근 제어 검사. 거부 시 PermissionError."""
    task_category = TOOL_TASK_MAP.get(tool_name)
    if task_category is None:
        logger.warning("Unknown tool for TBAC check: %s", tool_name)
        return

    allowed = ROLE_PERMISSIONS.get(_current_role, set())
    if task_category not in allowed:
        logger.warning(
            "TBAC DENIED: role=%s, tool=%s, category=%s",
            _current_role.value, tool_name, task_category.value,
        )
        raise PermissionError(
            f"Access denied. Role '{_current_role.value}' is not authorized "
            f"for '{task_category.value}' tasks. "
            f"Tool '{tool_name}' requires '{task_category.value}' permission."
        )
    logger.info(
        "TBAC ALLOWED: role=%s, tool=%s, category=%s",
        _current_role.value, tool_name, task_category.value,
    )


# ── 입력 검증 ───────────────────────────────────────────────────────

def validate_gpu_index(gpu_index: int) -> None:
    """GPU 인덱스 유효성 검사."""
    if not isinstance(gpu_index, int):
        raise TypeError(f"gpu_index must be an integer, got {type(gpu_index).__name__}")
    if gpu_index < 0:
        raise ValueError(f"gpu_index must be non-negative, got {gpu_index}")
    if _nvml_available:
        count = pynvml.nvmlDeviceGetCount()
        if gpu_index >= count:
            raise ValueError(
                f"gpu_index {gpu_index} out of range. "
                f"Available GPUs: 0-{count - 1} ({count} total)"
            )
    elif gpu_index > 7:
        raise ValueError(f"gpu_index {gpu_index} exceeds maximum expected GPU count (8)")


def validate_threshold(threshold_pct: float) -> None:
    """threshold_pct 범위 검증 (0-100)."""
    if not isinstance(threshold_pct, (int, float)):
        raise TypeError(f"threshold_pct must be a number, got {type(threshold_pct).__name__}")
    if threshold_pct < 0 or threshold_pct > 100:
        raise ValueError(
            f"threshold_pct must be between 0 and 100, got {threshold_pct}. "
            "Provide a percentage value (e.g., 80 for 80%)."
        )


# ── Mock 데이터 (pynvml 사용 불가 시) ──────────────────────────────

def _mock_gpu_info(gpu_index: int) -> dict[str, Any]:
    return {
        "gpu_index": gpu_index,
        "name": f"NVIDIA H100 80GB HBM3 (Mock GPU {gpu_index})",
        "mig_mode": True,
        "mig_instances": [
            {
                "gi_id": i,
                "profile": "1g.10gb",
                "sm_count": 16,
                "memory_gb": 10,
                "memory_used_gb": round(2.5 + i * 0.3, 1),
                "memory_free_gb": round(7.5 - i * 0.3, 1),
            }
            for i in range(7)
        ],
        "temperature_c": 45,
        "power_draw_w": 250,
        "power_limit_w": 700,
        "driver_version": "560.35.03 (mock)",
        "cuda_version": "12.6 (mock)",
        "_mock": True,
    }


def _real_gpu_info(gpu_index: int) -> dict[str, Any]:
    """pynvml로 실제 GPU 정보를 수집."""
    handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
    name = pynvml.nvmlDeviceGetName(handle)

    # MIG 모드 확인
    try:
        current_mode, _ = pynvml.nvmlDeviceGetMigMode(handle)
        mig_enabled = current_mode == pynvml.NVML_DEVICE_MIG_ENABLE
    except pynvml.NVMLError:
        mig_enabled = False

    # MIG 인스턴스 정보
    mig_instances = []
    if mig_enabled:
        try:
            max_count = pynvml.nvmlDeviceGetMaxMigDeviceCount(handle)
            for i in range(max_count):
                try:
                    mig_handle = pynvml.nvmlDeviceGetMigDeviceHandleByIndex(handle, i)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(mig_handle)
                    mig_instances.append({
                        "gi_id": i,
                        "memory_total_gb": round(mem_info.total / (1024**3), 1),
                        "memory_used_gb": round(mem_info.used / (1024**3), 1),
                        "memory_free_gb": round(mem_info.free / (1024**3), 1),
                    })
                except pynvml.NVMLError:
                    continue
        except pynvml.NVMLError:
            pass

    # 온도, 전력
    try:
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
    except pynvml.NVMLError:
        temp = None

    try:
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # mW → W
        power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
    except pynvml.NVMLError:
        power, power_limit = None, None

    driver = pynvml.nvmlSystemGetDriverVersion()
    cuda_ver = pynvml.nvmlSystemGetCudaDriverVersion_v2()

    return {
        "gpu_index": gpu_index,
        "name": name,
        "mig_mode": mig_enabled,
        "mig_instances": mig_instances,
        "temperature_c": temp,
        "power_draw_w": round(power, 1) if power else None,
        "power_limit_w": round(power_limit, 1) if power_limit else None,
        "driver_version": driver,
        "cuda_version": f"{cuda_ver // 1000}.{(cuda_ver % 1000) // 10}",
        "_mock": False,
    }


def get_gpu_info(gpu_index: int) -> dict[str, Any]:
    """GPU 정보 반환 (실제 또는 mock)."""
    if _nvml_available:
        return _real_gpu_info(gpu_index)
    return _mock_gpu_info(gpu_index)


# ── FastMCP 서버 정의 ───────────────────────────────────────────────

mcp = FastMCP(
    "MIG GPU Monitor",
    instructions="NVIDIA MIG GPU 모니터링 및 관리 서버 (TBAC 접근 제어 포함)",
)


# ── Tools ────────────────────────────────────────────────────────────

@mcp.tool()
def get_mig_status(gpu_index: int = 0) -> str:
    """
    지정된 GPU의 MIG 상태를 조회한다.
    MIG 인스턴스 목록, 메모리 사용량, 프로파일 정보를 반환한다.

    Args:
        gpu_index: GPU 인덱스 (0부터 시작, 기본값 0)
    """
    try:
        check_tbac("get_mig_status")
        validate_gpu_index(gpu_index)
        info = get_gpu_info(gpu_index)
        return json.dumps(info, indent=2, ensure_ascii=False)
    except (ValueError, TypeError) as e:
        logger.error("Input validation error in get_mig_status: %s", e)
        return json.dumps({"error": "validation_error", "message": str(e)})
    except PermissionError as e:
        logger.error("TBAC error in get_mig_status: %s", e)
        return json.dumps({"error": "permission_denied", "message": str(e)})
    except RuntimeError as e:
        logger.error("Runtime error in get_mig_status: %s", e)
        return json.dumps({"error": "runtime_error", "message": str(e)})
    except Exception as e:
        logger.error("Unexpected error in get_mig_status: %s", e)
        return json.dumps({"error": "internal_error", "message": "An unexpected error occurred."})


@mcp.tool()
def get_gpu_metrics(gpu_index: int = 0, threshold_pct: float = 80.0) -> str:
    """
    GPU 메트릭(메모리 사용률, 온도, 전력)을 조회하고,
    threshold_pct를 초과하는 항목에 경고를 표시한다.

    Args:
        gpu_index: GPU 인덱스 (0부터 시작)
        threshold_pct: 경고 임계값 퍼센트 (0-100, 기본값 80)
    """
    try:
        check_tbac("get_gpu_metrics")
        validate_gpu_index(gpu_index)
        validate_threshold(threshold_pct)

        info = get_gpu_info(gpu_index)
        alerts = []

        # MIG 인스턴스 메모리 사용률 체크
        for inst in info.get("mig_instances", []):
            used = inst.get("memory_used_gb", 0)
            total = used + inst.get("memory_free_gb", 0)
            if total > 0:
                usage_pct = (used / total) * 100
                inst["memory_usage_pct"] = round(usage_pct, 1)
                if usage_pct > threshold_pct:
                    alerts.append(
                        f"MIG instance {inst['gi_id']}: memory usage "
                        f"{usage_pct:.1f}% > threshold {threshold_pct}%"
                    )

        # 온도/전력 체크
        if info.get("temperature_c") and info["temperature_c"] > threshold_pct:
            alerts.append(
                f"GPU temperature {info['temperature_c']}°C > threshold {threshold_pct}%"
            )

        if info.get("power_draw_w") and info.get("power_limit_w"):
            power_pct = (info["power_draw_w"] / info["power_limit_w"]) * 100
            if power_pct > threshold_pct:
                alerts.append(
                    f"Power usage {power_pct:.1f}% > threshold {threshold_pct}%"
                )

        result = {
            "gpu_index": gpu_index,
            "threshold_pct": threshold_pct,
            "metrics": info,
            "alerts": alerts,
            "alert_count": len(alerts),
        }
        return json.dumps(result, indent=2, ensure_ascii=False)
    except (ValueError, TypeError) as e:
        logger.error("Input validation error in get_gpu_metrics: %s", e)
        return json.dumps({"error": "validation_error", "message": str(e)})
    except PermissionError as e:
        logger.error("TBAC error: %s", e)
        return json.dumps({"error": "permission_denied", "message": str(e)})
    except RuntimeError as e:
        logger.error("Runtime error: %s", e)
        return json.dumps({"error": "runtime_error", "message": str(e)})
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return json.dumps({"error": "internal_error", "message": "An unexpected error occurred."})


@mcp.tool()
def admin_reset_gpu(gpu_index: int = 0) -> str:
    """
    [ADMINISTRATION] GPU MIG 인스턴스를 리셋한다.
    admin 역할만 실행 가능하다. student/researcher 역할은 거부된다.

    Args:
        gpu_index: 리셋할 GPU 인덱스
    """
    try:
        check_tbac("admin_reset_gpu")
        validate_gpu_index(gpu_index)
        # 실제 리셋은 수행하지 않음 (안전)
        return json.dumps({
            "status": "success",
            "message": f"GPU {gpu_index} MIG reset simulated (dry-run).",
            "role": _current_role.value,
        })
    except PermissionError as e:
        logger.error("TBAC DENIED for admin_reset_gpu: %s", e)
        return json.dumps({"error": "permission_denied", "message": str(e)})
    except (ValueError, TypeError) as e:
        logger.error("Validation error: %s", e)
        return json.dumps({"error": "validation_error", "message": str(e)})
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return json.dumps({"error": "internal_error", "message": "An unexpected error occurred."})


@mcp.tool()
def set_session_role(role: str) -> str:
    """
    현재 세션의 TBAC 역할을 설정한다.
    사용 가능한 역할: student, researcher, admin

    Args:
        role: 역할 이름 (student / researcher / admin)
    """
    try:
        set_role(role)
        permissions = [tc.value for tc in ROLE_PERMISSIONS[_current_role]]
        return json.dumps({
            "status": "success",
            "role": _current_role.value,
            "permissions": permissions,
        })
    except ValueError as e:
        return json.dumps({"error": "validation_error", "message": str(e)})


# ── Resources ────────────────────────────────────────────────────────

@mcp.resource("mig://gpu/{gpu_id}/status")
def gpu_status_resource(gpu_id: int) -> str:
    """GPU의 현재 MIG 상태 리소스. 메모리 사용량 포함."""
    try:
        validate_gpu_index(gpu_id)
        info = get_gpu_info(gpu_id)
        return json.dumps(info, indent=2, ensure_ascii=False)
    except (ValueError, TypeError, RuntimeError) as e:
        return json.dumps({"error": str(e)})


@mcp.resource("mig://gpu/{gpu_id}/metrics")
def gpu_metrics_resource(gpu_id: int) -> str:
    """GPU 메트릭 리소스 템플릿 (메모리, 온도, 전력 실시간 수집)."""
    try:
        validate_gpu_index(gpu_id)
        info = get_gpu_info(gpu_id)
        metrics = {
            "gpu_index": gpu_id,
            "temperature_c": info.get("temperature_c"),
            "power_draw_w": info.get("power_draw_w"),
            "power_limit_w": info.get("power_limit_w"),
            "mig_instances": [
                {
                    "gi_id": inst.get("gi_id"),
                    "memory_used_gb": inst.get("memory_used_gb"),
                    "memory_free_gb": inst.get("memory_free_gb"),
                    "memory_total_gb": round(
                        inst.get("memory_used_gb", 0) + inst.get("memory_free_gb", 0), 1
                    ),
                }
                for inst in info.get("mig_instances", [])
            ],
        }
        return json.dumps(metrics, indent=2, ensure_ascii=False)
    except (ValueError, TypeError, RuntimeError) as e:
        return json.dumps({"error": str(e)})


# ── Prompts ──────────────────────────────────────────────────────────

@mcp.prompt()
def gpu_analysis_prompt(gpu_index: int = 0) -> str:
    """
    GPU 사용 현황을 분석하는 프롬프트를 생성한다.
    MIG 인스턴스 상태를 포함하여 최적화 제안을 요청한다.
    """
    try:
        validate_gpu_index(gpu_index)
        info = get_gpu_info(gpu_index)
        gpu_data = json.dumps(info, indent=2, ensure_ascii=False)
    except Exception as e:
        gpu_data = json.dumps({"error": str(e)})

    return f"""다음 GPU 상태 데이터를 분석하고 최적화 방안을 제시해주세요.

## GPU 상태 데이터
```json
{gpu_data}
```

## 분석 요청사항
1. 각 MIG 인스턴스의 메모리 사용률을 계산하고, 과다 사용 인스턴스를 식별하세요.
2. 현재 MIG 프로파일 구성(1g.10gb × 7)이 워크로드에 적합한지 평가하세요.
3. 메모리/SM/L2캐시 관점에서 프로파일 재구성이 필요하면 대안을 제시하세요.
4. 온도와 전력 사용량이 정상 범위인지 확인하세요.
5. Kubernetes 스케줄링 관점에서 리소스 요청량 조정이 필요한지 제안하세요.
"""


# ── 서버 실행 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import atexit
    atexit.register(_nvml_shutdown)
    logger.info("Starting MIG GPU Monitor MCP server...")
    mcp.run()
