# Software Requirements Specification (SRS)
# RAG Bank Loan Evaluator

**Version:** 1.0
**Date:** March 2026
**Module:** CCS6430 - Industrial Group Project
**Team:** [Team Name]

---

## Table of Contents

1. Introduction
2. Overall Description
3. System Features and Functional Requirements
4. Use Cases
5. Non-Functional Requirements
6. Data Requirements
7. External Interface Requirements
8. System Architecture
9. Technology Stack
10. Glossary

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for the RAG Bank Loan Evaluator, an AI-powered loan application assessment system. The system combines deterministic business rules with Retrieval-Augmented Generation (RAG) to provide transparent, explainable, and consistent loan approval decisions.

### 1.2 Scope

The RAG Bank Loan Evaluator assists bank officers in evaluating loan applications by:

- Automatically checking applications against predefined hard and soft business rules
- Leveraging historical customer data for contextual decision-making
- Providing AI-generated explanations for each decision
- Supporting both individual and batch evaluations
- Offering a natural language Q&A interface for bank policy inquiries

### 1.3 Intended Audience

- Bank Officers: Primary users who evaluate loan applications
- Risk Managers: Users who manage evaluation policies and review analytics
- Auditors: Users who review decision history for compliance purposes

### 1.4 Definitions and Acronyms

| Acronym | Definition |
|---------|-----------|
| RAG | Retrieval-Augmented Generation |
| LLM | Large Language Model |
| DTI | Debt-to-Income Ratio |
| SRS | Software Requirements Specification |

---

## 2. Overall Description

### 2.1 Product Perspective

The system is a standalone web application that integrates with the Groq cloud API for LLM inference. It uses ChromaDB as a local vector database for document retrieval and Sentence Transformers for text embedding generation.

### 2.2 User Classes and Characteristics

| User Class | Description | Frequency of Use |
|-----------|-------------|-----------------|
| Bank Officer | Evaluates individual and batch loan applications, asks questions about rules | Daily |
| Risk Manager | Updates bank rules, reviews dashboard analytics, monitors decision patterns | Weekly |

### 2.3 Operating Environment

- Operating System: Windows 10/11, macOS, Linux
- Python: 3.12+
- Browser: Any modern browser (Chrome, Edge, Firefox)
- Internet: Required for Groq API access

### 2.4 Constraints

- Requires active internet connection for LLM inference via Groq API
- Groq free tier has rate limits (30 requests/minute)
- Vector database stored locally (not distributed)
- Session-based evaluation history (not persisted across restarts)

---

## 3. System Features and Functional Requirements

### 3.1 Hard Rules Engine

**FR-01:** The system SHALL automatically reject applications that violate any of the following hard rules:

| Rule ID | Condition | Action |
|---------|-----------|--------|
| HR-01 | Applicant age < 21 or > 65 | Automatic REJECT |
| HR-02 | Employment history < 1 year | Automatic REJECT |
| HR-03 | Past delinquencies > 2 | Automatic REJECT |
| HR-04 | Credit score < 550 | Automatic REJECT |
| HR-05 | Debt-to-Income ratio > 0.40 | Automatic REJECT |

**FR-02:** If any hard rule is violated, the system SHALL immediately return a REJECT decision without proceeding to soft scoring or LLM analysis.

**FR-03:** The system SHALL display the specific hard rule(s) that caused the rejection.

### 3.2 Soft Scoring Engine

**FR-04:** For applications that pass all hard rules, the system SHALL calculate a soft score based on the following factors:

