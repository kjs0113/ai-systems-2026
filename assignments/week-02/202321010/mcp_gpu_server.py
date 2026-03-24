"""
FastMCP GPU Monitor Server with Security Hardening
Lab 03: MCP 서버 구현과 보안 검증

보안 기능:
- 입력 검증 (GPU 인덱스, 파라미터 범위)
- 안전한 에러 반환 (구조화된 JSON 응답)
- 에러 코드 표준화 (ErrorCode 클래스)
- TBAC 권한 체크 (Role-Based Access Control)
- stderr 전용 로깅 (stdout 오염 방지)
- pynvml 초기화 실패 안전 처리
"""

import sys
import os
import logging
from typing import Optional

# 환경 변수 설정 (FastMCP 배너 억제)
os.environ['FASTMCP_QUIET'] = '1'
os.environ['NO_COLOR'] = '1'

# CRITICAL: stdout 오염 방지 - stderr로만 로깅
root_logger = logging.getLogger()
root_logger.handlers.clear()
root_logger.setLevel(logging.INFO)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
root_logger.addHandler(stderr_handler)

logger = logging.getLogger(__name__)

# pynvml 안전한 import 및 초기화
nvml_initialized = False
nvml_init_error: Optional[str] = None

try:
    import pynvml
    NVMLError = pynvml.NVMLError
    pynvml.nvmlInit()
    nvml_initialized = True
    logger.info("pynvml initialized successfully")
except ImportError:
    pynvml = None  # type: ignore
    class NVMLError(Exception):
        """Fallback NVMLError when pynvml not available"""
        pass
    nvml_init_error = "pynvml not installed. Install with: pip install pynvml"
    logger.error(f"✗ {nvml_init_error}")
except Exception as e:
    nvml_init_error = f"NVML initialization failed: {type(e).__name__}"
    logger.error(f"✗ {nvml_init_error}: {str(e)}")

from fastmcp import FastMCP

# FastMCP 서버 초기화
mcp = FastMCP("GPU Monitor Server")


# ============================================================================
# 에러 코드 표준화
# ============================================================================
class ErrorCode:
    """표준화된 에러 코드 상수"""
    INVALID_GPU_INDEX = "INVALID_GPU_INDEX"
    NVML_NOT_AVAILABLE = "NVML_NOT_AVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    ACCESS_DENIED = "ACCESS_DENIED"
    VALIDATION_ERROR = "VALIDATION_ERROR"


# ============================================================================
# TBAC (Task-Based Access Control) - 역할 기반 권한 관리
# ============================================================================
USER_ROLES = {
    "student": "viewer",
    "professor": "admin",
    "researcher": "power_user"
}

def check_permission(user_id: str, required_role: str = "viewer") -> tuple[bool, Optional[str]]:
    """
    사용자 권한 확인
    
    Args:
        user_id: 사용자 식별자
        required_role: 필요한 최소 역할 (viewer < power_user < admin)
        
    Returns:
        (권한 있음 여부, 에러 메시지)
    """
    role = USER_ROLES.get(user_id)
    
    if role is None:
        return False, f"Unknown user: {user_id}"
    
    # 역할 계층
    role_hierarchy = ["viewer", "power_user", "admin"]
    
    if required_role not in role_hierarchy:
        return False, f"Invalid required role: {required_role}"
    
    user_level = role_hierarchy.index(role) if role in role_hierarchy else -1
    required_level = role_hierarchy.index(required_role)
    
    if user_level < required_level:
        return False, f"Insufficient privileges. Required: {required_role}, Current: {role}"
    
    return True, None


