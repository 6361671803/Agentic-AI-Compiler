"""Single-prompt AI helper used by the MCP server's ai_fix/ai_explain tools.

Shares the same LLM configuration as the multi-agent crew (Gemini by
default, Ollama if CREW_MODEL=ollama/<model>) instead of duplicating
provider-selection logic - see agents/crew.py for details and setup.
"""
from functools import lru_cache

from agents.crew import _build_llm

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = _build_llm()
    return _llm


@lru_cache(maxsize=64)
def _ask_ai_cached(prompt):
    return _get_llm().call(messages=[{"role": "user", "content": prompt}])


def ask_ai(prompt):
    """Send prompt to the configured LLM.

    Identical prompts are served from an in-memory cache instead of
    re-hitting the LLM, since callers can re-issue the same request.
    """
    try:
        return _ask_ai_cached(prompt)
    except Exception as error:
        return f"AI Error: {error}"
