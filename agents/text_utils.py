"""Small text helpers shared by the UI when rendering LLM responses."""
import re

_CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code_block(text):
    """Pull the first fenced code block out of a markdown response, if any.

    Used to show corrected code in its own st.code() box (which gets a
    hover copy icon), instead of making the user select-and-copy out of
    a wall of markdown.
    """
    if not isinstance(text, str):
        return None
    match = _CODE_FENCE_RE.search(text)
    return match.group(1).rstrip() if match else None
