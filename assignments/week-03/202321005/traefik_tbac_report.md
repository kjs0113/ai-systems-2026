# Traefik Hub MCP Gateway 리서치 — TBAC 변수 치환 정책 설계 보고서

## 1. 개요

Traefik Hub는 MCP 클라이언트(AI 에이전트)와 MCP 서버(도구 제공자) 사이에 위치하는
**인프라 수준의 MCP Gateway**이다. 조직이 개별 MCP 서버를 직접 노출하지 않고,
중앙 집중식 인그레스 포인트에서 인증, 정책, 감사를 처리할 수 있게 한다.

## 2. Traefik Hub MCP Gateway 아키텍처

```
┌──────────────────┐     ┌─────────────────────────────┐     ┌────────────────┐
│  AI Agent        │     │  Traefik Hub MCP Gateway     ���     │  MCP Servers   │
│  (Claude Code,   │────▶│                              │────▶│                │
│   Cursor, etc.)  │     │  · JWT 검증 (OIDC)           │     │  · GPU Monitor │
│                  │◀────│  · TBAC 정책 적용             │◀────│  · File System │
│                  │     │  · tools/list 집계            │     │  · Git Server  │
│  SSE / HTTP      │     │  · Rate Limiting             │     │  · DB Query    │
└──────────────────┘     │  · 감사 로그                  │     └────────────────┘
                         └─────────────────────────────┘
```

### 핵심 기능

| 기능 | 설명 |
|------|------|
| **프로토콜 프록시** | SSE / Streamable HTTP 지원, 백엔드 MCP 서버로 투명하게 라우팅 |
| **디스커버리 집계** | 여러 MCP 서버의 `tools/list` 응답을 단일 카탈로그로 통합 |
| **OIDC 통합** | Keycloak, Auth0, Okta 등과 연동하여 JWT 토큰 검증 |
| **TBAC 정책** | 도구 수준 + 인자 수준의 세밀한 접근 제어 |
| **감사 로그** | 모든 도구 호출을 ID/도구명/인자/결과와 함께 기록 |
| **도구별 Rate Limiting** | HTTP 엔드포인트가 아닌 도구 단위로 요청 제한 |

## 3. TBAC 변수 네임스페이스

Traefik Hub는 TBAC 정책 규칙에서 **두 개의 변수 네임스페이스**를 제공한다.

### 3.1 `mcp.*` 네임스페이스 — MCP 프로토콜 메타데이터

| 변수 | 설명 | 예시 값 |
|------|------|---------|
| `mcp.tool.name` | 호출되는 도구 이름 | `"get_mig_status"` |
| `mcp.tool.server` | 도구가 속한 백엔드 MCP 서버 | `"gpu-monitor"` |
| `mcp.tool.args.<key>` | 도구 호출의 개별 인자 값 | `mcp.tool.args.gpu_index` → `0` |
| `mcp.method` | MCP JSON-RPC 메서드 | `"tools/call"`, `"tools/list"` |

### 3.2 `jwt.*` 네임스페이스 — JWT 토큰 클레임

| 변수 | 설명 | 예시 값 |
|------|------|---------|
| `jwt.sub` | Subject 클레임 | `"student-202321005"` |
| `jwt.iss` | Issuer 클레임 | `"https://auth.university.ac.kr"` |
| `jwt.claims.<name>` | 커스텀 클레임 | `jwt.claims.role` → `"student"` |
| `jwt.groups` | 그룹 멤버십 | `["ai-class", "lab-03"]` |

이 두 네임스페이스를 조합하면 **"누가(identity) + 무엇을(tool/args)"** 기반의 동적 정책이 가능하다.

## 4. 동적 정책 설계 — GPU 모니터링 MCP 서버 적용

본 과제의 MIG GPU Monitor MCP 서버에 Traefik Hub TBAC 정책을 적용하는 설계.

### 4.1 정책 A: 역할별 도구 접근 제어

학생(student)은 모니터링 도구만, 관리자(admin)만 관리 도구를 사용할 수 있다.

```yaml
apiVersion: hub.traefik.io/v1alpha1
kind: MCPPolicy
metadata:
  name: student-monitoring-only
  namespace: ai-class
spec:
  jwt:
    claims:
      - name: role
        value: student
  mcpServers:
    - name: mig-gpu-monitor
  rules:
    # 기본: 모든 도구 거부
    - action: deny
      tools: ["*"]
    # 모니터링/분석 도구만 허용
    - action: allow
      tools:
        - get_mig_status
        - get_gpu_metrics
        - set_session_role
      methods:
        - tools/call
        - tools/list
        - resources/read
        - prompts/list
        - prompts/get
```

```yaml
apiVersion: hub.traefik.io/v1alpha1
kind: MCPPolicy
metadata:
  name: admin-full-access
  namespace: ai-class
spec:
  jwt:
    claims:
      - name: role
        value: admin
  mcpServers:
    - name: mig-gpu-monitor
  rules:
    - action: allow
      tools: ["*"]          # 모든 도구 허용 (admin_reset_gpu 포함)
```

### 4.2 정책 B: 인자 수준 제약 — GPU 인덱스 격리

각 학생이 자신에게 할당된 MIG 슬라이스(GPU 인덱스)만 조회할 수 있도록 제한.
JWT의 커스텀 클레임 `assigned_gpu`와 도구 인자 `gpu_index`를 비교한다.

