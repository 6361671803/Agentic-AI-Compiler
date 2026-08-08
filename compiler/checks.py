"""Deterministic, tool-grounded checks shared by the MCP server and the CrewAI agents.

Kept dependency-free of both `mcp` and `crewai` so either layer can wrap
these plain functions without circular imports.
"""
import ast
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

RISKY_CALLS = {
    "eval": "Arbitrary code execution via eval().",
    "exec": "Arbitrary code execution via exec().",
    "os.system": "Shell command execution; vulnerable to injection.",
    "os.popen": "Shell command execution; vulnerable to injection.",
    "pickle.loads": "Deserializing untrusted data can execute arbitrary code.",
    "pickle.load": "Deserializing untrusted data can execute arbitrary code.",
    "yaml.load": "Unsafe YAML loading; use yaml.safe_load instead.",
    "__import__": "Dynamic import can load arbitrary modules at runtime.",
}
SECRET_PATTERN = re.compile(
    r"(?i)(password|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]{4,}['\"]"
)


def _run_tool(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).strip() or "No issues found."
    except FileNotFoundError:
        return f"AI Error: '{args[0]}' is not installed in this environment."
    except subprocess.TimeoutExpired:
        return f"AI Error: '{args[0]}' timed out."


def lint_code(code: str) -> str:
    """Lint Python code with ruff for style issues, dead code, and common bugs."""
    return _run_tool([sys.executable, "-m", "ruff", "check", "--stdin-filename", "snippet.py", "-"])


def type_check(code: str) -> str:
    """Type-check Python code with mypy."""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        return _run_tool([sys.executable, "-m", "mypy", "--ignore-missing-imports", path])
    finally:
        os.unlink(path)


def _pypi_lookup(name):
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.load(resp)
        version = data["info"]["version"]
        return {"found": True, "install": f"pip install {name}=={version}"}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"found": False, "install": None, "note": "not a top-level PyPI package name"}
        return {"found": False, "install": None, "note": f"PyPI lookup failed: {e}"}
    except Exception as e:
        return {"found": False, "install": None, "note": f"lookup error: {e}"}


def check_dependencies(imports: list[str]) -> dict:
    """Look up each import name on PyPI and return the pip install command if it exists there."""
    return {name: _pypi_lookup(name) for name in imports}


def extract_imports(code: str) -> list[str]:
    """Top-level module names this code imports, via ast (no execution)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return sorted(names)


def check_missing_dependencies(code: str) -> dict:
    """Find imports this code needs that aren't installed locally, with a pip command for each."""
    import importlib.util

    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    missing = {}
    for name in extract_imports(code):
        if name in stdlib:
            continue
        if importlib.util.find_spec(name) is not None:
            continue
        missing[name] = _pypi_lookup(name)
    return missing


def _call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts = []
        cur = node.func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


def security_scan(code: str) -> list[dict]:
    """Flag risky calls and hardcoded-looking secrets via ast + regex. Deterministic, no LLM guessing."""
    findings = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [{"line": e.lineno, "issue": f"Cannot scan: syntax error: {e}", "severity": "error"}]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in RISKY_CALLS:
                findings.append({"line": node.lineno, "issue": RISKY_CALLS[name], "severity": "high"})
            elif name in ("subprocess.run", "subprocess.Popen", "subprocess.call"):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append({
                            "line": node.lineno,
                            "issue": "subprocess call with shell=True is vulnerable to command injection.",
                            "severity": "high",
                        })

    for i, line in enumerate(code.splitlines(), start=1):
        if SECRET_PATTERN.search(line):
            findings.append({"line": i, "issue": "Possible hardcoded secret/credential.", "severity": "medium"})

    return findings
