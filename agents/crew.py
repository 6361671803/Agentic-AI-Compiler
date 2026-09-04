"""4-stage code review pipeline: Error Detection -> Debug -> Explain -> Security.

Every local Ollama model tried here (qwen2.5:3b, qwen2.5-coder:3b,
qwen2.5-coder:7b) turned out unreliable at native tool-calling: agents would
sometimes print the raw tool-call JSON as their final answer instead of
actually invoking the tool and using its result, and CPU-only local inference
made every run take minutes. So tool execution isn't left to the LLM at all -
the real checkers (ast/ruff/mypy/sandboxed execution/regex scan) run first in
plain Python, deterministically, and each agent explains those already-
computed results in plain language, only reasoning further where no tool can
help (logical bugs, edge cases, malicious-intent judgment).

Now runs against Gemini by default (crewai's native "gemini/<model>" provider)
for speed; set CREW_MODEL=ollama/<model-name> to go back to local Ollama.
Needs GEMINI_API_KEY (or GOOGLE_API_KEY) in the environment or a .env file -
see .env.example.

RAG context is injected into Stage 1 and Stage 2 (retrieve() in
agents/rag.py), sourced from a curated Python exceptions/style-guide
knowledge base and a running memory of code this app has fixed before -
never from this app's own source code. An earlier version grounded prompts
with snippets of this app's own source, and a small local model sometimes
parroted that irrelevant project code back as the "corrected code" for
whatever the user pasted in - a real, reproduced bug. Every retrieved chunk
is now genuinely about fixing Python code, and every prompt that includes
one also explicitly tells the model it's background reference material, not
something to output.
"""
import os
import re

os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Task, Crew, Process, LLM

from compiler.parser import check_syntax as _check_syntax
from compiler.sandbox import run_code_sandboxed as _run_code_sandboxed
from compiler.checks import (
    lint_code as _lint_code,
    type_check as _type_check,
    security_scan as _security_scan,
)
from agents.text_utils import extract_code_block as _extract_code_block
from agents.rag import retrieve as _retrieve, remember_fix as _remember_fix

# Three interchangeable backends, switched purely via CREW_MODEL's provider
# prefix - no code change needed to move between them:
#   gemini/<model>      (default) - needs GEMINI_API_KEY
#   openrouter/<model>             - needs OPENROUTER_API_KEY, e.g.
#                                    openrouter/openai/gpt-4o-mini
#   ollama/<model>                 - local, free, no key, needs `ollama serve`
# CrewAI's LLM class natively recognises the "gemini/" and "openrouter/"
# prefixes and reads the matching *_API_KEY env var itself; only "ollama/"
# needs the explicit base_url override below, since it's not a hosted API.
CREW_MODEL = os.getenv("CREW_MODEL", "gemini/gemini-2.0-flash")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Stage 2 (Debug) has to fit a full corrected file plus line-by-line diffs,
# so this needs real headroom - capped so a stuck agent can't run away
# generating tokens for minutes.
CREW_MAX_TOKENS = int(os.getenv("CREW_MAX_TOKENS", "2048"))
CREW_MAX_ITER = int(os.getenv("CREW_MAX_ITER", "6"))
# How many extra fix passes the Debug Agent's own output gets if the real
# checkers still find something wrong with the code it just produced.
DEBUG_VERIFY_RETRIES = int(os.getenv("DEBUG_VERIFY_RETRIES", "2"))


def _build_llm():
    if CREW_MODEL.startswith("ollama/"):
        return LLM(
            model=CREW_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.2,
            max_tokens=CREW_MAX_TOKENS,
        )
    return LLM(
        model=CREW_MODEL,
        temperature=0.2,
        max_tokens=CREW_MAX_TOKENS,
    )

PLAIN_LANGUAGE_RULE = (
    "Write for a complete beginner: short sentences, everyday words. If you must use a "
    "technical term, explain what it means right after in plain words."
)
NO_CONTRADICTION_RULE = (
    "IMPORTANT: If the tool output below lists any findings, you MUST include every single one in your "
    "answer - never summarize them away, drop them, or end with a line saying no issues were found. Only "
    "say nothing-was-found if the tool output itself is genuinely empty or says no issues."
)
ONLY_THIS_CODE_RULE = (
    "Only ever discuss and output the Code given below in this task. Never invent, reference, or output "
    "any other code, file, or project."
)
RAG_USAGE_RULE = (
    "Background reference material may be provided below, pulled from a Python knowledge base and past "
    "fixes - it is ONLY for you to learn from, never something to quote, copy, or output as your answer. "
    "If it's irrelevant to this specific code, ignore it entirely."
)


