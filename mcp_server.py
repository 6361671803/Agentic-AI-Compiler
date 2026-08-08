"""MCP server exposing this compiler's verification tools and full pipeline over stdio.

Connect from Claude Desktop / Claude Code / any MCP client by pointing it at:
    python "c:\\ai compiler\\mcp_server.py"

Every tool here calls a real local checker (ast, ruff, mypy, a subprocess,
or the PyPI API) so an LLM client gets grounded facts about the code instead
of a guess. run_pipeline exposes the exact same 4-stage crew the Streamlit
UI uses (agents/crew.py) - an external MCP client gets the same analysis
quality as the browser app, not a separate, simpler path.
"""
import sys

from mcp.server.fastmcp import FastMCP

sys.path.append(".")
from compiler.parser import check_syntax
from compiler.sandbox import run_code_sandboxed, DEFAULT_TIMEOUT_SECONDS
from compiler.checks import lint_code, type_check, check_dependencies, check_missing_dependencies, security_scan
from agents.crew import run_crew
from agents.rag import index_knowledge

mcp = FastMCP("agentic-ai-compiler")

mcp.tool()(lint_code)
mcp.tool()(type_check)
mcp.tool()(check_dependencies)
mcp.tool()(check_missing_dependencies)
mcp.tool()(security_scan)


@mcp.tool()
def check_syntax_tool(code: str) -> str:
    """Check Python code for syntax errors using the ast module."""
    return check_syntax(code)


@mcp.tool()
def run_code(code: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Run Python code in an isolated subprocess with a timeout and capture stdout/stderr/exit code."""
    return run_code_sandboxed(code, timeout=timeout)


@mcp.tool()
def run_pipeline(code: str) -> dict:
    """Run the full 4-stage review pipeline on this code: Error Detection, Debug (verified,
    zero-error corrected code), Explain, and Security. Same pipeline the Streamlit app uses,
    grounded by real checkers plus a Python knowledge base and past fixes (RAG)."""
    return run_crew(code)


if __name__ == "__main__":
    index_knowledge()
    mcp.run(transport="stdio")
