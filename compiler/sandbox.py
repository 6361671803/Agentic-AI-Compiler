"""Subprocess-based code execution, isolated from this process and time-bounded.

Used by the MCP server, the CrewAI pipeline's own verification step, and the
Streamlit UI's "Run Code" button, so arbitrary submitted code - including
things like exit()/sys.exit(), infinite loops, or a stray null byte - can't
hang or crash the host process.
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
    except (ValueError, OSError) as e:
        # e.g. a null byte in the submitted code makes subprocess.run() itself
        # raise (ValueError: embedded null character) before any process
        # starts - report it like any other failed run instead of letting it
        # escape uncaught into the caller (Streamlit UI / MCP server).
        return {
            "stdout": "",
            "stderr": f"Could not start execution: {e}",
            "exit_code": None,
            "timed_out": False,
            "elapsed_seconds": round(time.monotonic() - start, 3),
        }