```yaml
apiVersion: hub.traefik.io/v1alpha1
kind: MCPPolicy
metadata:
  name: gpu-index-isolation
  namespace: ai-class
spec:
  jwt:
    claims:
      - name: role
        value: student
  rules:
    - action: allow
      tools:
        - get_mig_status
        - get_gpu_metrics
      constraints:
        # 도구 인자의 gpu_index가 JWT의 assigned_gpu와 일치해야 함
        - field: mcp.tool.args.gpu_index
          operator: eq
          value: "{{ jwt.claims.assigned_gpu }}"
```

**JWT 토큰 예시:**
```json
{
  "sub": "student-202321005",
  "iss": "https://auth.university.ac.kr",
  "role": "student",
  "assigned_gpu": 3,
  "groups": ["ai-class-2026"]
}
```

이 정책 하에서:
- `get_mig_status(gpu_index=3)` → 허용 (자신의 슬라이스)
- `get_mig_status(gpu_index=5)` → 거부 (다른 학생의 슬라이스)

### 4.3 정책 C: threshold_pct 범위 강제

Gateway 레벨에서 `threshold_pct` 인자의 범위를 강제한다 (서버 측 검증의 이중화).

```yaml
apiVersion: hub.traefik.io/v1alpha1
kind: MCPPolicy
metadata:
  name: threshold-range-enforcement
  namespace: ai-class
spec:
  rules:
    - action: allow
      tools:
        - get_gpu_metrics
      constraints:
        - field: mcp.tool.args.threshold_pct
          operator: gte
          value: "0"
        - field: mcp.tool.args.threshold_pct
          operator: lte
          value: "100"
```

### 4.4 정책 D: MCP 서버 스코프 + 그룹 기반 접근

프로덕션 GPU 서버에는 SRE 팀만 접근 가능.

```yaml
apiVersion: hub.traefik.io/v1alpha1
kind: MCPPolicy
metadata:
  name: production-gpu-lockdown
  namespace: production
spec:
  jwt:
    claims:
      - name: groups
        valueIn:
          - sre-team
          - platform-engineering
  mcpServers:
    - name: production-gpu-monitor
    - name: production-gpu-admin
  rules:
    - action: allow
      tools: ["*"]
```

## 5. TBAC 흐름 시퀀스

```
Student Agent                Traefik Hub Gateway              MCP Server
    │                              │                              │
    │  tools/call                  │                              │
    │  + JWT (role=student,        │                              │
    │    assigned_gpu=3)           │                              │
    │─────────────────────────────▶│                              │
    │                              │                              │
    │                    ┌─────────┴──────────┐                   │
    │                    │ 1. JWT 검증 (OIDC) │                   │
    │                    │ 2. jwt.* 추출      │                   │
    │                    │    role=student     │                   │
    │                    │    assigned_gpu=3   │                   │
    │                    ��� 3. mcp.* 추출      │                   │
    │                    │    tool=get_mig_... │                   │
    │                    │    args.gpu_index=3 │                   │
    │                    │ 4. 정책 매칭        │                   │
    │                    │    gpu_index(3) ==  │                   │
    │                    │    assigned_gpu(3)  │                   │
    │                    │    → ALLOW          │                   │
    │                    │ 5. Rate Limit 확인  │                   │
    │                    │ 6. 감사 로그 기록   │                   │
    │                    └─────────┬──────────┘                   │
    │                              │  프록시 전달                  │
    │                              │─────────────────────────────▶│
    │                              │                    실행 결과  │
    │                              │◀─────────────────────────────│
    │  JSON-RPC 응답               │                              │
    │◀─────────────────────────────│                              │
```

## 6. 본 과제 MCP 서버와의 비교

| 구현 계층 | 본 과제 (`mcp_server.py`) | Traefik Hub Gateway |
|-----------|--------------------------|---------------------|
| 정책 위치 | 서버 코드 내부 | 외부 Gateway (Kubernetes CRD) |
| 인증 | 수동 `set_session_role()` | JWT + OIDC 자동 검증 |
| 역할 관리 | Python Enum | JWT 클레임 기반 |
| 인자 제약 | 코드 내 `validate_*()` | 선언적 YAML constraints |
| 변경 시 | 코드 수정 + 재배포 | YAML 적용 (무중단) |
| 감사 | stderr 로깅 | 구조화된 감사 로그 + 대시보드 |
| 멀티 서버 | 단일 서버 | 다수 MCP 서버 통합 관리 |

**결론**: 본 과제의 서버 내장 TBAC은 프로토타입/학습용으로 적합하고,
프로덕션 환경에서는 Traefik Hub 같은 외부 Gateway에서 선언적 정책을 관리하는 것이
운영 효율성과 보안 측면에서 우월하��.

## 7. 핵심 요약

1. **`mcp.*` 네임스페이스**: 도구 이름, 서버, 인자를 정책 변수로 노출
2. **`jwt.*` 네임스페이스**: JWT 클레임(역할, 그룹, 커스텀)을 정책 변수로 노출
3. **변수 치환**: `{{ jwt.claims.assigned_gpu }}`처럼 런타임 값을 정책에 주입
4. **다계층 정책**: 서버 스코프 → 도구 허용/거부 → 인자 제약 순으로 평가
5. **선언적 관리**: Kubernetes CRD로 정책 정의, 코드 변경 없이 무중단 적용
