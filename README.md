# AI Coding Platform

An AI-powered programming practice and automated evaluation platform. The system leverages **Groq LLMs** for code generation, test-case synthesis, and mentoring guidance, combined with **Judge0** for secure, sandboxed multi-language code execution.

---

## 🚀 Overview

The platform guides developers through an interactive competitive programming loop:
1. **Problem Statement Input:** Provide a programming challenge.
2. **Reference Solution Generation:** The AI generates both Brute Force and Optimal solutions in Python.
3. **Automated Test Case Generation:** Strict test cases (including boundaries and edge cases) are synthesized as structured JSON.
4. **Sandboxed Reference Validation:** Reference solutions are executed against test cases in Judge0 to verify problem correctness with zero local host execution.
5. **User Submission & Evaluation:** The user submits their solution in any supported language (Python, C++, Java, JavaScript, TypeScript, Ruby, Go, C#).
6. **Judge0 Sandboxed Testing:** Language harnesses wrap user code with standard input/output parsing and run against verified test cases.
7. **AI Error Analysis & Hints:** If any test case fails, the AI mentor analyzes the failure and offers targeted hints without revealing the full solution.

---

## 🛠️ Implemented Architecture & Tech Stack

* **LLM Engine:** [Groq](https://groq.com/) API (defaulting to `openai/gpt-oss-120b` or custom configured model) with optional Google Gemini integration.
* **Execution Engine:** [Judge0](https://ce.judge0.com/) CE REST API for sandboxed remote code execution.
* **API Service:** [FastAPI](https://fastapi.tiangolo.com/) with Pydantic schemas and CORS middleware.
* **Environment & Config:** `python-dotenv`.
* **Testing:** Python `unittest` suite with complete mock coverage for offline CI/CD.

---

## 📂 Project Structure

```text
AI coding/
├── .env.example                                      # Template for environment secrets
├── .gitignore                                        # Secret and environment exclusions
├── main.py                                           # Interactive CLI pipeline runner
├── gemini.py                                         # Model inspection & GenAI sandbox
├── requirements.txt                                  # Pinned dependencies
├── README.md                                         # Project documentation
├── funtions/                                         # Core logic modules
│   ├── extract_codes.py                              # AI solution splitter & fence cleaner
│   ├── suggestion.py                                 # AI mistake analysis & mentoring hints
│   ├── usercode_evaluation.py                        # Language harnesses, Judge0 bridge & FastAPI app
│   ├── validate_testcases.py                         # Sandboxed reference-solution validation via Judge0
│   └── complete_test_cases/
│       ├── generate_testcases.py                     # AI testcase generator & JSON parser
│       ├── testcase_validation_Judge0.py             # Base64 Judge0 communication utilities
│       ├── write_code.py                             # Reference solution generator
│       └── judge_pipeline.py                         # Standalone testing pipeline
└── tests/                                            # Comprehensive unit & integration tests
    ├── test_solution_parsing.py                      # Solution extraction tests
    ├── test_testcase_generation_parsing.py           # Testcase JSON parsing tests
    ├── test_language_mapping.py                      # Language string-to-ID mapping tests
    ├── test_judge0_parsing.py                        # Base64 & Judge0 response tests
    ├── test_feedback_parsing.py                      # AI suggestion JSON parsing tests
    ├── test_testcase_validation.py                   # Sandboxed validation tests
    ├── test_user_evaluation.py                       # User code harness & verdict tests
    ├── test_fastapi_endpoints.py                     # FastAPI router tests
    └── test_failure_scenarios.py                     # Network errors, timeouts & validation tests
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
* Python 3.10+
* Network access to Groq API and Judge0 CE API

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template and configure your API keys:
```bash
cp .env.example .env
```
Fill in `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
JUDGE0_URL=https://ce.judge0.com/submissions?wait=true
```
*(The `.env` file is excluded from Git tracking for security).*

---

## 🖥️ Running the Application

### Option A: Interactive CLI Pipeline
Run the complete end-to-end evaluation pipeline in the terminal:
```bash
python main.py
```

### Option B: FastAPI Judge Microservice
Run the standalone FastAPI server:
```bash
uvicorn funtions.usercode_evaluation:app --host 0.0.0.0 --port 8000 --reload
```
Available endpoints:
* `GET /`: Health check.
* `GET /languages`: List supported languages and Judge0 IDs.
* `POST /judge`: Submit user code and testcases for sandboxed evaluation.

Example `/judge` payload:
```json
{
  "code": "def solve(a, b): return a + b",
  "language_id": "Python 3",
  "testcases": [
    {"input": {"a": 2, "b": 3}, "expected_output": 5}
  ]
}
```

---

## 🧪 Running Automated Tests

Run the complete test suite (all external API calls to Groq and Judge0 are mocked, consuming 0 API credits):
```bash
python -m unittest discover -s tests -v
```

---

## 🔒 Security

* **No Local Host Execution:** All AI-generated reference code and user-submitted code are sent exclusively to the remote Judge0 sandbox.
* **Credentials Management:** API keys reside strictly in `.env` and environment variables; `.gitignore` blocks credentials from repository commits.
