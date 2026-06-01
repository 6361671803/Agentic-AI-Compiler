
# 🤖 Agentic AI Compiler

An advanced AI-powered Python Compiler built using Streamlit, Gemini AI, and Python.

The application can execute Python code, detect syntax errors, explain code, fix errors using AI, and perform security analysis.

---

## 🚀 Features

### ✅ Syntax Checking
- Detects Python syntax errors instantly
- Highlights error messages
- Fast code validation

### ✅ Code Execution
- Executes Python programs
- Displays output in real time
- Captures runtime errors

### ✅ AI Code Fixer
- Uses Gemini AI
- Automatically fixes syntax errors
- Suggests corrected code
- Provides detailed explanations

### ✅ AI Code Explanation
- Explains Python code in beginner-friendly language
- Explains functions, loops, conditions, and variables
- Helps students learn programming

### ✅ Security Analysis
- Detects risky coding patterns
- Identifies dangerous functions
- Improves code safety

### ✅ Large Code Support
- Analyzes long Python programs
- Generates fixes and explanations

---

## 🛠️ Technologies Used

- Python 3.11
- Streamlit
- Gemini AI API
- Google GenAI SDK
- Python AST
- Logging

---

## 📂 Project Structure

```text
Agentic-AI-Compiler/
│
├── agents/
│   └── ai_helper.py
│
├── compiler/
│   ├── parser.py
│   └── executor.py
│
├── ui/
│   └── app.py
│
├── reports/
│
├── tests/
│
├── .env
├── requirements.txt
├── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/your-username/Agentic-AI-Compiler.git
```

### Open Project

```bash
cd Agentic-AI-Compiler
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Gemini API Setup

Create a file named:

```text
.env
```

Add:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Get API key from:

https://aistudio.google.com

---

## ▶️ Run Application

```bash
streamlit run ui/app.py
```

Application runs at:

```text
http://localhost:8501
```

---

## 📸 Screenshots

### Home Page

Add Screenshot Here

### AI Code Fixer

Add Screenshot Here

### AI Explanation

Add Screenshot Here

### Security Analysis

Add Screenshot Here

---

## 🧪 Sample Test

### Input

```python
for i in range(5)
    print(i)
```

### AI Output

```python
for i in range(5):
    print(i)
```

### Explanation

- Missing colon after for loop
- Correct indentation added

---

## 🎯 Future Enhancements

- Multi-Agent Architecture
- Code Optimization Agent
- Test Case Generator
- PDF Report Generator
- Complexity Analyzer
- Multi-Language Support
- Code Quality Score

---

## 👨‍💻 Author

Developed using Python, Streamlit, and Gemini AI.

---

## 📜 License

This project is for educational and research purposes.
