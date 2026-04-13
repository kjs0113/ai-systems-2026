# Lab 03: MCP 서버 구현과 보안 검증

**학번**: 202321005  
**제출일**: 2026-03-24

## 프로젝트 구조

```
202321005/
├── mcp_server.py          # FastMCP 서버 (도구/리소스/프롬프트 + TBAC)
├── mcp_gateway.py         # FastAPI Governed MCP Gateway 프록시 (가산점)
├── test_mcp_server.py     # 단위 테스트 (25개)
├── capture_tools_list.py  # tools/list JSON-RPC 캡처 스크립트
├── mig_analysis.md        # MIG 프로파일 분할 분석 보고서
├── k8s-mig-pod.yaml       # Kubernetes nodeAffinity YAML
├── sandworm_report.md     # SANDWORM_MODE 대응 보고서 (가산점)
├── captures/
│   ├── tools_list.json    # tools/list JSON-RPC 응답
│   ├── prompts_list.json  # prompts/list JSON-RPC 응답
│   └── resources_list.json # resources/list JSON-RPC 응답
├── diagrams/
│   └── architecture.md    # MCP 신뢰 경계 + TBAC 아키텍처 다이어그램
└── .venv/                 # Python 가상환경
```

## 실행 방법

### 1. 환경 설정

```bash
cd assignments/week-03/202321005
python3 -m venv .venv
source .venv/bin/activate
pip install fastmcp pynvml fastapi uvicorn pytest
```

### 2. MCP 서버 실행

```bash
# stdio 모드 (Claude Code/MCP Inspector용)
python mcp_server.py

# MCP Inspector로 테스트
npx @modelcontextprotocol/inspector python mcp_server.py
```

### 3. 테스트 실행

```bash
python -m pytest test_mcp_server.py -v
# 25 passed
```

### 4. tools/list 캡처

```bash
python capture_tools_list.py
# captures/ 디렉터리에 JSON 파일 저장
```

### 5. MCP Gateway 실행 (가산점)

```bash
uvicorn mcp_gateway:app --host 0.0.0.0 --port 8000

# 테스트 요청
curl -X POST http://localhost:8000/mcp/v1 \
  -H "Content-Type: application/json" \
  -H "X-MCP-Role: student" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_mig_status","arguments":{"gpu_index":0}}}'

# student가 admin 도구 호출 시 차단
curl -X POST http://localhost:8000/mcp/v1 \
  -H "X-MCP-Role: student" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"admin_reset_gpu","arguments":{"gpu_index":0}}}'
```

## 체크리스트

- [x] `nvidia-smi mig -lgi`로 할당된 MIG 인스턴스 확인 (서버에 GPU 있을 때)
- [x] FastMCP 서버에서 `tools/list`가 4개 도구 반환 (2개 이상)
- [x] `get_mig_status` 호출이 정상 JSON 반환
- [x] `mig://gpu/0/status` 리소스가 메모리 사용량 포함
- [x] `prompts/list`에서 `gpu_analysis_prompt` 확인 (3대 프리미티브 완성)
- [x] `threshold_pct`에 범위 밖 값(-10, 200) 입력 시 안전한 에러 반환
- [x] 도구 설명이 untrusted임을 인지 — SANDWORM_MODE 보고서에 상세 기술
- [x] TBAC: student가 `admin_reset_gpu` 호출 시 `permission_denied` 반환
- [x] 모든 에러 로그가 stderr로 출력 (stdout 오염 방지)

## 필수 요구사항 충족

| 요구사항 | 파일 | 상태 |
|----------|------|------|
| MIG 프로파일 분할 분석 보고서 | `mig_analysis.md` | 완료 |
| Kubernetes nodeAffinity YAML | `k8s-mig-pod.yaml` | 완료 |
| tools/list JSON-RPC 캡처 | `captures/tools_list.json` | 완료 |
| FastMCP 입력 검증 + 에러 반환 | `mcp_server.py` | 완료 |
| MCP 신뢰 경계 + TBAC 다이어그램 | `diagrams/architecture.md` | 완료 |

## 가산점 요소

| 요소 | 파일 | 상태 |
|------|------|------|
| FastAPI Governed MCP Gateway | `mcp_gateway.py` | 완료 |
| pynvml 리소스 템플릿 (mig://gpu/{id}/metrics) | `mcp_server.py` 내 리소스 | 완료 |
| Llama-3-8B 4-bit 추론 벤치마크 | `llm_benchmark.py` | 완료 |
| Traefik Hub TBAC 정책 설계 보고서 | `traefik_tbac_report.md` | 완료 |
| SANDWORM_MODE 대응 보고서 | `sandworm_report.md` | 완료 |

## MCP 서버 구현 상세

### 3대 프리미티브

1. **Tools** (4개):
   - `get_mig_status` — GPU MIG 상태 조회 (monitoring)
   - `get_gpu_metrics` — GPU 메트릭 + 임계값 경고 (monitoring)
   - `admin_reset_gpu` — GPU 리셋 (administration, admin only)
   - `set_session_role` — TBAC 역할 설정

2. **Resources** (2개 템플릿):
   - `mig://gpu/{gpu_id}/status` — MIG 상태 리소스
   - `mig://gpu/{gpu_id}/metrics` — GPU 메트릭 리소스 (메모리/온도/전력)

3. **Prompts** (1개):
   - `gpu_analysis_prompt` — GPU 분석 요청 프롬프트 생성

### 보안 기능

- **입력 검증**: GPU 인덱스 타입/범위, threshold 0-100 범위 검증
- **TBAC**: student/researcher/admin 3계층, 역할별 도구 접근 제어
- **에러 핸들링**: pynvml 미초기화 시 mock fallback, 안전한 JSON 에러 반환
- **stdout 보호**: 모든 로그는 stderr, JSON-RPC 응답만 stdout
