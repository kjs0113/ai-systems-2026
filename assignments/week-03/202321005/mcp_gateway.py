"""
FastAPI 기반 Governed MCP Gateway 프록시

인바운드/아웃바운드 검열을 포함한 MCP 요청 게이트웨이.
- 인바운드: 요청 검증, TBAC 권한 확인, 프롬프트 인젝션 탐지
- 아웃바운드: 응답 필터링, 민감정보 마스킹, 감사 로그
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# stderr 로깅
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-gateway")

app = FastAPI(
    title="Governed MCP Gateway",
    description="MCP 요청을 검증하고 라우팅하는 게이트웨이 프록시",
    version="1.0.0",
)


# ── 데이터 모델 ──────────────────────────────────────────────────────

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str
    result: Any = None
    error: dict[str, Any] | None = None


class GatewayPolicy(BaseModel):
    """TBAC 게이트웨이 정책."""
    role: str
    allowed_methods: list[str]
    allowed_tools: list[str]
    max_requests_per_minute: int = 60
    blocked_patterns: list[str] = Field(default_factory=list)


# ── 정책 정의 ────────────────────────────────────────────────────────

POLICIES: dict[str, GatewayPolicy] = {
    "student": GatewayPolicy(
        role="student",
        allowed_methods=["tools/list", "tools/call", "resources/read", "prompts/list", "prompts/get"],
        allowed_tools=["get_mig_status", "get_gpu_metrics", "set_session_role"],
        max_requests_per_minute=30,
        blocked_patterns=[
            r"admin_",        # admin 도구 접근 차단
            r"reset",         # 리셋 명령 차단
            r"delete",        # 삭제 명령 차단
            r"DROP\s+TABLE",  # SQL 인젝션 패턴
        ],
    ),
    "researcher": GatewayPolicy(
        role="researcher",
        allowed_methods=["tools/list", "tools/call", "resources/read", "prompts/list", "prompts/get"],
        allowed_tools=["get_mig_status", "get_gpu_metrics", "analyze_gpu_usage", "set_session_role"],
        max_requests_per_minute=60,
        blocked_patterns=[r"admin_", r"reset", r"DROP\s+TABLE"],
    ),
    "admin": GatewayPolicy(
        role="admin",
        allowed_methods=["tools/list", "tools/call", "resources/read", "resources/list",
                         "prompts/list", "prompts/get"],
        allowed_tools=["*"],  # 전체 허용
        max_requests_per_minute=120,
        blocked_patterns=[r"DROP\s+TABLE"],
    ),
}

# ── Rate Limiter ─────────────────────────────────────────────────────

_request_log: dict[str, list[float]] = {}


def check_rate_limit(role: str, limit: int) -> bool:
    now = time.time()
    if role not in _request_log:
        _request_log[role] = []
    _request_log[role] = [t for t in _request_log[role] if now - t < 60]
    if len(_request_log[role]) >= limit:
        return False
    _request_log[role].append(now)
    return True


# ── 프롬프트 인젝션 탐지 패턴 ────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore\s+(previous|all)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"IMPORTANT:\s*ignore",
    r"forget\s+(everything|all|your\s+instructions)",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if",
    r"override\s+(your|the)\s+(instructions|rules|safety)",
    r"jailbreak",
    r"DAN\s+mode",
]


def detect_prompt_injection(text: str) -> list[str]:
    """텍스트에서 프롬프트 인젝션 패턴을 탐지."""
    findings = []
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(f"Detected injection pattern: {pattern}")
    return findings


# ── 인바운드 검열 ────────────────────────────────────────────────────

def inbound_censor(request: MCPRequest, policy: GatewayPolicy) -> list[str]:
    """인바운드 요청 검열. 위반 사항 목록 반환."""
    violations = []

    # 1. 허용된 메서드인지 확인
    if request.method not in policy.allowed_methods:
        violations.append(f"Method '{request.method}' not allowed for role '{policy.role}'")

    # 2. 도구 호출 시 허용된 도구인지 확인
    if request.method == "tools/call":
        tool_name = request.params.get("name", "")
        if "*" not in policy.allowed_tools and tool_name not in policy.allowed_tools:
            violations.append(f"Tool '{tool_name}' not allowed for role '{policy.role}'")

        # 차단 패턴 검사
        for pattern in policy.blocked_patterns:
            if re.search(pattern, tool_name, re.IGNORECASE):
                violations.append(f"Tool name matches blocked pattern: {pattern}")

    # 3. 파라미터에서 프롬프트 인젝션 탐지
    params_str = json.dumps(request.params)
    injections = detect_prompt_injection(params_str)
    violations.extend(injections)

    return violations


# ── 아웃바운드 검열 ──────────────────────────────────────────────────

SENSITIVE_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "***-**-****"),           # SSN
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+", "[CREDENTIAL_REDACTED]"),
    (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CARD_REDACTED]"),  # 카드번호
]


def outbound_censor(response_data: Any) -> Any:
    """아웃바운드 응답에서 민감정보 마스킹."""
    if isinstance(response_data, str):
        for pattern, replacement in SENSITIVE_PATTERNS:
            response_data = re.sub(pattern, replacement, response_data)
        return response_data
    elif isinstance(response_data, dict):
        return {k: outbound_censor(v) for k, v in response_data.items()}
    elif isinstance(response_data, list):
        return [outbound_censor(item) for item in response_data]
    return response_data


# ── 감사 로그 ────────────────────────────────────────────────────────

def audit_log(role: str, method: str, tool: str | None, allowed: bool, violations: list[str]):
    """감사 로그를 stderr로 기록."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "role": role,
        "method": method,
        "tool": tool,
        "allowed": allowed,
        "violations": violations,
    }
    logger.info("AUDIT: %s", json.dumps(entry, ensure_ascii=False))