def _static_analysis_report(code):
    return (
        f"Syntax check:\n{_check_syntax(code)}\n\n"
        f"Ruff lint:\n{_lint_code(code)}\n\n"
        f"Mypy type check:\n{_type_check(code)}"
    )


def _runtime_report(code):
    result = _run_code_sandboxed(code)
    if result["timed_out"]:
        return f"Execution timed out after {result['elapsed_seconds']}s.\nPartial stdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
    return (
        f"Exit code: {result['exit_code']}\n"
        f"stdout:\n{result['stdout']}\n"
        f"stderr (a traceback here means the code raised an exception):\n{result['stderr']}"
    )


def _security_report(code):
    findings = _security_scan(code)
    if not findings:
        return "No issues found by the automated scanner."
    return "\n".join(f"Line {f['line']} [{f['severity']}]: {f['issue']}" for f in findings)


_CLEAN_CLAIM_PHRASES = (
    "no issue", "no security issue", "no risk", "nothing found",
    "no findings", "code is clean", "no vulnerab", "no danger",
)


def _verified_security_output(llm_text, security_report):
    """Fall back to the real scan results if the LLM claims "clean" when it isn't.

    Repeatedly reproduced during testing: this model sometimes writes "No
    security issues found" even when the deterministic scanner (ast/regex,
    not an LLM) found real high-severity issues on the same input. Rather
    than keep tuning prompt wording against a failure that's proven to
    recur, this checks the LLM's claim against the real result and only
    trusts it when it isn't contradicted by the ground truth.
    """
    real_has_findings = security_report != "No issues found by the automated scanner."
    if not real_has_findings:
        return llm_text

    llm_lower = llm_text.lower()
    llm_claims_clean = any(phrase in llm_lower for phrase in _CLEAN_CLAIM_PHRASES)
    flagged_lines = re.findall(r"Line (\d+)", security_report)
    llm_mentions_a_flagged_line = any(f"line {ln}" in llm_lower for ln in flagged_lines)

    if llm_claims_clean and not llm_mentions_a_flagged_line:
        bullets = "\n".join(f"- {entry}" for entry in security_report.split("\n"))
        return (
            "⚠️ The AI summary for this stage incorrectly reported no issues. Showing the "
            "verified scanner findings instead (these are computed directly, not by the AI):\n\n"
            f"{bullets}"
        )
    return llm_text


