import sys
import os
import ast
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from streamlit_ace import st_ace
from compiler.executor import execute_code
from agents.rag import index_knowledge, index_upload
from agents.crew import run_crew
from agents.text_utils import extract_code_block
import time

LARGE_CODE_THRESHOLD = 100

# Index the curated Python reference docs (knowledge/) once per process;
# index_knowledge() no-ops on repeat calls internally.
index_knowledge()


# ============================================================================
# PAGE CONFIG & THEME
# ============================================================================

st.set_page_config(
    page_title="Agentic AI Compiler",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# SESSION STATE - results persist across Streamlit reruns
# ============================================================================

DEFAULTS = {
    "run_result": None,
    "crew_result": None,
    "crew_steps": [],
    "last_uploaded_doc": None,
}
for _key, _val in DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val


# ============================================================================
# CUSTOM CSS & STYLING - PREMIUM DEVELOPER STUDIO DESIGN
# ============================================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    :root {
        --primary: #10b981;
        --primary-dark: #059669;
        --primary-light: #6ee7b7;
        --accent: #3b82f6;
        --accent-dark: #1e40af;
        --success: #10b981;
        --error: #ef4444;
        --warning: #f59e0b;
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-tertiary: #94a3b8;
        --border-color: #475569;
        --border-subtle: rgba(226, 232, 240, 0.1);
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: 'Outfit', sans-serif;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }

    /* MAIN BACKGROUND WITH SUBTLE GRADIENT */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1a2749 50%, #0f172a 100%);
        position: relative;
    }

    /* SIDEBAR STYLING - REFINED */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid var(--border-subtle);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: var(--text-primary);
    }

    /* HEADER STYLING - ELEGANT & REFINED */
    .header-main {
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        z-index: 2;
        animation: fadeInDown 0.8s ease-out;
    }

    .header-title {
        font-family: 'Outfit', sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .header-subtitle {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        color: var(--text-secondary);
        font-weight: 500;
        letter-spacing: 0.5px;
    }

    /* DIVIDER - SUBTLE & REFINED */
    .divider-gradient {
        height: 1px;
        background: linear-gradient(90deg,
            transparent,
            var(--border-color) 10%,
            var(--primary) 50%,
            var(--border-color) 90%,
            transparent);
        margin: 2.5rem 0;
        border-radius: 1px;
    }

    /* EDITOR CONTAINER - CLEAN CARD DESIGN */
    .editor-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.5));
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.5rem;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .editor-container:hover {
        border-color: rgba(16, 185, 129, 0.2);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.6));
    }

    .editor-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: -0.3px;
    }

    .editor-title::before {
        content: '';
        width: 3px;
        height: 20px;
        background: var(--primary);
        border-radius: 1.5px;
    }

    /* STAT CHIPS ROW */
    .chip-row {
        display: flex;
        gap: 0.6rem;
        margin: 0.75rem 0 1.25rem 0;
        flex-wrap: wrap;
    }
    .chip {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
    .chip strong {
        color: var(--primary);
    }
    .chip.warn {
        background: rgba(245, 158, 11, 0.1);
        border-color: rgba(245, 158, 11, 0.35);
    }
    .chip.warn strong {
        color: var(--warning);
    }

    /* AGENT RESULT CARD */
    .agent-card {
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin: 0.75rem 0;
        border-left: 4px solid var(--primary);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.6));
    }
    .agent-card-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .agent-card.errors { border-left-color: #10b981; }
    .agent-card.errors .agent-card-title { color: #10b981; }
    .agent-card.debug { border-left-color: #3b82f6; }
    .agent-card.debug .agent-card-title { color: #3b82f6; }
    .agent-card.explain { border-left-color: #f59e0b; }
    .agent-card.explain .agent-card-title { color: #f59e0b; }
    .agent-card.security { border-left-color: #ef4444; }
    .agent-card.security .agent-card-title { color: #ef4444; }

    /* TEXT AREA / ACE EDITOR WRAPPER */
    .ace_editor {
        border-radius: 8px !important;
        border: 1px solid var(--border-subtle) !important;
    }

    /* BUTTONS - REFINED & INTENTIONAL */
    .stButton > button {
        width: 100%;
        padding: 0.875rem 1.25rem !important;
        border-radius: 8px !important;
        border: 1px solid transparent !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.2px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        position: relative;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* PRIMARY MULTI-AGENT CTA */
    div[data-testid="stButton"]:has(button[kind="primary"]) > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%) !important;
        color: #f1f5f9 !important;
        border: 1px solid var(--accent) !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35) !important;
        font-size: 1rem !important;
        padding: 1rem 1.25rem !important;
    }
    div[data-testid="stButton"]:has(button[kind="primary"]) > button:hover {
        box-shadow: 0 6px 22px rgba(59, 130, 246, 0.45) !important;
    }

    /* SECONDARY ACTION BUTTONS */
    div[data-testid="stButton"]:has(button[kind="secondary"]) > button {
        background: rgba(16, 185, 129, 0.08) !important;
        color: var(--primary) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }

    div[data-testid="stButton"]:has(button[kind="secondary"]) > button:hover {
        background: rgba(16, 185, 129, 0.15) !important;
        border-color: var(--primary) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15) !important;
    }

    /* TABS - CLEAN UNDERLINE STYLE */
    [role="tablist"] {
        gap: 0 !important;
        border-bottom: 1px solid var(--border-subtle) !important;
        padding: 0 !important;
    }

    [role="tab"] {
        padding: 1rem 1.5rem !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        color: var(--text-secondary) !important;
        border-radius: 0 !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.3s ease !important;
        position: relative;
    }

    [role="tab"]:hover {
        color: var(--primary) !important;
    }

    [role="tab"][aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom-color: var(--primary) !important;
    }

    /* ALERTS - REFINED STYLING */
    [data-testid="stSuccess"] {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
    }

    [data-testid="stError"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
    }

    [data-testid="stInfo"] {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
    }

    [data-testid="stWarning"] {
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
    }

    /* CODE BLOCKS */
    [data-testid="stCode"] {
        background: #0a0f1d !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="stCode"] code {
        color: #10b981 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 12px !important;
    }

    /* MARKDOWN HEADINGS */
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        font-family: 'Outfit', sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
    }

    [data-testid="stMarkdownContainer"] h2 {
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        font-size: 1.5rem !important;
        color: var(--primary) !important;
    }

    [data-testid="stMarkdownContainer"] h3 {
        margin-top: 1.25rem !important;
        margin-bottom: 0.75rem !important;
        font-size: 1.15rem !important;
    }

    /* SPINNER / STATUS */
    [data-testid="stSpinner"] {
        color: var(--primary) !important;
    }
    [data-testid="stStatusWidget"] {
        border-radius: 10px !important;
    }

    /* SIDEBAR FEATURE CARDS */
    .sidebar-feature {
        padding: 1rem;
        background: rgba(16, 185, 129, 0.08);
        border-left: 3px solid var(--primary);
        border-radius: 6px;
        margin: 0.75rem 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
        transition: all 0.3s ease;
    }

    .sidebar-feature:hover {
        background: rgba(16, 185, 129, 0.12);
    }

    .sidebar-feature strong {
        color: var(--primary);
        font-weight: 700;
    }

    /* STAT CARDS */
    .stat-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(59, 130, 246, 0.08));
        border: 1px solid var(--border-subtle);
        border-radius: 10px;
        padding: 1.75rem;
        margin: 1.25rem 0;
        text-align: center;
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        border-color: var(--primary);
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(59, 130, 246, 0.12));
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--primary);
        font-family: 'Outfit', sans-serif;
        letter-spacing: -1px;
    }

    .stat-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.75rem;
        font-weight: 600;
    }

    /* FOOTER */
    .footer {
        text-align: center;
        padding: 2.5rem 1.5rem;
        color: var(--text-tertiary);
        font-size: 0.85rem;
        border-top: 1px solid var(--border-subtle);
        margin-top: 3rem;
        letter-spacing: 0.3px;
    }

    .footer-text {
        line-height: 1.8;
    }

    /* QUICK ACTIONS CONTAINER */
    .quick-actions-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.5));
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.5rem;
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }

    .quick-actions-container:hover {
        border-color: rgba(16, 185, 129, 0.2);
    }

    .quick-actions-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        letter-spacing: -0.3px;
    }

    /* ANIMATIONS */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .fade-in-down {
        animation: fadeInDown 0.6s ease-out;
    }

    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }

    .slide-in-left {
        animation: slideInLeft 0.6s ease-out;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

with st.sidebar:
    st.markdown("### ⚡ COMPILER FEATURES")

    st.markdown("""
    <div class="sidebar-feature">
        <strong>▶ Code Execution</strong><br>
        <small>Run with output capture</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-feature">
        <strong>🤖 4-Stage Pipeline</strong><br>
        <small>Error Detection → Debug → Explain → Security</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-feature">
        <strong>📚 RAG Context</strong><br>
        <small>Grounded in Python docs + your past fixes</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-feature">
        <strong>🔌 MCP Server</strong><br>
        <small>Run mcp_server.py to expose the same pipeline externally</small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📎 Extra Reference Docs (optional)")
    st.caption(
        "The pipeline already includes a Python exceptions reference and PEP 8 style guide by "
        "default, and remembers code you've fixed before. Upload something here only if you want "
        "to add your OWN material - e.g. your team's style guide, or notes on a library you use a "
        "lot. Don't upload code you want fixed; paste that in the editor above instead."
    )
    uploaded_doc = st.file_uploader(
        "Upload extra reference material (.py, .md, .txt)",
        type=["py", "md", "txt"],
        label_visibility="collapsed",
    )
    if uploaded_doc is not None:
        if st.session_state["last_uploaded_doc"] != uploaded_doc.name:
            doc_text = uploaded_doc.read().decode("utf-8", errors="ignore")
            n_chunks = index_upload(uploaded_doc.name, doc_text)
            st.session_state["last_uploaded_doc"] = uploaded_doc.name
            st.success(f"Indexed {n_chunks} chunk(s) from {uploaded_doc.name}")

    st.markdown("---")

    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #cbd5e1; font-size: 0.85rem;">
        <strong>Built Using</strong><br>
        🐍 Python • 🌊 Streamlit • ✨ Gemini • 🧠 Chroma RAG<br>
        🤝 CrewAI • 🔌 MCP<br>
        <strong style="color: #10b981;">v2.1 MULTI-AGENT EDITION</strong>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header-main">
    <div class="header-title">🤖 AGENTIC AI COMPILER</div>
    <div class="header-subtitle">Multi-Agent Python Execution, Debugging & Security Review</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)


# ============================================================================
# DEFAULT CODE
# ============================================================================

default_code = '''# 🚀 Agentic AI Compiler
# Start coding or paste your Python code here

def greet(name):
    """Greet a person with AI style"""
    return f"🤖 Hello, {name}! Welcome to the Agentic AI Compiler"

if __name__ == "__main__":
    print(greet("Developer"))
    print("✨ Run this code, or launch the AI agent crew to detect, fix, explain, and security-check it")
'''


# ============================================================================
# MAIN LAYOUT
# ============================================================================

col1, col2 = st.columns([2.5, 1.5])

# LEFT COLUMN - EDITOR
with col1:
    st.markdown("""
    <div class="editor-container">
        <div class="editor-title">💻 Python Editor</div>
    </div>
    """, unsafe_allow_html=True)

    code = st_ace(
        value=default_code,
        language="python",
        theme="tomorrow_night_eighties",
        keybinding="vscode",
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        min_lines=20,
        max_lines=40,
        # auto_update=False required an explicit Ctrl+Enter inside the editor
        # before Streamlit saw new content - paste new code, click a button
        # without that keystroke, and every action ran on stale code (the
        # exact bug reported: buttons kept using the old/default code).
        auto_update=True,
        key="code_editor",
    )

    line_count = code.count("\n") + 1 if isinstance(code, str) else 0
    char_count = len(code) if isinstance(code, str) else 0
    func_count = 0
    if isinstance(code, str):
        try:
            func_count = sum(
                1 for n in ast.walk(ast.parse(code))
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        except SyntaxError:
            func_count = 0
    logging.debug(f"Code input type: {type(code)}, Line count: {line_count}")

    st.markdown(f"""
    <div class="chip-row">
        <div class="chip">📏 <strong>{line_count}</strong> lines</div>
        <div class="chip">🔤 <strong>{char_count}</strong> chars</div>
        <div class="chip">🧩 <strong>{func_count}</strong> functions</div>
    </div>
    """, unsafe_allow_html=True)

    if isinstance(code, str) and (code.count('\n') + 1) > LARGE_CODE_THRESHOLD:
        st.warning(
            "⚠ Large code detected. AI analysis may take longer."
        )


# RIGHT COLUMN - ACTION BUTTONS
with col2:
    st.markdown("""
    <div class="quick-actions-container">
        <div class="quick-actions-title">⚙ ACTIONS</div>
    </div>
    """, unsafe_allow_html=True)

    run_crew_btn = st.button(
        "🚀 RUN MULTI-AGENT ANALYSIS",
        key="run_crew_btn",
        use_container_width=True,
        type="primary",
        help="Error Detection -> Debug -> Explain -> Security, run as one pipeline",
    )

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    run_code_btn = st.button(
        "▶ RUN CODE",
        key="run_code",
        use_container_width=True,
        type="secondary",
        help="Execute your Python code",
    )


st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)


# ============================================================================
# ACTION HANDLERS - write into session_state so results survive reruns
# ============================================================================

if run_code_btn:
    try:
        st.session_state["run_result"] = {"ok": True, "output": execute_code(code)}
    except Exception as e:
        st.session_state["run_result"] = {"ok": False, "output": str(e)}

if run_crew_btn:
    steps = []
    with st.status("🤖 Multi-agent crew is analyzing your code...", expanded=True) as status:
        def _on_step(role, _text):
            steps.append(role)
            status.write(f"✅ **{role}** finished")

        status.write("🔎 Debugger Agent verifying syntax, lint, and types...")
        try:
            result = run_crew(code, on_step=_on_step)
            st.session_state["crew_result"] = result
            st.session_state["crew_steps"] = steps
            status.update(label="✅ Multi-agent analysis complete", state="complete", expanded=False)
        except Exception as e:
            st.session_state["crew_result"] = {"error": str(e)}
            status.update(label="❌ Multi-agent analysis failed", state="error", expanded=True)


# ============================================================================
# OUTPUT TABS
# ============================================================================

tab_output, tab_crew = st.tabs(
    ["📤 Run Output", "🤖 Multi-Agent Crew"]
)


# TAB 1 - RUN OUTPUT (raw execution only; syntax/fix/explain are the crew's job now)
with tab_output:
    st.markdown("### ▶ Execution Result")
    run_result = st.session_state["run_result"]
    if run_result is None:
        st.info("Click **RUN CODE** to execute your code.")
    elif run_result["ok"]:
        st.code(run_result["output"], language="python")
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number" style="color: #10b981;">✓</div>
            <div class="stat-label">Execution Successful</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error(f"❌ Execution Error: {run_result['output']}")


# TAB 2 - MULTI-AGENT CREW (4-stage pipeline: Error Detection -> Debug -> Explain -> Security)
with tab_crew:
    crew_result = st.session_state["crew_result"]
    if crew_result is None:
        st.info(
            "Click **🚀 RUN MULTI-AGENT ANALYSIS** to send your code through all four stages: "
            "Error Detection, Debug, Explain, and Security."
        )
    elif "error" in crew_result:
        st.error(
            f"❌ Crew run failed: {crew_result['error']}\n\n"
            "This needs one of three backends configured in `.env` (copy from `.env.example`):\n\n"
            "- **Gemini** (default): set `GEMINI_API_KEY` - https://aistudio.google.com/apikey\n"
            "- **OpenRouter** (fast, many models): set `OPENROUTER_API_KEY` and "
            "`CREW_MODEL=openrouter/openai/gpt-4o-mini` - https://openrouter.ai/keys\n"
            "- **Ollama** (free, local, slower): set `CREW_MODEL=ollama/qwen2.5-coder:7b` and run "
            "`ollama serve`"
        )
    else:
        knowledge_sources = crew_result.get("knowledge_sources") or []
        if knowledge_sources:
            st.caption(f"📚 RAG context used (Stages 1 & 2): {', '.join(knowledge_sources)}")

        st.markdown(f"""
        <div class="agent-card errors">
            <div class="agent-card-title">🔎 Stage 1 — Error Detection Agent</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(crew_result.get("errors", ""))
        with st.expander("Raw checker output (syntax + ruff + mypy + real sandbox run, ground truth)"):
            st.code(crew_result.get("raw_static_report", "") + "\n\n" + crew_result.get("raw_runtime_report", ""), language="text")

        st.markdown(f"""
        <div class="agent-card debug">
            <div class="agent-card-title">🐛 Stage 2 — Debug Agent</div>
        </div>
        """, unsafe_allow_html=True)
        debug_text = crew_result.get("debug", "")
        st.markdown(debug_text)
        fixed_code = extract_code_block(debug_text)
        if fixed_code:
            st.markdown("**✅ Corrected Code** — click the copy icon (top-right of the box) to copy it")
            st.code(fixed_code, language="python")

        st.markdown(f"""
        <div class="agent-card explain">
            <div class="agent-card-title">📘 Stage 3 — Explain Agent</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(crew_result.get("explain", ""))

        st.markdown(f"""
        <div class="agent-card security">
            <div class="agent-card-title">🔒 Stage 4 — Security Agent</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(crew_result.get("security", ""))
        with st.expander("Raw security scan output (ground truth — the AI summary above can be wrong; this can't)"):
            st.code(crew_result.get("raw_security_report", ""), language="text")


# ============================================================================
# FOOTER
# ============================================================================

st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <p class="footer-text">
        🚀 AGENTIC AI COMPILER v2.1 | Python • Streamlit • Gemini • CrewAI • Chroma RAG • MCP<br>
        <span style="color: #10b981;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span><br>
        <span style="font-size: 0.85rem; letter-spacing: 0.5px;">
            💡 Start writing code, then run a quick check or launch the full agent crew
        </span>
    </p>
</div>
""", unsafe_allow_html=True)