| Factor | Max Points | Scoring Tiers |
|--------|-----------|---------------|
| Credit Score | 50 | 750+: 50, 700-749: 40, 650-699: 20, 550-649: 10, <550: 0 |
| Income Level | 30 | >=60K: 30, 40-59K: 20, 25-39K: 10, <25K: 0 |
| DTI Ratio | 30 | <=0.20: 30, 0.21-0.30: 20, 0.31-0.40: 10, >0.40: 0 |
| Account Balance | 20 | >=6 months coverage: 20, 3-5 months: 10, <3 months: 0 |
| Employment Stability | 20 | >=5 years: 20, 2-4 years: 10, <2 years: 0 |
| Delinquency History | 20 | 0 defaults: 20, 1 default: 5, 2+ defaults: 0 |
| Collateral | 20 | Secured: 20, Unsecured: 0 |
| Age (Optimal Range) | 10 | 25-55: 10, outside: 0 |
| Loan vs Income Ratio | 20 | <=30%: 20, <=50%: 10, >50%: 0 |

**FR-05:** The system SHALL map the total soft score to a decision:

| Score Range | Decision |
|------------|----------|
| >= 200 points | APPROVE |
| 150 - 199 points | REFER FOR MANUAL REVIEW |
| < 150 points | REJECT |

**FR-06:** The system SHALL display a detailed score breakdown showing each factor, the applicant's value, and the points awarded.

### 3.3 RAG-Enhanced LLM Analysis

**FR-07:** After deterministic evaluation, the system SHALL retrieve relevant bank rule chunks from the vector database using semantic similarity search.

**FR-08:** The system SHALL retrieve similar historical customer records from the customer vector database.

**FR-09:** The system SHALL construct a prompt containing the applicant data, retrieved rules, and historical context, and send it to the Groq LLM for analysis.

**FR-10:** The system SHALL display the LLM-generated explanation alongside the deterministic decision.

### 3.4 Single Application Evaluation (New Application Tab)

**FR-11:** The system SHALL provide a form with the following input fields:

| Field | Type | Validation |
|-------|------|-----------|
| Full Name | Text | Required |
| Age | Integer | 18 - 100 |
| Annual Income | Integer | > 0 |
| Credit Score | Integer | 300 - 850 |
| Past Delinquencies | Integer | >= 0 |
| Employment Years | Integer | >= 0 |
| Loan Amount Requested | Integer | > 0 |
| Account Balance | Integer | >= 0 |
| Has Collateral | Checkbox | Boolean |

**FR-12:** Upon form submission, the system SHALL evaluate the application and display the full result including status, score, breakdown, and LLM explanation.

### 3.5 Batch Evaluation (CSV Upload Tab)

**FR-13:** The system SHALL accept CSV file uploads containing multiple loan applications.

**FR-14:** The system SHALL display the uploaded data as a preview table.

**FR-15:** The system SHALL allow the user to select and evaluate a single application from the uploaded data.

**FR-16:** The system SHALL allow the user to evaluate all applications in the uploaded CSV with one click.

**FR-17:** The system SHALL provide a downloadable CSV file containing the evaluation results.

### 3.6 Dashboard Analytics

**FR-18:** The system SHALL display the following session metrics:

- Total number of evaluations performed
- Count of APPROVE decisions
- Count of REJECT decisions
- Count of REFER decisions
- Average risk score

**FR-19:** The system SHALL display a bar chart showing decision distribution.

**FR-20:** The system SHALL display a score distribution chart.

**FR-21:** The system SHALL display an evaluation history table with all session evaluations.

### 3.7 Bank Rules Q&A

**FR-22:** The system SHALL provide a chat interface where users can ask natural language questions about bank policies.

**FR-23:** The system SHALL retrieve relevant rule chunks from the vector database to answer the question.

**FR-24:** The system SHALL maintain chat history within the session.

### 3.8 Rules Management

**FR-25:** The system SHALL allow users to upload a new bank rules PDF via the sidebar.

**FR-26:** Upon new PDF upload, the system SHALL re-index the vector store with the new rules.

**FR-27:** The system SHALL display system status indicators showing:

- Embeddings model loaded
- LLM connection status
- Vector databases ready

---

## 4. Use Cases

### UC1: Evaluate Single Loan Application