# ── API 엔드포인트 ──────────────────────────────────────────────────

@app.post("/mcp/v1")
async def mcp_proxy(request: Request):
    """MCP JSON-RPC 요청을 수신하여 검열 후 라우팅한다."""
    # 역할은 헤더에서 추출 (실제로는 JWT에서)
    role = request.headers.get("X-MCP-Role", "student").lower()
    policy = POLICIES.get(role)
    if not policy:
        raise HTTPException(status_code=403, detail=f"Unknown role: {role}")

    # Rate limit 검사
    if not check_rate_limit(role, policy.max_requests_per_minute):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {policy.max_requests_per_minute}/min for {role}",
        )

    # 요청 파싱
    try:
        body = await request.json()
        mcp_req = MCPRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid MCP request: {e}")

    # 인바운드 검열
    violations = inbound_censor(mcp_req, policy)
    tool_name = mcp_req.params.get("name") if mcp_req.method == "tools/call" else None

    if violations:
        audit_log(role, mcp_req.method, tool_name, allowed=False, violations=violations)
        return JSONResponse(
            status_code=403,
            content=MCPResponse(
                id=mcp_req.id,
                error={
                    "code": -32600,
                    "message": "Request blocked by gateway policy",
                    "data": {"violations": violations},
                },
            ).model_dump(),
        )

    audit_log(role, mcp_req.method, tool_name, allowed=True, violations=[])

    # 실제로는 여기서 백엔드 MCP 서버로 프록시
    # 데모에서는 mock 응답 반환
    mock_result = {
        "status": "proxied",
        "method": mcp_req.method,
        "role": role,
        "message": "Request passed gateway validation and would be forwarded to MCP server.",
    }

    # 아웃바운드 검열
    censored_result = outbound_censor(mock_result)

    return JSONResponse(
        content=MCPResponse(
            id=mcp_req.id,
            result=censored_result,
        ).model_dump(),
    )


@app.get("/gateway/policies")
async def list_policies():
    """등록된 게이트웨이 정책 목록."""
    return {
        role: {
            "allowed_methods": p.allowed_methods,
            "allowed_tools": p.allowed_tools,
            "rate_limit": p.max_requests_per_minute,
            "blocked_patterns_count": len(p.blocked_patterns),
        }
        for role, p in POLICIES.items()
    }


@app.get("/gateway/health")
async def health():
    return {"status": "healthy", "service": "Governed MCP Gateway"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
