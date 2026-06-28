# Software Architecture Document
# RAG Bank Loan Evaluator

**Version:** 1.0
**Date:** March 2026
**Module:** CCS6430 - Industrial Group Project
**Team:** [Team Name]

---

## Table of Contents

1. Introduction
2. Architectural Goals and Constraints
3. System Overview
4. Architectural Views
   - 4.1 Logical View
   - 4.2 Process View
   - 4.3 Development View
   - 4.4 Physical View
5. Component Descriptions
6. Data Architecture
7. Technology Stack
8. Design Patterns
9. Design Decisions and Rationale
10. Security Considerations
11. Performance Considerations
12. Error Handling Strategy
13. Future Architecture Considerations

---

## 1. Introduction

### 1.1 Purpose

This document describes the software architecture of the RAG Bank Loan Evaluator system. It provides a comprehensive overview of the system's structure, components, interactions, design decisions, and technical constraints. It is intended for developers, project supervisors, and stakeholders who need to understand how the system is built and why specific architectural choices were made.

### 1.2 Scope

The RAG Bank Loan Evaluator is a web-based application that evaluates bank loan applications using a hybrid approach combining deterministic business rules with Retrieval-Augmented Generation (RAG) and Large Language Model (LLM) analysis. The system provides automated loan decisions (APPROVE, REJECT, REFER FOR MANUAL REVIEW) with transparent scoring and AI-generated explanations.

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|-----------|
| RAG | Retrieval-Augmented Generation - technique that retrieves relevant documents to augment LLM prompts |
| LLM | Large Language Model - AI model capable of understanding and generating human language |
| DTI | Debt-to-Income Ratio |
| Vector Store | Database optimised for storing and querying high-dimensional vector embeddings |
| Embedding | Numerical vector representation of text that captures semantic meaning |

### 1.4 References