def _build_crew():
    llm = _build_llm()

    error_detector = Agent(
        role="Error Detection Agent",
        goal="Find every issue in the code across every category: syntax, indentation, runtime, logical, type, and edge-case.",
        backstory=(
            "A meticulous QA engineer trained to catch every category of Python bug - not just what a "
            "linter reports, but logical mistakes and edge cases too, by actually reading and reasoning "
            "about the code."
        ),
        tools=[],
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=CREW_MAX_ITER,
    )
    debugger = Agent(
        role="Debug Agent",
        goal="Fix every issue Error Detection found and produce the complete corrected file.",
        backstory="A precise senior engineer who only touches what's broken and never rewrites unrelated code.",
        tools=[],
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=CREW_MAX_ITER,
    )
    explainer = Agent(
        role="Explain Agent",
        goal="Teach a beginner what the corrected code does, why each error happened, and how the code could be improved further.",
        backstory="A patient instructor who connects each bug to the underlying concept so the reader avoids it next time.",
        tools=[],
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=CREW_MAX_ITER,
    )
    security = Agent(
        role="Security Agent",
        goal="Independently scan the code for anything malicious or dangerous, with a risk level for each finding.",
        backstory=(
            "An application security engineer specialized in spotting injection, unsafe deserialization, "
            "credential leaks, path traversal, obfuscated logic, and malware-like behavior such as "
            "persistence or self-replication."
        ),
        tools=[],
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=CREW_MAX_ITER,
    )

    task_errors = Task(
        description=(
            "Real tool output for this code is below (syntax check, ruff lint, mypy type check, and what "
            "actually happened when it was run in a sandbox). Using that evidence, plus your own careful "
            "reading of the code, list every issue found across ALL SIX of these categories:\n"
            "1. Syntax errors\n2. Indentation / formatting errors\n3. Runtime errors\n4. Logical errors "
            "(code runs but gives the wrong result)\n5. Type errors / signature mismatches\n"
            "6. Edge-case failures (empty input, None, zero, negative numbers, etc.)\n\n"
            "For EVERY category, either list each issue with its exact line number and a one-line "
            "description, or write 'None found' for that category. Never skip a category. "
            f"{PLAIN_LANGUAGE_RULE} {NO_CONTRADICTION_RULE} {ONLY_THIS_CODE_RULE} {RAG_USAGE_RULE}\n\n"
            "Static-analysis tool output:\n{static_report}\n\n"
            "Sandbox execution tool output:\n{runtime_report}\n\n"
            "Background reference material:\n{knowledge_context}\n\nCode:\n{code}"
        ),
        expected_output=(
            "1. Syntax errors: ...\n2. Indentation / formatting errors: ...\n3. Runtime errors: ...\n"
            "4. Logical errors: ...\n5. Type errors / signature mismatches: ...\n6. Edge-case failures: ...\n"
            "(every category present, 'None found' where nothing exists)"
        ),
        agent=error_detector,
    )
    task_debug = Task(
        description=(
            "The Error Detection Agent's findings for this code are provided above as context - use them. "
            "For EACH issue it found, show: the broken line(s) as they currently are, the corrected "
            "line(s), and one sentence on why the fix works. Do not touch any line that isn't broken. "
            "After that, as your FINAL section, output the complete corrected file - every line, from the "
            "first to the last, inside one python code block. Never abbreviate, truncate, or write '...' / "
            f"'rest unchanged' in place of real lines - paste the whole runnable file. {PLAIN_LANGUAGE_RULE} "
            f"{ONLY_THIS_CODE_RULE} {RAG_USAGE_RULE}\n\n"
            "Background reference material:\n{knowledge_context}\n\nOriginal code:\n{code}"
        ),
        expected_output=(
            "## Fixes\n(for each issue: broken line -> corrected line -> why, one at a time)\n\n"
            "## Corrected Code\n```python\n(the complete file, every line)\n```"
        ),
        agent=debugger,
        context=[task_errors],
    )
    task_explain = Task(
        description=(
            "The Error Detection Agent's findings and the Debug Agent's corrected code are provided above "
            "as context - use them. Do three things:\n"
            "1. Explain in plain language what the corrected code does overall.\n"
            "2. For each error that was found, explain in a bit more depth why it happened and what "
            "concept the reader should understand to avoid it in future code.\n"
            "3. Suggest 2-4 concrete advancements beyond just fixing bugs (e.g. better error handling, "
            "input validation, performance, readability, test coverage). These are SUGGESTIONS ONLY - do "
            f"not write code for them. {PLAIN_LANGUAGE_RULE} {ONLY_THIS_CODE_RULE}\n\nOriginal code:\n{{code}}"
        ),
        expected_output=(
            "## What The Code Does\n...\n\n## Errors Explained\n(each error, why it happened, the concept "
            "behind it)\n\n## Suggested Advancements\n(2-4 bullet-point suggestions, not applied)"
        ),
        agent=explainer,
        context=[task_errors, task_debug],
    )
    task_security = Task(
        description=(
            "Independently of the other reports, scan this code for anything potentially dangerous or "
            "malicious. Real automated-scanner output is below - use it as a starting point, then also "
            "look for anything the scanner can't catch: code execution from untrusted input, file-system "
            "access outside expected scope, network calls to hardcoded/suspicious URLs or data "
            "exfiltration, hardcoded credentials or tokens, injection risks (SQL/command/path traversal), "
            "obfuscated or intentionally hard-to-read logic, privilege escalation, and malware-like "
            "behavior (self-replication, persistence, disabling security tools). For each finding, give a "
            "risk level (Low/Medium/High/Critical), the line number, and why it's risky. If the code is "
            f"clean, say so explicitly - never invent a risk that isn't there. {PLAIN_LANGUAGE_RULE} "
            f"{NO_CONTRADICTION_RULE} {ONLY_THIS_CODE_RULE}\n\n"
            "Automated security-scan tool output:\n{security_report}\n\nCode:\n{code}"
        ),
        expected_output="A list of findings (risk level, line, why it's risky) or 'No security issues found.'",
        agent=security,
    )

    crew = Crew(
        agents=[error_detector, debugger, explainer, security],
        tasks=[task_errors, task_debug, task_explain, task_security],
        process=Process.sequential,
        verbose=False,
    )
    return crew, (task_errors, task_debug, task_explain, task_security), llm


def _validate_python(code):
    """Run the real checkers against a code string. Returns (is_clean, report)."""
    syntax = _check_syntax(code)
    lint = _lint_code(code)
    mypy = _type_check(code)
    is_clean = (
        "No syntax" in syntax
        and lint.strip() == "All checks passed!"
        and mypy.strip().startswith("Success")
    )
    report = f"Syntax check:\n{syntax}\n\nRuff lint:\n{lint}\n\nMypy type check:\n{mypy}"
    return is_clean, report