# ============================================================================
# 응답 구조 통일 - ok/data/error 패턴
# ============================================================================
def success(data: dict) -> dict:
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        
    Returns:
        통일된 성공 응답 구조
    """
    return {
        "ok": True,
        "data": data
    }


def error(code: str, message: str) -> dict:
    """
    에러 응답 생성
    
    Args:
        code: 에러 코드 (ErrorCode 클래스 사용 권장)
        message: 에러 메시지
        
    Returns:
        통일된 에러 응답 구조
    """
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message
        }
    }


# ============================================================================
# NVML 및 입력 검증 함수
# ============================================================================
def ensure_nvml() -> None:
    """NVML 초기화 확인 - 실패 시 안전한 에러 발생"""
    if not nvml_initialized:
        raise RuntimeError(nvml_init_error or "NVML not initialized")


def validate_gpu_index(gpu_index: int) -> int:
    """
    GPU 인덱스 검증 (다층 방어)
    
    Args:
        gpu_index: 사용자 입력 GPU 인덱스
        
    Returns:
        검증된 GPU 인덱스
        
    Raises:
        ValueError: 잘못된 GPU 인덱스
        RuntimeError: NVML 미초기화
    """
    ensure_nvml()
    
    device_count = pynvml.nvmlDeviceGetCount()
    
    # 1. 타입 검증
    if not isinstance(gpu_index, int):
        raise ValueError(f"GPU index must be integer, got {type(gpu_index).__name__}")
    
    # 2. 범위 검증 (음수)
    if gpu_index < 0:
        raise ValueError(f"GPU index must be non-negative, got {gpu_index}")
    
    # 3. 범위 검증 (상한)
    if gpu_index >= device_count:
        raise ValueError(
            f"GPU index {gpu_index} out of range. Available GPUs: 0-{device_count - 1}"
        )
    
    return gpu_index


# ============================================================================
# MCP Tools
# ============================================================================
@mcp.tool()
def list_gpus(user_id: str = "student") -> dict:
    """
    시스템의 모든 GPU 목록 조회
    
    Args:
        user_id: 사용자 식별자 (권한 확인용)
    
    Returns:
        GPU 목록과 기본 정보
    """
    # TBAC 권한 체크
    has_permission, perm_error = check_permission(user_id, "viewer")
    if not has_permission:
        return error(ErrorCode.ACCESS_DENIED, perm_error)
    
    try:
        ensure_nvml()
        
        device_count = pynvml.nvmlDeviceGetCount()
        gpus = []
        
        for i in range(device_count):
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                
                # pynvml 버전에 따라 bytes 또는 str 반환
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                gpus.append({
                    "index": i,
                    "name": name
                })
            except Exception as e:
                logger.warning(f"Failed to get info for GPU {i}: {e}")
                gpus.append({
                    "index": i,
                    "name": "Unknown (query failed)"
                })
        
        return success({
            "gpu_count": device_count,
            "gpus": gpus
        })
    
    except RuntimeError as e:
        # NVML 초기화 실패
        logger.error(f"NVML not available: {e}")
        return error(ErrorCode.NVML_NOT_AVAILABLE, str(e))
    
    except Exception as e:
        # 예상치 못한 내부 에러 - 상세 정보 노출 방지
        logger.error(f"list_gpus failed: {e}", exc_info=True)
        return error(ErrorCode.INTERNAL_ERROR, "Internal server error occurred")


@mcp.tool()
def get_gpu_info(user_id: str, gpu_index: int) -> dict:
    """
    특정 GPU의 상세 정보 조회
    
    Args:
        user_id: 사용자 식별자 (권한 확인용)
        gpu_index: GPU 인덱스 (0부터 시작)
        
    Returns:
        GPU 상세 정보
    """
    # TBAC 권한 체크
    has_permission, perm_error = check_permission(user_id, "viewer")
    if not has_permission:
        return error(ErrorCode.ACCESS_DENIED, perm_error)
    
    try:
        # 입력 검증
        gpu_index = validate_gpu_index(gpu_index)
        
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        
        # GPU 이름
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        
        # 메모리 정보
        try:
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory = {
                "total_mb": round(mem_info.total / 1024**2, 2),
                "used_mb": round(mem_info.used / 1024**2, 2),
                "free_mb": round(mem_info.free / 1024**2, 2),
                "utilization_percent": round((mem_info.used / mem_info.total) * 100, 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get memory info: {e}")
            memory = {"error": "unavailable"}
        
        # 온도 정보
        try:
            temperature = pynvml.nvmlDeviceGetTemperature(
                handle, 
                pynvml.NVML_TEMPERATURE_GPU
            )
        except Exception as e:
            logger.warning(f"Failed to get temperature: {e}")
            temperature = None
        
        # 전력 정보
        try:
            power_mw = pynvml.nvmlDeviceGetPowerUsage(handle)
            power_watts = round(power_mw / 1000.0, 2)
        except Exception as e:
            logger.warning(f"Failed to get power usage: {e}")
            power_watts = None
        
        # GPU 사용률
        try:
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_utilization = utilization.gpu
        except Exception as e:
            logger.warning(f"Failed to get utilization: {e}")
            gpu_utilization = None
        
        return success({
            "gpu_index": gpu_index,
            "name": name,
            "memory": memory,
            "temperature_celsius": temperature,
            "power_watts": power_watts,
            "gpu_utilization_percent": gpu_utilization
        })
    
    except ValueError as e:
        # 입력 검증 실패 - 사용자에게 명확한 피드백
        logger.warning(f"Validation error: {e}")
        return error(ErrorCode.INVALID_GPU_INDEX, str(e))
    
    except RuntimeError as e:
        # NVML 초기화 실패
        logger.error(f"NVML not available: {e}")
        return error(ErrorCode.NVML_NOT_AVAILABLE, str(e))
    
    except Exception as e:
        # 예상치 못한 에러 - 상세 정보 노출 방지
        logger.error(f"get_gpu_info failed for GPU {gpu_index}: {e}", exc_info=True)
        return error(ErrorCode.INTERNAL_ERROR, "Internal server error occurred")


@mcp.tool()
def get_mig_devices(user_id: str, gpu_index: int) -> dict:
    """
    특정 GPU의 MIG 장치 정보 조회
    
    Args:
        user_id: 사용자 식별자 (권한 확인용)
        gpu_index: GPU 인덱스 (0부터 시작)
        
    Returns:
        MIG 장치 목록 및 정보
    """
    # TBAC 권한 체크 - MIG 정보는 power_user 이상 필요
    has_permission, perm_error = check_permission(user_id, "power_user")
    if not has_permission:
        return error(ErrorCode.ACCESS_DENIED, perm_error)
    
    try:
        # 입력 검증
        gpu_index = validate_gpu_index(gpu_index)
        
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
        
        # MIG 모드 확인
        try:
            mig_mode_current, mig_mode_pending = pynvml.nvmlDeviceGetMigMode(handle)
        except Exception as e:
            logger.info(f"GPU {gpu_index} does not support MIG: {e}")
            return success({
                "gpu_index": gpu_index,
                "mig_enabled": False,
                "message": "MIG not supported or not available on this GPU"
            })
        
        if not mig_mode_current:
            return success({
                "gpu_index": gpu_index,
                "mig_enabled": False,
                "message": "MIG mode is disabled"
            })
        
        # MIG 장치 수 조회
        try:
            mig_device_count = pynvml.nvmlDeviceGetMaxMigDeviceCount(handle)
        except AttributeError:
            # 구버전 pynvml에서는 해당 함수가 없을 수 있음
            mig_device_count = 0
        
        mig_devices = []
        
        # 활성 MIG 인스턴스 조회 시도
        for i in range(mig_device_count):
            try:
                mig_handle = pynvml.nvmlDeviceGetMigDeviceHandleByIndex(
                    handle, i
                )
                
                # MIG 장치 정보 수집
                mig_info = {
                    "index": i,
                    "status": "active"
                }
                
                mig_devices.append(mig_info)
                
            except NVMLError as e:
                # 비활성 슬라이스는 에러 발생 - 정상 동작
                if hasattr(e, 'value') and e.value == pynvml.NVML_ERROR_NOT_FOUND:
                    continue
                else:
                    logger.warning(f"MIG device {i} query error: {e}")
        
        return success({
            "gpu_index": gpu_index,
            "mig_enabled": True,
            "max_mig_devices": mig_device_count,
            "active_mig_devices": len(mig_devices),
            "devices": mig_devices
        })
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return error(ErrorCode.INVALID_GPU_INDEX, str(e))
    
    except RuntimeError as e:
        logger.error(f"NVML not available: {e}")
        return error(ErrorCode.NVML_NOT_AVAILABLE, str(e))
    
    except Exception as e:
        logger.error(f"get_mig_devices failed: {e}", exc_info=True)
        return error(ErrorCode.INTERNAL_ERROR, "Internal server error occurred")


# ============================================================================
# MCP Resources
# ============================================================================
@mcp.resource("gpu://system/info")
def system_gpu_info() -> str:
    """
    시스템 GPU 정보 리소스 (읽기 전용)
    
    Returns:
        시스템의 모든 GPU 정보 (텍스트 형식)
    """
    try:
        result = list_gpus(user_id="student")
        
        if not result.get("ok"):
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return f"Error: {error_msg}"
        
        data = result["data"]
        lines = [
            f"GPU Monitoring System",
            f"=" * 50,
            f"Total GPUs: {data['gpu_count']}",
            ""
        ]
        
        for gpu in data["gpus"]:
            lines.append(f"GPU {gpu['index']}: {gpu['name']}")
        
        return "\n".join(lines)
    
    except Exception as e:
        logger.error(f"system_gpu_info resource failed: {e}")
        return f"Error: Failed to retrieve GPU information"


# ============================================================================
# Main
# ============================================================================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("FastMCP GPU Monitor Server - Starting")
    logger.info("=" * 60)
    logger.info(f"NVML Initialized: {nvml_initialized}")
    if nvml_init_error:
        logger.warning(f"NVML Error: {nvml_init_error}")
    logger.info("Logging: stderr only (stdout reserved for JSON-RPC)")
    logger.info("=" * 60)
    
    mcp.run()