- Bank Rules PDF (bank-rules.pdf) - Lending policy document
- Streamlit Documentation (https://docs.streamlit.io)
- ChromaDB Documentation (https://docs.trychroma.com)
- Groq API Documentation (https://console.groq.com/docs)
- LangChain Documentation (https://python.langchain.com)

---

## 2. Architectural Goals and Constraints

### 2.1 Architectural Goals

| ID | Goal | Description |
|----|------|-----------|
| AG-01 | Transparency | Every decision must be explainable with a clear score breakdown and reasoning |
| AG-02 | Accuracy | Deterministic rules ensure compliance; LLM adds contextual analysis |
| AG-03 | Modularity | Components are loosely coupled and can be replaced independently |
| AG-04 | Extensibility | New rules, new LLM providers, or new data sources can be added without major refactoring |
| AG-05 | Usability | Non-technical bank officers can use the system through an intuitive web interface |
| AG-06 | Local-first | The system runs locally without requiring cloud infrastructure (except LLM API) |

### 2.2 Architectural Constraints

| ID | Constraint | Rationale |
|----|-----------|-----------|
| AC-01 | Python-only backend | Team expertise and ecosystem compatibility |
| AC-02 | Groq as LLM provider | Free tier availability, fast inference, LLaMA 3.3 support |
| AC-03 | Local vector database (ChromaDB) | No external database server required for deployment |
| AC-04 | Streamlit for UI | Rapid prototyping, Python-native, built-in data visualisation |
| AC-05 | Session-based storage | No persistent database; data lives in session state only |
| AC-06 | PDF-based rules | Bank rules are provided as PDF documents |

---

## 3. System Overview

### 3.1 High-Level Architecture

The system follows a layered architecture with four distinct layers:

```
+================================================================+
|                      PRESENTATION LAYER                         |
|                      (Streamlit UI)                             |
|  +----------+  +-----------+  +---------+  +----------------+  |
|  | CSV Tab  |  | New App   |  |Dashboard|  | Q&A Tab        |  |
|  |          |  | Tab       |  | Tab     |  |                |  |
|  +----------+  +-----------+  +---------+  +----------------+  |
+================================================================+
                            |
+================================================================+
|                    BUSINESS LOGIC LAYER                          |
|  +-------------------+         +-------------------+            |
|  | RAG Engine        |         | Rules Engine      |            |
|  | (rag_engine.py)   |         | (rules_engine.py) |            |
|  |                   |         |                   |            |
|  | - Orchestration   |         | - Hard rules      |            |
|  | - RAG retrieval   |         | - Soft scoring    |            |
|  | - Prompt building |         | - Score breakdown |            |
|  +-------------------+         +-------------------+            |
+================================================================+
                            |
+================================================================+
|                     DATA ACCESS LAYER                            |
|  +-------------------+         +-------------------+            |
|  | LLM API           |         | ChromaDB          |            |
|  | (llmapi.py)       |         | (Vector Stores)   |            |
|  |                   |         |                   |            |
|  | - Groq connection |         | - Rules store     |            |
|  | - Model config    |         | - Customer store  |            |
|  +-------------------+         +-------------------+            |
+================================================================+
                            |
+================================================================+
|                    EXTERNAL SERVICES                             |
|  +-------------------+         +-------------------+            |
|  | Groq Cloud API    |         | HuggingFace       |            |
|  | (LLaMA 3.3 70B)   |         | (MiniLM-L6-v2)   |            |
|  +-------------------+         +-------------------+            |
+================================================================+
```

### 3.2 Architectural Style

The system uses a **Pipe-and-Filter** architecture for the evaluation pipeline, combined with a **Layered** architecture for the overall system structure.

- **Pipe-and-Filter:** The loan evaluation flows through sequential processing stages (hard rules -> soft scoring -> RAG retrieval -> LLM analysis), where each stage can pass or reject the application.
- **Layered:** Each layer has a specific responsibility and communicates only with adjacent layers.

---

## 4. Architectural Views

### 4.1 Logical View

The logical view describes the key abstractions in the system as components and their responsibilities.

**Components:**

| Component | Responsibility | Key Operations |
|-----------|---------------|---------------|
| Streamlit UI (app.py) | User interaction, input collection, result display | render tabs, collect form data, display charts |
| RAG Engine (rag_engine.py) | Orchestrate evaluation pipeline, manage RAG retrieval | evaluate_application(), ask_question(), update_rules() |
| Rules Engine (rules_engine.py) | Apply deterministic business rules | check_hard_rules(), calculate_soft_score(), get_breakdown() |
| LLM API (llmapi.py) | Manage LLM connection and configuration | get_groqllm(), configure model parameters |
| ChromaDB Stores | Store and retrieve vector embeddings | similarity_search(), add_documents() |

**Component Interactions:**

```
app.py ----calls----> rag_engine.py ----calls----> rules_engine.py
                           |
                           +----calls----> llmapi.py ----calls----> Groq API
                           |
                           +----queries---> ChromaDB
```

### 4.2 Process View

The process view describes the runtime behaviour and concurrency aspects.

**Evaluation Process Flow:**

```
Step 1: User submits application data via Streamlit form
         |
Step 2: app.py passes data to rag_engine.evaluate_application()
         |
Step 3: rag_engine calls rules_engine.check_hard_rules(data)
         |
         +-- If FAIL --> Return immediate REJECT (no further processing)
         |
         +-- If PASS --> Continue to Step 4
         |
Step 4: rag_engine calls rules_engine.calculate_soft_score(data)
         |
         Returns: total score + breakdown per factor
         |
Step 5: rag_engine queries ChromaDB rules_vectorstore
         |
         Input: query built from applicant data
         Output: top-k relevant rule chunks from bank-rules.pdf
         |
Step 6: rag_engine queries ChromaDB customer_vectorstore
         |
         Input: query built from applicant profile
         Output: similar historical customer records
         |
Step 7: rag_engine constructs LLM prompt
         |
         Combines: applicant data + rules chunks + customer history + scoring result
         |
Step 8: rag_engine sends prompt to Groq API via llmapi
         |
         Model: LLaMA 3.3 70B Versatile
         Temperature: 0 (deterministic output)
         |
Step 9: rag_engine returns complete result to app.py
         |
         Contains: decision, score, breakdown, LLM explanation, hard rule results
         |
Step 10: app.py renders result in UI
          |
          Displays: status banner, metrics, score breakdown table, LLM explanation
```

**Concurrency Model:**

The system runs as a single-threaded Streamlit application. Each user interaction triggers a synchronous request-response cycle. There is no parallel processing of multiple requests. Batch evaluation (Evaluate All) processes applications sequentially.

### 4.3 Development View

The development view describes the source code organisation.

**Project Structure:**

```
RAG_Bank_Loan_Project/
|
+-- src/
|   +-- bankingragdemo/
|       +-- app.py                 # Streamlit UI (Presentation Layer)
|       +-- rag_engine.py          # RAG orchestration (Business Logic)
|       +-- rules_engine.py        # Deterministic rules (Business Logic)
|       +-- llmapi.py              # LLM connection (Data Access)
|       +-- bank_main.py           # Original CLI entry point
|       +-- bank_data/
|           +-- bank-rules.pdf     # Bank lending policy document
|           +-- customers.csv      # Historical customer data
|           +-- applications.csv   # Loan application records
|
+-- docs/                          # Documentation
|   +-- Software_Architecture_Document.md
|   +-- Software_Requirements_Specification.md
|   +-- Use_Case_Specification.md
|   +-- use_case_diagram.puml
|
+-- .env                           # Environment variables (not in git)
+-- .gitignore                     # Git ignore rules
+-- requirements.txt               # Python dependencies
+-- pyproject.toml                 # Project configuration
+-- test_applications.csv          # Test data for batch evaluation
```

**Module Dependencies:**

```
app.py
  +-- imports rag_engine.py
  +-- imports streamlit
  +-- imports pandas

rag_engine.py
  +-- imports rules_engine.py
  +-- imports llmapi.py
  +-- imports langchain (ChromaDB, document loaders, text splitters)
  +-- imports sentence_transformers

rules_engine.py
  +-- imports: none (pure Python logic)

llmapi.py
  +-- imports langchain_openai (ChatOpenAI)
  +-- imports dotenv
```

### 4.4 Physical View (Deployment)

The physical view describes the deployment topology.

**Local Deployment:**

```
+--------------------------------------------------+
|              User's Local Machine                 |
|                                                   |
|  +--------------------------------------------+  |
|  |          Web Browser                        |  |
|  |          localhost:8501                      |  |
|  +--------------------+-----------------------+  |
|                       |                          |
|  +--------------------v-----------------------+  |
|  |          Streamlit Server                   |  |
|  |          (Python Process)                   |  |
|  |                                             |  |
|  |  +----------+  +----------+  +-----------+  |  |
|  |  | app.py   |  | rag_     |  | rules_    |  |  |
|  |  |          |  | engine   |  | engine    |  |  |
|  |  +----------+  +----------+  +-----------+  |  |
|  |                                             |  |
|  |  +----------+  +-------------------------+  |  |
|  |  | llmapi   |  | ChromaDB (in-process)   |  |  |
|  |  +----------+  +-------------------------+  |  |
|  +--------------------------------------------+  |
|                       |                          |
+--------------------------------------------------+
                        |
          HTTPS API calls (port 443)
                        |
           +------------v-----------+
           |    Groq Cloud API      |
           |    (LLaMA 3.3 70B)    |
           |    api.groq.com       |
           +------------------------+
```

**Network Requirements:**

| Connection | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| Browser to Streamlit | HTTP | 8501 | User interface |
| Streamlit to Groq API | HTTPS | 443 | LLM inference |
| Streamlit to HuggingFace | HTTPS | 443 | Model download (first run only) |

---

## 5. Component Descriptions

### 5.1 app.py - Presentation Layer

| Attribute | Description |
|-----------|-----------|
| **Purpose** | Streamlit-based web interface providing 4 tabs and a sidebar |
| **Responsibilities** | Render UI, collect user input, display results, manage session state |
| **Key Dependencies** | streamlit, pandas, rag_engine.py |
| **Design Pattern** | Model-View pattern (Streamlit manages view; rag_engine is the model) |

**UI Components:**

| Tab | Functionality |
|-----|-------------|
| Evaluate from CSV | File upload, customer selection, single/batch evaluation |
| New Application | Manual input form with 9 fields, single evaluation |
| Dashboard | Aggregate metrics, charts (bar, distribution), history table |
| Ask about Rules | Chat-style Q&A interface for bank policy queries |
| Sidebar | System status indicators, PDF upload for rules update |

### 5.2 rag_engine.py - Business Logic / Orchestration

| Attribute | Description |
|-----------|-----------|
| **Purpose** | Central orchestrator that connects all system components |
| **Responsibilities** | Coordinate evaluation pipeline, manage vector stores, handle RAG retrieval, construct prompts |
| **Key Dependencies** | rules_engine.py, llmapi.py, langchain, chromadb, sentence_transformers |
| **Design Pattern** | Facade pattern (provides simple interface to complex subsystem) |

**Key Operations:**

| Operation | Description |
|-----------|-----------|
| evaluate_application(data) | Full pipeline: hard rules -> soft score -> RAG -> LLM -> result |
| ask_question(query) | RAG-based Q&A: retrieve rules chunks -> LLM answer |
| update_rules(pdf) | Re-index vector store with new bank rules PDF |
| load_embeddings() | Initialise vector stores from PDF and CSV data |

### 5.3 rules_engine.py - Business Logic / Rules

| Attribute | Description |
|-----------|-----------|
| **Purpose** | Deterministic evaluation of loan applications using codified bank rules |
| **Responsibilities** | Check hard rules (pass/fail), calculate soft score (0-250 points), generate score breakdown |
| **Key Dependencies** | None (pure Python) |
| **Design Pattern** | Strategy pattern (each rule is an independent scoring strategy) |

**Hard Rules (Automatic Rejection):**

| Rule | Condition | Reason |
|------|----------|--------|
| HR-01 | Age < 21 or Age > 65 | Applicant outside eligible age range |
| HR-02 | Credit Score < 550 | Credit score below minimum threshold |
| HR-03 | DTI > 0.40 | Debt-to-income ratio exceeds safe limit |
| HR-04 | Delinquencies > 2 | Too many past payment defaults |

**Soft Scoring Factors:**

| Factor | Max Points | Scoring Logic |
|--------|-----------|--------------|
| Credit Score | 50 | 750+: 50, 700-749: 40, 650-699: 20, 600-649: 10, 550-599: 5 |
| Income Level | 30 | >=60K: 30, 40-59K: 20, 25-39K: 10, <25K: 5 |
| DTI Ratio | 30 | <=0.20: 30, 0.21-0.30: 20, 0.31-0.40: 10 |
| Account Balance | 20 | >=6 months coverage: 20, 3-5 months: 10, <3 months: 5 |
| Employment | 20 | >5 years: 20, 2-5 years: 10, <2 years: 0 |
| Delinquencies | 20 | 0: 20, 1: 5, 2: 0 |
| Collateral | 20 | Secured: 20, Unsecured: 0 |
| Age | 10 | 25-55: 10, 21-24 or 56-65: 5 |
| Loan-to-Income | 50 | <0.30: 50, 0.30-0.50: 30, 0.51-1.00: 10, >1.00: 0 |

**Decision Thresholds:**

| Score Range | Decision |
|------------|---------|
| >= 200 | APPROVE |
| 150 - 199 | REFER_FOR_MANUAL_REVIEW |
| < 150 | REJECT |

### 5.4 llmapi.py - Data Access / LLM

| Attribute | Description |
|-----------|-----------|
| **Purpose** | Manage connection to the Groq LLM API |
| **Responsibilities** | Load API credentials from .env, configure model parameters, return LLM instance |
| **Key Dependencies** | langchain_openai, python-dotenv |
| **Design Pattern** | Factory pattern (creates and configures LLM instances) |

**Configuration:**

| Parameter | Value | Source |
|-----------|-------|--------|
| API Key | GROQ_KEY | .env file |
| Model | llama-3.3-70b-versatile | .env file (GROQ_MODEL) |
| Endpoint | https://api.groq.com/openai/v1 | .env file (GROQ_ENDPOINT) |
| Temperature | 0 | Hardcoded (deterministic output) |

### 5.5 ChromaDB Vector Stores

| Attribute | Description |
|-----------|-----------|
| **Purpose** | Store and retrieve document embeddings for semantic search |
| **Collections** | 2: bank_rules (from PDF), customer_history (from CSV) |
| **Embedding Model** | all-MiniLM-L6-v2 (384 dimensions) |
| **Storage** | In-process (no external server) |

**Vector Store Details:**

| Store | Source | Chunk Size | Overlap | Purpose |
|-------|--------|-----------|---------|---------|
| bank_rules | bank-rules.pdf | 300 chars | 20 chars | Retrieve relevant policy sections for evaluation and Q&A |
| customer_history | customers.csv | Per record | N/A | Find similar historical customers for comparison |

---

## 6. Data Architecture

### 6.1 Data Flow Diagram

```
                    +-------------+
                    | bank-rules  |
                    |   .pdf      |
                    +------+------+
                           |
                    PDF Loader + Text Splitter
                           |
                    +------v------+
                    | Text Chunks |
                    | (300 chars) |
                    +------+------+
                           |
                    Sentence Transformers (MiniLM-L6-v2)
                           |
                    +------v------+
                    | Embeddings  |
                    | (384-dim)   |
                    +------+------+
                           |
                    +------v------+
                    | ChromaDB    |
                    | Rules Store |
                    +-------------+


                    +-------------+
                    | customers   |
                    |   .csv      |
                    +------+------+
                           |
                    CSV Loader
                           |
                    +------v------+
                    | Customer    |
                    | Records     |
                    +------+------+
                           |
                    Sentence Transformers (MiniLM-L6-v2)
                           |
                    +------v------+
                    | Embeddings  |
                    | (384-dim)   |
                    +------+------+
                           |
                    +------v------+
                    | ChromaDB    |
                    | Cust Store  |
                    +-------------+
```

### 6.2 Data Entities

**Loan Application (Input):**

| Field | Type | Constraints | Description |
|-------|------|-----------|-----------|
| customer_id | String | Optional | Unique identifier |
| name_app | String | Required | Applicant full name |
| age | Integer | 18-100 | Applicant age |
| income | Float | > 0 | Annual gross income in EUR |
| credit_score | Integer | 300-850 | Credit bureau score |
| delinquencies | Integer | >= 0 | Number of past payment defaults |
| employment_years | Integer | >= 0 | Years of continuous employment |
| loan_amount | Float | > 0 | Requested loan amount in EUR |
| account_balance | Float | >= 0 | Current bank account balance in EUR |
| collateral | Boolean | True/False | Whether loan is secured by collateral |

**Evaluation Result (Output):**

| Field | Type | Description |
|-------|------|-----------|
| decision | Enum | APPROVE, REJECT, REFER_FOR_MANUAL_REVIEW |
| soft_score | Integer | Total risk score (0-250) |
| hard_rules_passed | Boolean | Whether all hard rules were satisfied |
| hard_rule_failures | List | Names of violated hard rules (if any) |
| score_breakdown | List | Points awarded per scoring factor |
| llm_explanation | String | AI-generated analysis and reasoning |

### 6.3 Session State Data

The application uses Streamlit session state for temporary data persistence within a user session. Data is lost when the application restarts.

| Key | Type | Content |
|-----|------|---------|
| evaluation_history | List | All evaluations performed in current session |
| chat_history | List | Q&A conversation history |
| rag_engine | Object | Initialised RAG engine instance |

---

## 7. Technology Stack

### 7.1 Complete Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Streamlit | Latest | Web UI framework |
| **Language** | Python | 3.12 | Primary programming language |
| **LLM** | LLaMA 3.3 70B Versatile | - | Large language model for analysis |
| **LLM Provider** | Groq | - | Cloud inference API |
| **Embeddings** | all-MiniLM-L6-v2 | - | Text-to-vector conversion |
| **Vector DB** | ChromaDB | Latest | Embedding storage and retrieval |
| **RAG Framework** | LangChain | Latest | RAG pipeline orchestration |
| **Data Processing** | Pandas | Latest | CSV and tabular data handling |
| **PDF Processing** | PyPDF / LangChain PDF Loader | Latest | PDF text extraction |
| **Charting** | Streamlit built-in charts | - | Dashboard visualisations |
| **Environment** | python-dotenv | Latest | Environment variable management |

### 7.2 Dependency Map

```
streamlit
  +-- pandas
  +-- altair (charts)

langchain
  +-- langchain_openai (Groq compatibility)
  +-- langchain_community
      +-- chromadb
      +-- pypdf

sentence-transformers
  +-- transformers
  +-- torch

python-dotenv
```

---

## 8. Design Patterns

### 8.1 Patterns Used

| Pattern | Where Applied | Rationale |
|---------|-------------|-----------|
| **Facade** | rag_engine.py | Provides a simple interface (evaluate_application, ask_question) hiding the complexity of rules checking, RAG retrieval, prompt construction, and LLM calls |
| **Pipe-and-Filter** | Evaluation pipeline | Application data flows through sequential stages: hard rules -> soft scoring -> RAG retrieval -> LLM analysis. Each stage can terminate the pipeline early (e.g. hard rule rejection) |
| **Strategy** | rules_engine.py | Each scoring factor (credit score, income, DTI, etc.) is an independent scoring strategy. New factors can be added without modifying existing ones |
| **Factory** | llmapi.py | get_groqllm() creates and configures LLM instances. Switching to a different provider requires only changing the factory method |
| **Observer** | Streamlit session state | UI components reactively update when session state changes |

### 8.2 Architectural Patterns

| Pattern | Description |
|---------|-----------|
| **Layered Architecture** | Clear separation between Presentation, Business Logic, Data Access, and External Services |
| **RAG (Retrieval-Augmented Generation)** | Domain-specific documents are embedded and retrieved to augment LLM prompts with relevant context |
| **Hybrid AI** | Deterministic rules provide guaranteed compliance; LLM provides flexible reasoning and explanation |

---

## 9. Design Decisions and Rationale

### 9.1 Key Decisions

| ID | Decision | Alternatives Considered | Rationale |
|----|----------|----------------------|-----------|
| DD-01 | Hybrid deterministic + LLM approach | LLM-only, Rules-only | Rules ensure regulatory compliance and consistency. LLM adds contextual reasoning for edge cases and generates human-readable explanations. Neither alone is sufficient. |
| DD-02 | ChromaDB as vector database | Pinecone, Weaviate, FAISS | ChromaDB is lightweight, runs in-process (no server), open-source, and integrates well with LangChain. Suitable for the scale of this project (small document set). |
| DD-03 | Groq as LLM provider | OpenAI, Ollama (local), HuggingFace Inference | Groq offers a free tier with generous limits, very fast inference (LPU architecture), and supports LLaMA 3.3 70B. OpenAI requires paid API. Ollama needs powerful local hardware. |
| DD-04 | Streamlit for UI | Flask + React, Gradio, Django | Streamlit enables rapid prototyping with Python-only code. Built-in widgets for forms, charts, file uploads, and session state. Ideal for data-centric applications. |
| DD-05 | Session-based storage (no database) | SQLite, PostgreSQL | Simplifies deployment (no database setup). Acceptable for a prototype/academic project. Trade-off: data lost on restart. |
| DD-06 | Sentence Transformers (MiniLM-L6-v2) | OpenAI embeddings, larger models | Open-source, runs locally (no API cost), small model (80MB), good quality for semantic search. No dependency on external embedding API. |
| DD-07 | Temperature = 0 for LLM | Higher temperature values | Deterministic output ensures consistent evaluations. Same application data will produce the same LLM analysis. Critical for banking compliance. |
| DD-08 | PDF-based rules (not hardcoded) | Hardcoded rules in Python | Bank rules can be updated by uploading a new PDF without code changes. Supports operational flexibility. The rules engine hard rules ARE hardcoded as a safety baseline. |

### 9.2 Trade-offs

| Trade-off | Chosen Approach | Advantage | Disadvantage |
|-----------|----------------|-----------|-------------|
| Speed vs Accuracy | LLM analysis for every evaluation | More thorough analysis with reasoning | Slower than pure deterministic (2-5 seconds per evaluation) |
| Simplicity vs Persistence | Session-only storage | Zero database configuration | Data lost on restart |
| Local vs Cloud LLM | Cloud (Groq API) | Access to 70B parameter model, no local GPU needed | Requires internet connection, dependent on external service |
| Small vs Large embedding model | MiniLM-L6-v2 (small) | Fast loading, low memory, runs on any machine | Lower embedding quality than larger models |

---

## 10. Security Considerations

### 10.1 Sensitive Data Handling

| Concern | Mitigation |
|---------|-----------|
| API keys in source code | Stored in .env file, excluded from Git via .gitignore |
| Customer data exposure | Data processed locally, not stored permanently, session-scoped |
| LLM data privacy | Customer data sent to Groq API for analysis. Risk: data processed externally. Mitigation: use anonymised names in production. |

### 10.2 Authentication and Access Control

The current prototype does not implement user authentication. In a production environment, the following would be required:

| Requirement | Recommendation |
|-------------|---------------|
| User authentication | OAuth2 / SSO integration with bank's identity provider |
| Role-based access | Bank Officer (evaluate, Q&A) vs Risk Manager (upload rules, analytics) |
| Audit logging | Persistent log of all evaluations with timestamp, user, and decision |
| Data encryption | HTTPS for all communications, encrypted storage for customer data |

---

## 11. Performance Considerations

### 11.1 Performance Characteristics

| Operation | Typical Duration | Bottleneck |
|-----------|-----------------|-----------|
| System startup (first run) | 30-60 seconds | Downloading embedding model from HuggingFace |
| System startup (subsequent) | 10-20 seconds | Loading embedding model + indexing documents |
| Single evaluation | 3-8 seconds | Groq API response time |
| Batch evaluation (10 records) | 30-80 seconds | Sequential Groq API calls |
| Q&A query | 2-5 seconds | Groq API response time |
| PDF upload and re-indexing | 5-15 seconds | Text extraction + embedding generation |

### 11.2 Scalability Limitations

| Limitation | Impact | Potential Solution |
|-----------|--------|-------------------|
| Single-threaded processing | Batch evaluation is sequential | Implement async API calls |
| In-process vector database | Limited by RAM | Migrate to Chroma server mode or Pinecone |
| Session-based storage | No data sharing between users | Add PostgreSQL or SQLite persistence |
| Groq API rate limits | May throttle large batch operations | Implement request queuing and retry logic |

---

## 12. Error Handling Strategy

### 12.1 Error Categories and Responses

| Error Category | Example | Handling Strategy |
|---------------|---------|------------------|
| Hard Rule Violation | Age < 21 | Return immediate REJECT with specific reason. No LLM call needed. |
| Groq API Failure | Timeout, rate limit, 500 error | Display deterministic result (score + decision) without LLM explanation. Show warning message to user. |
| Invalid Input | Negative income, text in numeric field | Streamlit form validation prevents submission. Display field-level error. |
| Invalid CSV Format | Missing required columns | Display error message listing expected column format. Do not process. |
| PDF Processing Error | Corrupted or empty PDF | Display error message. Keep existing rules unchanged. |
| Embedding Model Error | Model download failure | Display startup error. System cannot proceed without embeddings. |

### 12.2 Graceful Degradation

The system is designed to degrade gracefully:

```
Full functionality:     Hard Rules + Soft Score + RAG + LLM Explanation
LLM unavailable:        Hard Rules + Soft Score + Decision (no explanation)
Vector DB error:        Hard Rules + Soft Score + Decision (no RAG context)
Complete failure:       Error message with instructions to check configuration
```

---

## 13. Future Architecture Considerations

### 13.1 Short-term Improvements

| Improvement | Effort | Impact |
|------------|--------|--------|
| SQLite persistence for evaluation history | Low | Data survives restarts, enables audit trail |
| Async Groq API calls for batch processing | Medium | Faster batch evaluation |
| What-If analysis (scenario testing) | Low | Added value for bank officers |
| PDF export of evaluation reports | Low | Better reporting capabilities |

### 13.2 Long-term Evolution

| Evolution | Description |
|-----------|-----------|
| Multi-user support | Add authentication, role-based access, user-specific sessions |
| Production LLM | Replace Groq free tier with dedicated LLM infrastructure or private deployment |
| Persistent vector store | Move ChromaDB to server mode or cloud-hosted vector database |
| API layer | Add REST API (FastAPI) between UI and business logic for service-oriented architecture |
| Monitoring | Add logging, performance metrics, and alerting for production operation |
| CI/CD | Automated testing and deployment pipeline |

---

**Document End**