| Field | Description |
|-------|-----------|
| **Actor** | Bank Officer |
| **Precondition** | System is running, LLM is connected |
| **Trigger** | Officer fills in the New Application form and clicks Submit |
| **Main Flow** | 1. Officer enters applicant data in the form 2. System checks hard rules 3. System calculates soft score 4. System retrieves relevant rules and historical data via RAG 5. System sends context to LLM for analysis 6. System displays decision with score breakdown and explanation |
| **Alternative Flow** | If hard rule violated, system returns immediate REJECT with reason (skips steps 3-5) |
| **Postcondition** | Evaluation result is stored in session history |

### UC2: Batch Evaluate from CSV

| Field | Description |
|-------|-----------|
| **Actor** | Bank Officer |
| **Precondition** | CSV file with correct column format is available |
| **Trigger** | Officer uploads CSV and clicks Evaluate All or Evaluate Selected |
| **Main Flow** | 1. Officer uploads CSV file 2. System displays data preview 3. Officer selects evaluation mode (single or all) 4. System evaluates each application through the full pipeline 5. System displays results table 6. Officer downloads results as CSV |
| **Postcondition** | All evaluations stored in session history, CSV download available |

### UC3: Ask about Bank Rules

| Field | Description |
|-------|-----------|
| **Actor** | Bank Officer / Risk Manager |
| **Precondition** | Bank rules PDF has been indexed |
| **Trigger** | User types a question in the Q&A tab |
| **Main Flow** | 1. User types question (e.g. "What credit score is needed?") 2. System performs semantic search on rules vector store 3. System sends retrieved chunks + question to LLM 4. System displays answer |
| **Postcondition** | Question and answer added to chat history |

### UC4: View Dashboard Analytics

| Field | Description |
|-------|-----------|
| **Actor** | Bank Officer / Risk Manager |
| **Precondition** | At least one evaluation has been performed in current session |
| **Trigger** | User navigates to Dashboard tab |
| **Main Flow** | 1. System retrieves evaluation history from session state 2. System calculates aggregate metrics 3. System generates charts (decision distribution, score distribution) 4. System displays metrics, charts, and history table |
| **Postcondition** | None (read-only view) |

### UC5: Upload New Rules PDF

| Field | Description |
|-------|-----------|
| **Actor** | Risk Manager |
| **Precondition** | New bank rules PDF is available |
| **Trigger** | User uploads PDF via sidebar uploader |
| **Main Flow** | 1. User uploads new PDF 2. System extracts text and splits into chunks 3. System generates embeddings for each chunk 4. System clears old rules vector store 5. System stores new embeddings in ChromaDB 6. System confirms successful update |
| **Postcondition** | All subsequent evaluations and Q&A use the new rules |

### UC6: Export Evaluation Results

| Field | Description |
|-------|-----------|
| **Actor** | Bank Officer |
| **Precondition** | Batch evaluation has been completed |
| **Trigger** | User clicks Download CSV button |
| **Main Flow** | 1. System converts evaluation results to CSV format 2. System provides downloadable file |
| **Postcondition** | CSV file downloaded to user's machine |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement |
|----|------------|
| NFR-01 | Single application evaluation SHALL complete within 15 seconds |
| NFR-02 | Batch evaluation of 10 applications SHALL complete within 3 minutes |
| NFR-03 | Q&A response SHALL be returned within 10 seconds |
| NFR-04 | Application startup (embedding model + vector stores) SHALL complete within 60 seconds |

### 5.2 Usability

| ID | Requirement |
|----|------------|
| NFR-05 | The interface SHALL be accessible via any modern web browser |
| NFR-06 | Decision results SHALL use colour-coded indicators (green=approve, red=reject, orange=refer) |
| NFR-07 | The system SHALL provide clear error messages for invalid inputs |

### 5.3 Reliability

| ID | Requirement |
|----|------------|
| NFR-08 | The deterministic rules engine SHALL produce consistent results for identical inputs |
| NFR-09 | The system SHALL handle Groq API failures gracefully with error messages |
| NFR-10 | Vector database files SHALL persist locally between application restarts |

