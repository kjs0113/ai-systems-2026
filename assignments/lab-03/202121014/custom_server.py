from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, Dict


ALLOWED_BASE = Path(__file__).resolve().parent


def _validate_path(path: str) -> Path:
    target = (ALLOWED_BASE / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if ALLOWED_BASE not in target.parents and target != ALLOWED_BASE:
        raise ValueError("Path traversal is not allowed.")
    return target


def _safe_text(text: str) -> str:
    return text.strip() if text.strip() else "(no output)"


def _run_pytest_impl(path: str = ".") -> str:
    try:
        target = _validate_path(path)
        completed = subprocess.run(
            ["pytest", str(target), "-v"],
            cwd=ALLOWED_BASE,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        return (
            f"returncode={completed.returncode}\n"
            f"stdout:\n{_safe_text(completed.stdout)}\n\n"
            f"stderr:\n{_safe_text(completed.stderr)}"
        )
    except Exception as exc:
        return f"ERROR: {exc}"


def _count_lines_impl(file_path: str) -> str:
    try:
        target = _validate_path(file_path)
        if not target.is_file():
            return "ERROR: file not found"
        line_count = len(target.read_text(encoding="utf-8").splitlines())
        return f"{target.name}: {line_count} lines"
    except Exception as exc:
        return f"ERROR: {exc}"


def get_project_stats() -> str:
    py_files = list(ALLOWED_BASE.rglob("*.py"))
    total_lines = 0
    for py_file in py_files:
        try:
            total_lines += len(py_file.read_text(encoding="utf-8").splitlines())
        except Exception:
            continue
    return (
        f"project_path: {ALLOWED_BASE}\n"
        f"python_file_count: {len(py_files)}\n"
        f"total_python_lines: {total_lines}"
    )


def _build_code_review_prompt(file_path: str) -> str:
    return (
        "코드 리뷰 템플릿\n"
        f"대상 파일: {file_path}\n"
        "1. 보안 취약점\n"
        "2. 예외 처리\n"
        "3. 코드 품질\n"
        "4. 테스트 가능성"
    )


try:
    from mcp.server.fastmcp import FastMCP  # type: ignore

    MCP_AVAILABLE = True
except Exception:
    MCP_AVAILABLE = False

    class FastMCP:
        def __init__(self, name: str):
            self.name = name
            self.tools: Dict[str, Callable] = {}
            self.resources: Dict[str, Callable] = {}
            self.prompts: Dict[str, Callable] = {}

        def tool(self) -> Callable:
            def decorator(func: Callable) -> Callable:
                self.tools[func.__name__] = func
                return func

            return decorator

        def resource(self, name: str) -> Callable:
            def decorator(func: Callable) -> Callable:
                self.resources[name] = func
                return func

            return decorator

        def prompt(self) -> Callable:
            def decorator(func: Callable) -> Callable:
                self.prompts[func.__name__] = func
                return func

            return decorator

        def run(self) -> None:
            print("FastMCP package is not installed.")
            print(f"Server name: {self.name}")
            print("tools/list:", ", ".join(sorted(self.tools)))
            print("resources/list:", ", ".join(sorted(self.resources)))
            print("prompts/list:", ", ".join(sorted(self.prompts)))
            print("Install the MCP package to serve over Inspector.")


mcp = FastMCP("lab03-custom")


@mcp.tool()
def run_pytest(path: str = ".") -> str:
    return _run_pytest_impl(path)


@mcp.tool()
def count_lines(file_path: str) -> str:
    return _count_lines_impl(file_path)


@mcp.resource("project://stats")
def resource_project_stats() -> str:
    return get_project_stats()


@mcp.prompt()
def code_review(file_path: str) -> str:
    return _build_code_review_prompt(file_path)


if __name__ == "__main__":
    mcp.run()
