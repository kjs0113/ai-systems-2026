# Lab 03: FastMCP GPU Monitor Server

**학번**: 202321010  
**이름**: 박진우  

---

## 1. 실습 환경

- **OS**: Windows 10
- **GPU**: NVIDIA GeForce RTX 3060 (MIG 미지원)
- **Python**: 3.11.8, Conda (mcp-lab)
- **테스트**: `npx @modelcontextprotocol/inspector python mcp_gpu_server.py`

---

## 2. 문제 상황

### 2.1 MCP Inspector 연결 실패

서버를 작성하고 MCP Inspector로 테스트하려고 했는데 연결이 계속 실패했습니다. 브라우저 콘솔에 `SyntaxError: Unexpected token 'F'` 에러가 표시되고 Tools 목록이 안 나왔습니다. 

원인을 찾아보니 FastMCP가 시작할 때 ASCII 배너를 stdout으로 출력하고 있었습니다. MCP 프로토콜은 stdin/stdout으로 JSON-RPC 메시지를 주고받는데, stdout에 JSON이 아닌 텍스트가 섞여서 파싱이 깨진 것이었습니다.

### 2.2 MIG 기능 테스트 불가

과제에서 `get_mig_devices` Tool 구현이 요구되었는데, RTX 3060은 소비자용 GPU라 MIG를 지원하지 않았습니다. `nvidia-smi` 실행 시 MIG 항목이 `N/A`로 표시되고, 실제 MIG 명령어를 실행할 수 없어서 실제 하드웨어로 테스트가 불가능했습니다.

### 2.3 응답 형식 불일치

처음 구현할 때 Tool마다 성공/실패 응답을 다르게 만들었습니다. 어떤 Tool은 `{"status": "success", "gpu_count": 2}` 형식으로, 어떤 Tool은 `{"error": "ValidationError"}` 형식으로 보내니 클라이언트 코드에서 매번 다르게 처리해야 했습니다.

---

## 3. 해결 방법

### 3.1 stdout 보호 

서버 코드 최상단에 `os.environ['FASTMCP_QUIET'] = '1'`을 추가해서 FastMCP 배너를 비활성화했습니다. 그리고 `logging.StreamHandler(sys.stderr)`로 모든 로그를 stderr로만 보내서 stdout을 깨끗하게 유지했습니다. 이후 MCP Inspector가 정상적으로 연결되었습니다.

### 3.2 ErrorCode 클래스 정의

`INVALID_GPU_INDEX`, `ACCESS_DENIED` 같은 표준 에러 코드를 `ErrorCode` 클래스에 상수로 정의했습니다. 클라이언트가 문자열이 아닌 고정된 코드로 에러를 구분할 수 있게 했습니다.

### 3.3 MIG 미지원 환경 처리

`get_mig_devices()`에서 `nvmlDeviceGetMigMode()` 호출을 try-except로 감싸서 예외가 발생하면 에러 대신 `{"mig_enabled": false, "message": "MIG not supported"}`를 반환하도록 했습니다. 덕분에 RTX 3060에서도 서버가 정상 작동합니다.

---

## 4. 구현 설명

### 주요 구조

- **Tools**: `list_gpus`, `get_gpu_info`, `get_mig_devices`
- **Resource**: `gpu://system/info`
- **보안**: TBAC (3-tier) + 입력 검증 (3-layer)
- **응답**: `{"ok": true/false, "data"/"error": {...}}`

### 테스트 예시

**권한 거부**:
```json
{"user_id": "student", "gpu_index": 0}  // get_mig_devices
→ {"ok": false, "error": {"code": "ACCESS_DENIED", ...}}
```

**입력 검증 실패**:
```json
{"user_id": "student", "gpu_index": -1}
→ {"ok": false, "error": {"code": "INVALID_GPU_INDEX", ...}}
```

**MIG 미지원 처리**:
```json
{"user_id": "researcher", "gpu_index": 0}
→ {"ok": true, "data": {"mig_enabled": false, "message": "MIG not supported"}}
```

---

## 실행 방법

```bash
npx @modelcontextprotocol/inspector python mcp_gpu_server.py
```