### 5.4 Security

| ID | Requirement |
|----|------------|
| NFR-11 | API keys SHALL be stored in environment variables (.env file), never in source code |
| NFR-12 | The .env file SHALL be excluded from version control via .gitignore |
| NFR-13 | The application SHALL run on localhost only (not exposed to public internet) |

### 5.5 Maintainability

| ID | Requirement |
|----|------------|
| NFR-14 | Bank rules SHALL be updatable by uploading a new PDF without code changes |
| NFR-15 | LLM provider SHALL be configurable via environment variables |
| NFR-16 | Code SHALL be modular with separate files for UI, rules engine, RAG engine, and LLM API |

---

## 6. Data Requirements

### 6.1 Input Data

**Loan Application Data (CSV or Form):**

| Field | Type | Description |
|-------|------|-----------|
| customer_id | String | Unique identifier |
| name_app | String | Applicant full name |
| age | Integer | Applicant age |
| income | Float | Annual income in EUR |
| credit_score | Integer | Credit score (300-850) |
| delinquencies | Integer | Number of past defaults |
| employment_years | Integer | Years of employment |
| loan_amount | Float | Requested loan amount in EUR |
| account_balance | Float | Current account balance in EUR |
| collateral | Boolean | Whether loan is secured |

**Bank Rules Document:**

- Format: PDF
- Content: Hard rules, soft scoring criteria, thresholds, policy guidelines
- Location: bank_data/bank-rules.pdf

**Historical Customer Data:**

- Format: CSV
- Content: Past customer records with loan outcomes
- Location: bank_data/bank_customers.csv

### 6.2 Output Data

| Output | Format | Description |
|--------|--------|-----------|
| Decision | String | APPROVE, REJECT, or REFER_FOR_MANUAL_REVIEW |
| Risk Score | Integer | Cumulative soft score (0-250) |
| Score Breakdown | Table | Per-factor scoring details |
| LLM Explanation | Text | AI-generated reasoning for the decision |
| Batch Results | CSV | Downloadable file with all evaluation decisions |

### 6.3 Data Storage

| Store | Technology | Persistence |
|-------|-----------|------------|
| Bank Rules Vectors | ChromaDB (chroma_db_bank_rules) | Persistent on disk |
| Customer History Vectors | ChromaDB (chroma_db_customer_history) | Persistent on disk |
| Evaluation History | Streamlit Session State | Session only (lost on restart) |
| Chat History | Streamlit Session State | Session only (lost on restart) |

---

## 7. External Interface Requirements

### 7.1 User Interface

- Framework: Streamlit
- Layout: Tabbed interface with 4 main tabs + sidebar
- Tabs: Evaluate from CSV, New Application, Dashboard, Ask about Rules
- Sidebar: System status indicators, Rules PDF upload

### 7.2 External APIs

| API | Provider | Purpose | Protocol |
|-----|----------|---------|----------|
| Groq API | Groq Inc. | LLM inference (LLaMA 3.3 70B) | HTTPS REST |
| HuggingFace Hub | HuggingFace | Embedding model download | HTTPS |

### 7.3 Configuration

