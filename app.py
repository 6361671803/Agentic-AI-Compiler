import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from compiler.parser import check_syntax
from compiler.executor import execute_code
from agents.ai_helper import ask_ai
import time

LARGE_CODE_THRESHOLD = 100


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
        margin-bottom: 2.5rem;
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
        margin-bottom: 1.5rem;
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
    
    /* TEXT AREA STYLING - CLEAN & FOCUSED */
    textarea {
        background-color: #0f172a !important;
        color: #10b981 !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
        padding: 1.25rem !important;
        line-height: 1.7 !important;
        transition: all 0.3s ease !important;
    }
    
    textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1), 0 4px 12px rgba(16, 185, 129, 0.15) !important;
        outline: none !important;
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
    
    /* PRIMARY ACTION BUTTON */
    [data-testid="stButton"]:nth-child(1) > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #0f172a !important;
        border: 1px solid var(--primary) !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
    }
    
    [data-testid="stButton"]:nth-child(1) > button:hover {
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35) !important;
    }
    
    /* SECONDARY ACTION BUTTONS */
    [data-testid="stButton"]:nth-child(n+2) > button {
        background: rgba(16, 185, 129, 0.08) !important;
        color: var(--primary) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }
    
    [data-testid="stButton"]:nth-child(n+2) > button:hover {
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
    
    /* SPINNER */
    [data-testid="stSpinner"] {
        color: var(--primary) !important;
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
        <strong>✅ Syntax Checking</strong><br>
        <small>Detect errors instantly</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-feature">
        <strong>🤖 AI Debugging</strong><br>
        <small>Intelligent code fixing</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-feature">
        <strong>▶ Code Execution</strong><br>
        <small>Run with output capture</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-feature">
        <strong>📘 AI Explanation</strong><br>
        <small>Understand your code</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-feature">
        <strong>🔍 Security Analysis</strong><br>
        <small>Detect risky patterns</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #cbd5e1; font-size: 0.85rem;">
        <strong>Built Using</strong><br>
        🐍 Python • 🌊 Streamlit • 🦙 Ollama<br>
        <strong style="color: #10b981;">v1.0 DEVELOPER EDITION</strong>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header-main">
    <div class="header-title">🤖 AGENTIC AI COMPILER</div>
    <div class="header-subtitle">Professional Python Execution & Intelligent Debugging</div>
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
    print("✨ Use the tabs to check syntax, run code, fix errors, or get explanations")
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
    
    code = st.text_area(
        label="code_input",
        value=default_code,
        height=420,
        label_visibility="collapsed"
    )
    line_count = code.count("\n") + 1 if isinstance(code, str) else "N/A"
    logging.debug(f"Code input type: {type(code)}, Line count: {line_count}")
    
    if isinstance(code, str) and (code.count('\n') + 1) > LARGE_CODE_THRESHOLD:
        st.warning(
            "⚠ Large code detected. AI analysis may take longer."
        )


# RIGHT COLUMN - ACTION BUTTONS
with col2:
    st.markdown("""
    <div class="quick-actions-container">
        <div class="quick-actions-title">⚙ QUICK ACTIONS</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_btn = st.container()
    
    with col_btn:
        syntax_check = st.button(
            "🧠 CHECK SYNTAX",
            key="syntax_check",
            use_container_width=True,
            help="Validate your Python code syntax"
        )
        
        run_code = st.button(
            "▶ RUN CODE",
            key="run_code",
            use_container_width=True,
            help="Execute your Python code"
        )
        
        ai_fix = st.button(
            "🤖 AI FIX",
            key="ai_fix",
            use_container_width=True,
            help="Get AI-powered code fixes"
        )
        
        ai_explain = st.button(
            "📘 EXPLAIN",
            key="ai_explain",
            use_container_width=True,
            help="Get AI explanation of your code"
        )


st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)


# ============================================================================
# OUTPUT TABS
# ============================================================================

tab1, tab2 = st.tabs(["📤 Compiler Output", "🤖 AI Analysis"])


# TAB 1 - COMPILER OUTPUT
with tab1:
    col_output_1, col_output_2 = st.columns(2)
    
    with col_output_1:
        if syntax_check:
            st.markdown("### 🧠 Syntax Validation")
            result = check_syntax(code)
            
            if "No syntax" in result:
                st.success("✅ " + result)
                st.markdown("""
                <div class="stat-card">
                    <div class="stat-number">✓</div>
                    <div class="stat-label">Code is Clean</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ " + result)
                st.markdown("""
                <div class="stat-card" style="border-color: #ef4444;">
                    <div class="stat-number" style="color: #ef4444;">⚠</div>
                    <div class="stat-label">Errors Detected</div>
                </div>
                """, unsafe_allow_html=True)
    
    with col_output_2:
        if run_code:
            st.markdown("### ▶ Execution Result")
            
            try:
                output = execute_code(code)
                st.code(output, language="python")
                
                st.markdown("""
                <div class="stat-card">
                    <div class="stat-number" style="color: #10b981;">✓</div>
                    <div class="stat-label">Execution Successful</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Execution Error: {str(e)}")


# TAB 2 - AI ANALYSIS
with tab2:
    if ai_fix:
        st.markdown("### 🤖 AI Code Fixer")
        
        with st.spinner("🔄 AI is analyzing and fixing your code..."):
            time.sleep(0.5)  # UX delay for perceived thinking
            
            prompt = f"""
You are a senior Python software engineer.

Analyze the entire code carefully.

Return your response in the following format:

## Errors Found
- List all syntax errors
- List all logical errors

## Corrected Code
Provide the complete corrected code.

## Explanation
Explain every fix clearly.

## Optimization Suggestions
Suggest improvements for readability, performance, and maintainability.

Rules:
1. Fix all syntax errors.
2. Fix logical mistakes if found.
3. Return complete corrected code.
4. Mention line numbers whenever possible.
5. Keep explanations professional and concise.

Code:

{code}
"""
            response = ask_ai(prompt)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1));
                       border: 1px solid rgba(16, 185, 129, 0.3);
                       border-radius: 8px;
                       padding: 1.5rem;
                       margin: 1rem 0;">
            """, unsafe_allow_html=True)
            if "503" in str(response):
                st.warning(
                    "⚠ Gemini servers are busy. Please try again in a few moments."
                )
            else:
                st.write(response)
            st.markdown("</div>", unsafe_allow_html=True)
    
    if ai_explain:
        st.markdown("### 📘 AI Code Explanation")
        
        with st.spinner("🔍 AI is analyzing your code..."):
            time.sleep(0.5)  # UX delay
            prompt = f"""
You are an expert Python teacher.

Explain the following code:

1. Overall purpose of the program.
2. Explain every function.
3. Explain every loop.
4. Explain every condition.
5. Explain important variables.
6. Mention time complexity if possible.
7. Mention space complexity if possible.
8. Use beginner-friendly language.

Code:

{code}
"""
            response = ask_ai(prompt)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1));
                       border: 1px solid rgba(59, 130, 246, 0.3);
                       border-radius: 8px;
                       padding: 1.5rem;
                       margin: 1rem 0;">
            """, unsafe_allow_html=True)
            st.write(response)
            st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# FOOTER
# ============================================================================

st.markdown('<div class="divider-gradient"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <p class="footer-text">
        🚀 AGENTIC AI COMPILER v1.0 | Developed with Python • Streamlit • Ollama LLM<br>
        <span style="color: #10b981;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span><br>
        <span style="font-size: 0.85rem; letter-spacing: 0.5px;">
            💡 Start writing code or paste your Python scripts above
        </span>
    </p>
</div>
""", unsafe_allow_html=True)
