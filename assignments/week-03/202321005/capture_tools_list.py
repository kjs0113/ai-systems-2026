"""
tools/list JSON-RPC 응답을 캡처하는 스크립트.

FastMCP 서버의 tools/list, prompts/list, resources/list 응답을
JSON-RPC 형식으로 JSON 파일에 저장한다.
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


async def capture_primitives():
    """MCP 서버의 3대 프리미티브를 캡처."""
    from mcp_server import mcp

    # Tools 캡처 (to_mcp_tool()로 표준 MCP 스키마 변환)
    tools_raw = await mcp._list_tools()
    tools = [t.to_mcp_tool().model_dump(exclude_none=True) for t in tools_raw]

    tools_list_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": tools},
    }

    # Prompts 캡처
    prompts_raw = await mcp._list_prompts()
    prompts = [
        {"name": p.name, "description": p.description}
        for p in prompts_raw
    ]

    prompts_list_response = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"prompts": prompts},
    }

    # Resource Templates 캡처
    templates_raw = await mcp._list_resource_templates()
    templates = [
        {
            "uriTemplate": str(t.uri_template),
            "name": t.name,
            "description": t.description,
        }
        for t in templates_raw
    ]

    resources_list_response = {
        "jsonrpc": "2.0",
        "id": 3,
        "result": {"resourceTemplates": templates},
    }

    # 파일로 저장
    captures_dir = os.path.join(os.path.dirname(__file__), "captures")
    os.makedirs(captures_dir, exist_ok=True)

    for filename, data in [
        ("tools_list.json", tools_list_response),
        ("prompts_list.json", prompts_list_response),
        ("resources_list.json", resources_list_response),
    ]:
        with open(os.path.join(captures_dir, filename), "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # stdout 출력
    for label, resp in [
        ("tools/list", tools_list_response),
        ("prompts/list", prompts_list_response),
        ("resources/list", resources_list_response),
    ]:
        print("=" * 60)
        print(f"{label} JSON-RPC Response")
        print("=" * 60)
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        print()

    print(f"Captured: {len(tools)} tools, {len(prompts)} prompts, {len(templates)} resource templates")
    print(f"Files saved to: {captures_dir}/")


if __name__ == "__main__":
    asyncio.run(capture_primitives())