| Variable | Description | Source |
|----------|-----------|--------|
| GROQ_KEY | API authentication key | .env file |
| GROQ_MODEL | LLM model name (llama-3.3-70b-versatile) | .env file |
| GROQ_ENDPOINT | API base URL (https://api.groq.com/openai/v1) | .env file |

---

## 8. System Architecture

### 8.1 Architecture Overview

The system follows a layered architecture pattern:

```
+-----------------------------------------------------------+
|                    PRESENTATION LAYER                      |
|                    Streamlit UI (app.py)                   |
|  [CSV Tab] [New App Tab] [Dashboard Tab] [Q&A Tab]        |
+-----------------------------------------------------------+
                            |
+-----------------------------------------------------------+
|                    BUSINESS LOGIC LAYER                    |
|  +------------------+  +-------------------------------+  |
|  | Rules Engine      |  | RAG Engine                    |  |
|  | (rules_engine.py) |  | (rag_engine.py)               |  |
|  | - Hard Rules      |  | - Document Retrieval          |  |
|  | - Soft Scoring    |  | - Context Building            |  |
|  | - Decision Logic  |  | - LLM Prompt Construction     |  |
|  +------------------+  +-------------------------------+  |
+-----------------------------------------------------------+
                            |
+-----------------------------------------------------------+
|                    DATA ACCESS LAYER                       |
|  +------------------+  +-------------------------------+  |
|  | LLM API           |  | ChromaDB                      |  |
|  | (llmapi.py)       |  | - Rules Vector Store          |  |
|  | - Groq Connection |  | - Customer Vector Store       |  |
|  +------------------+  +-------------------------------+  |
+-----------------------------------------------------------+
                            |
+-----------------------------------------------------------+
|                    EXTERNAL SERVICES                       |
|  [Groq API / LLaMA 3.3]     [HuggingFace / MiniLM-L6]   |
+-----------------------------------------------------------+
```

### 8.2 Data Flow

```
User Input --> Hard Rules Check --> [FAIL] --> REJECT
                    |
                  [PASS]
                    |
              Soft Score Calculation
                    |
              RAG Retrieval (rules + customer history)
                    |
              LLM Analysis (Groq / LLaMA 3.3)
                    |
              Decision: APPROVE / REFER / REJECT
                    |
              Display Result + Score Breakdown + Explanation
```

### 8.3 Component Description

| Component | File | Responsibility |
|-----------|------|---------------|
| UI Layer | app.py | User interface, input forms, result display, charts |
| RAG Engine | rag_engine.py | Evaluation orchestration, vector store management, RAG retrieval |
| Rules Engine | rules_engine.py | Hard rule checks, soft score calculation, deterministic decisions |
| LLM API | llmapi.py | Groq API connection, LLM configuration |
| Bank Main | bank_main.py | Legacy CLI entry point (reference only) |

---

## 9. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend | Streamlit | Latest | Web UI framework |
| Language | Python | 3.12 | Primary programming language |
| LLM | LLaMA 3.3 70B | 70B-versatile | Large Language Model for reasoning |
| LLM Provider | Groq API | - | Cloud inference API |
| Embeddings | all-MiniLM-L6-v2 | - | Sentence Transformer for text vectorisation |
| Vector Database | ChromaDB | Latest | Local vector storage and retrieval |
| LLM Framework | LangChain | Latest | LLM orchestration and prompt management |
| Data Processing | Pandas | Latest | CSV handling and data manipulation |

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| RAG (Retrieval-Augmented Generation) | AI technique that retrieves relevant documents from a knowledge base and uses them as context for an LLM to generate accurate responses |
| LLM (Large Language Model) | AI model trained on large text datasets capable of understanding and generating human language |
| Embeddings | Numerical vector representations of text that capture semantic meaning for similarity search |
| Vector Database | Database optimised for storing and querying embeddings using similarity search |
| Hard Rules | Non-negotiable conditions that automatically reject an application if violated |
| Soft Rules | Scoring factors that add points to a risk score to determine the final decision |
| Risk Score | Cumulative points from soft rules used to determine loan approval |
| DTI (Debt-to-Income Ratio) | Total debt payments divided by gross monthly income |
| Credit Score | Numerical score representing a borrower's creditworthiness (300-850) |
| Collateral | Asset pledged as security for the loan |
| Delinquency | Failure to make a loan payment on time |
| Deterministic Decision | Decision made purely by coded rules without LLM involvement |
| LLM-Augmented Decision | Decision where the LLM analyses rules and historical data to provide reasoning |
| Chunking | Splitting large documents into smaller pieces for embedding and retrieval |
| Cosine Similarity | Mathematical measure of similarity between two vectors |
| Semantic Search | Search based on meaning rather than exact keyword matching |

---

**Document End**
