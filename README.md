# RAG Bank Loan Evaluation System

A Retrieval-Augmented Generation (RAG) system that evaluates bank loan
applications by combining deterministic business rules with LLM-powered
reasoning.

## Technology Stack

- **Python** 3.12 or later
- **LLM Provider** -- Groq API (LLaMA 3.3 70B Versatile)
- **Embeddings** -- sentence-transformers/all-MiniLM-L6-v2 (HuggingFace)
- **Vector Database** -- ChromaDB
- **Framework** -- LangChain
- **Backend API** -- FastAPI (by Uvicorn)
- **UI** -- Streamlit

## Project Structure

```
run.py               -- One-command launcher (starts backend + UI together)
src/bankingragdemo/
    api.py           -- FastAPI REST backend (evaluation, Q&A, rules upload)
    app.py           -- Streamlit web interface (4 tabs)
    rag_engine.py    -- Reusable RAG backend (embeddings, retrieval, evaluation)
    rules_engine.py  -- Deterministic hard/soft rule engine
    llmapi.py        -- LLM connection helper (Groq)
    bank_main.py     -- Standalone CLI evaluation script
    example2.py      -- Minimal RAG demo script
bank_data/
    bank-rules.pdf   -- Loan approval rules document
    bank_customers.csv   -- Historical customer data
    loan_applications.csv -- Sample loan applications
tests/
    test_rules_engine.py -- Unit tests for the rules engine (pytest)
```

## Setup

### 1. Create virtual environment

```bash
py -3.12 -m venv .venv
```

### 2. Activate virtual environment

**PowerShell:**
```
.venv\Scripts\Activate.ps1
```

**CMD:**
```
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
GROQ_KEY=<your Groq API key>
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_ENDPOINT=https://api.groq.com/openai/v1
```

Get your Groq API key from https://console.groq.com

### 5. Run the application

The system has two processes: a FastAPI backend (port 8000) and the
Streamlit UI (port 8501). The backend must be running before the UI.

**Easiest (one command):**

```bash
python run.py
```

This starts the backend, waits until it is ready, then launches the UI, and
shuts both down on Ctrl+C.

**Manual (two terminals):**

```bash
# Terminal 1 - backend
python src/bankingragdemo/api.py
```

```bash
# Terminal 2 - frontend
streamlit run src/bankingragdemo/app.py
```

The UI opens at http://localhost:8501 and talks to the backend at
http://localhost:8000.

**CLI reference script (no UI):**

```bash
cd src/bankingragdemo
python bank_main.py
```

## How It Works

1. **PDF Rules Ingestion** -- The bank-rules PDF is split into chunks,
   embedded and stored in ChromaDB.
2. **Customer History** -- Historical customer data is converted to text
   summaries, embedded and stored in a separate collection.
3. **Hard Rules Check** -- Each application is first checked against
   non-negotiable rules (age, credit score, DTI, etc.).
4. **Soft Scoring** -- Applications that pass hard rules receive a
   points-based score from multiple weighted factors.
5. **LLM Analysis** -- The most relevant rule chunks and historical
   records are retrieved and sent to the LLM alongside the applicant
   data for a reasoned decision with explanation.

## Decision Thresholds

| Score       | Decision                 |
|-------------|--------------------------|
| >= 200 pts  | APPROVE                  |
| 150-199 pts | REFER FOR MANUAL REVIEW  |
| < 150 pts   | REJECT                   |


## Testing

For tests pytest is used. The requirements-dev.txt has the python package required. The command "pytest tests/test_rules_engine.py" can be used.
This test runs 31 checks on the rules and if they are applied properly.
