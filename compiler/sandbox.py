"""Subprocess-based code execution, isolated from this process and time-bounded.

Used by the MCP server (compiler/executor.py's exec() stays as-is for the
Streamlit UI's own "Run Code" button, since that behavior wasn't part of
this change) so external MCP clients can't hang or crash the host process
by submitting arbitrary code.
"""
import subprocess
import sys
import time

DEFAULT_TIMEOUT_SECONDS = 10


def run_code_sandboxed(code, timeout=DEFAULT_TIMEOUT_SECONDS):
    start = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "timed_out": False,
            "elapsed_seconds": round(elapsed, 3),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + f"\nExecution timed out after {timeout}s",
            "exit_code": None,
            "timed_out": True,
            "elapsed_seconds": timeout,
        }
