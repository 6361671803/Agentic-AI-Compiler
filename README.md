# 🤖 Agentic AI Compiler

An AI-powered Python compiler built with Streamlit and a 4-stage CrewAI multi-agent
pipeline. Paste in Python code and it gets checked, fixed, explained, and
security-scanned by four cooperating agents - each grounded by real tools
(ast, ruff, mypy, sandboxed execution), not just an LLM's guess.

##domolink:https://youtu.be/CsDJMVyDfqo?si=sJVikH-QX4cc8gSz

---

## 🚀 Features

### 🔎 4-Stage Multi-Agent Pipeline
- **Error Detection Agent** - finds every issue across 6 categories (syntax,
  indentation, runtime, logical, type, edge-case), grounded by real syntax/
  lint/type-check/sandbox-execution output
- **Debug Agent** - fixes every issue found and outputs the complete
  corrected file; the fix is then automatically re-checked by the same real
  tools, and re-fixed if anything's still wrong, before you ever see it
- **Explain Agent** - explains what the corrected code does, why each error
  happened, and suggests concrete improvements (as suggestions, not applied)
- **Security Agent** - independently scans for dangerous patterns (`eval`,
  `exec`, shell injection, hardcoded secrets, unsafe deserialization, and
  more), with a verified-findings fallback so a wrong "no issues" from the
  AI never overrides the real scanner

### ⚡ Two speeds
- **Run Multi-Agent Analysis** - the full pipeline above, thorough
- **Run Code** - just execute and see output, no AI involved

### 📚 RAG (Retrieval-Augmented Generation)
Grounds the pipeline in a curated Python knowledge base (built-in
exceptions, PEP 8) plus a running memory of code you've submitted before and
how it was fixed - never this app's own source code, which caused a real,
fixed bug where the AI would parrot irrelevant project internals back as
"corrected code."

### 🔌 MCP Server
`mcp_server.py` exposes the same pipeline (plus individual tools: lint,
type-check, sandboxed execution, PyPI dependency lookup) to any MCP client
(Claude Desktop, Claude Code, etc.) over stdio.

### 🧠 Model backend
Runs on **Gemini** (cloud, fast) by default, or **local Ollama** (free,
private, no API key) with one environment variable - see Setup below.

---

## 🛠️ Technologies Used

- Python
- Streamlit + streamlit-ace (syntax-highlighted editor)
- CrewAI (multi-agent orchestration)
- Gemini API / Ollama (LLM backend)
- ChromaDB (local vector store for RAG)
- MCP (Model Context Protocol)
- ruff, mypy, ast (real static analysis - not LLM guesses)

---

## 📂 Project Structure

```text
Agentic-AI-Compiler/
│
├── agents/
│   ├── crew.py          # the 4-stage pipeline
│   ├── rag.py            # RAG: knowledge base + past-fix memory
│   ├── ai_helper.py       # single-prompt LLM helper (used by MCP tools)
│   └── text_utils.py
│
├── compiler/
│   ├── parser.py          # syntax checking
│   ├── executor.py        # code execution
│   ├── checks.py          # lint / type-check / security scan
│   └── sandbox.py         # isolated subprocess execution
│
├── ui/
│   └── app.py             # Streamlit app
│
├── knowledge/              # curated Python reference docs (RAG source)
├── mcp_server.py            # MCP server exposing the pipeline externally
├── tests/
├── requirements.txt
└── .env.example             # copy to .env and add your own key
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/6361671803/Agentic-AI-Compiler.git
cd Agentic-AI-Compiler
```

### Create & activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Model Setup

Copy `.env.example` to `.env`, then either:

**Use Gemini (default, cloud, fast)** - add your key:
```env
GEMINI_API_KEY=your-real-key
```
Get one at https://aistudio.google.com/apikey

**Or use local Ollama (free, private, no key needed)** - set:
```env
CREW_MODEL=ollama/qwen2.5-coder:7b
```
(requires `ollama serve` running locally with that model pulled)

---

## ▶️ Run Application

```bash
streamlit run ui/app.py
```

Runs at http://localhost:8501

### Run the MCP server (optional, for external MCP clients)

```bash
python mcp_server.py
```

---

## 🧪 Sample

### Input

```python
def divide(a, b)
    return a / b

result = divide(10, 0)
print(result)
```

### Pipeline Output

- **Error Detection**: missing colon on line 1 (syntax error)
- **Debug**: fixes the colon, verifies the result against real checkers (0 errors), outputs the complete corrected file
- **Explain**: what changed and why, plus suggestions (e.g. handle division by zero)
- **Security**: no issues found

---

## 🎯 Future Enhancements

- Code Optimization Agent
- Test Case Generator
- PDF Report Generator
- Complexity Analyzer
- Multi-Language Support
- Code Quality Score

---

## 👨‍💻 Author

Developed using Python, Streamlit, CrewAI, and Gemini/Ollama.

---

## 📜 License

This project is for educational and research purposes.