def _verify_and_fix_debug_output(debug_text, llm):
    """Make "full corrected code, zero errors" a checked guarantee, not just a prompt instruction.

    Extracts the code block the Debug Agent produced, runs it through the same
    real checkers used everywhere else in this pipeline, and if anything is
    still wrong, sends just that code + the specific remaining errors back for
    another fix pass (up to DEBUG_VERIFY_RETRIES times). Returns the debug
    text with its code block swapped for the final, checked version, plus a
    status line stating whether it's actually clean.
    """
    code = _extract_code_block(debug_text)
    if code is None:
        return debug_text, "⚠️ Could not find a code block in the Debug Agent's output to verify."

    is_clean, report = _validate_python(code)
    attempts = 0
    while not is_clean and attempts < DEBUG_VERIFY_RETRIES:
        attempts += 1
        retry_prompt = (
            "This Python code still has real issues found by automated checkers. Fix ONLY what's "
            "listed below and return the complete corrected file in one python code block - no "
            "explanation, just the code.\n\n"
            f"Checker output:\n{report}\n\nCode:\n{code}"
        )
        response = llm.call(messages=[{"role": "user", "content": retry_prompt}])
        retried_code = _extract_code_block(response) or response
        code = retried_code
        is_clean, report = _validate_python(code)

    fixed_debug_text = debug_text
    original_block = _extract_code_block(debug_text)
    if original_block is not None and original_block != code:
        fixed_debug_text = debug_text.replace(original_block, code, 1)

    if is_clean:
        status = f"✅ Verified: the corrected code passes syntax, lint, and type checks (0 errors, {attempts} extra fix pass(es) needed)."
    else:
        status = (
            f"⚠️ After {attempts} automatic fix attempt(s), the checkers still report issues:\n\n{report}"
        )
    return fixed_debug_text, status


_crew = None
_tasks = None
_llm = None


def run_crew(code, on_step=None):
    """Run the 4-stage pipeline against `code`: Error Detection -> Debug -> Explain -> Security.

    on_step(role, output_text), if given, fires right after each stage finishes
    so a caller (e.g. the Streamlit UI) can show live progress.
    """
    global _crew, _tasks, _llm
    if _crew is None:
        _crew, _tasks, _llm = _build_crew()

    if on_step:
        _crew.task_callback = lambda task_output: on_step(str(task_output.agent), task_output.raw)
    else:
        _crew.task_callback = None

    static_report = _static_analysis_report(code)
    runtime_report = _runtime_report(code)
    security_report = _security_report(code)
    knowledge_context, knowledge_sources = _retrieve(code)

    _crew.kickoff(inputs={
        "code": code,
        "static_report": static_report,
        "runtime_report": runtime_report,
        "security_report": security_report,
        "knowledge_context": knowledge_context or "(none relevant)",
    })

    task_errors, task_debug, task_explain, task_security = _tasks
    security_llm_output = task_security.output.raw if task_security.output else ""

    debug_raw = task_debug.output.raw if task_debug.output else ""
    debug_verified, debug_status = _verify_and_fix_debug_output(debug_raw, _llm) if debug_raw else ("", "")
    if on_step and debug_status:
        on_step("Debug Agent (verification)", debug_status)

    fixed_code = _extract_code_block(debug_verified)
    if fixed_code:
        # Builds up a growing memory of code this app has fixed before, so
        # future similar submissions can be grounded in real past fixes -
        # not this app's own source, which is what caused problems earlier.
        _remember_fix(code, fixed_code, summary=task_errors.output.raw[:300] if task_errors.output else "")

    return {
        "errors": task_errors.output.raw if task_errors.output else "",
        "debug": f"{debug_verified}\n\n---\n{debug_status}" if debug_status else debug_verified,
        "explain": task_explain.output.raw if task_explain.output else "",
        # Named "security", not "error" - the caller uses a dict with an
        # "error" key to signal the whole crew run raised an exception, and
        # no key here may collide with that one.
        "security": _verified_security_output(security_llm_output, security_report),
        # Raw ground truth, computed in plain Python (not an LLM), passed
        # through as a safety net: local models have, on occasion,
        # confidently claimed a non-empty tool report was empty. The UI shows
        # this alongside each agent's prose so the user always sees what the
        # checker actually found.
        "raw_static_report": static_report,
        "raw_runtime_report": runtime_report,
        "raw_security_report": security_report,
        "knowledge_sources": knowledge_sources,
    }
