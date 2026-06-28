# Use Case Specification Document
# RAG Bank Loan Evaluator

**Version:** 1.0
**Date:** March 2026
**Module:** CCS6430 - Industrial Group Project
**Team:** [Team Name]

---

## Table of Contents

1. Introduction
2. Actors
3. Use Case Diagram
4. UC1: Evaluate Single Loan Application
5. UC2: Batch Evaluate from CSV
6. UC3: Ask about Bank Rules
7. UC4: View Dashboard Analytics
8. UC5: Upload New Rules PDF
9. UC6: Export Evaluation Results
10. Use Case Traceability Matrix

---

## 1. Introduction

### 1.1 Purpose

This document provides a detailed specification of all use cases for the RAG Bank Loan Evaluator system. Each use case includes a full description, actors, preconditions, postconditions, main flow, alternative flows, exception flows, and business rules.

### 1.2 Scope

The system supports six primary use cases covering loan evaluation, batch processing, policy Q&A, analytics, rules management, and result export.

---

## 2. Actors

### 2.1 Primary Actors

| Actor | Description | Goals |
|-------|-----------|-------|
| Bank Officer | Front-line employee who processes loan applications daily | Evaluate applications quickly and accurately, understand bank rules, export results for reporting |
| Risk Manager | Senior employee who manages lending policies and monitors decision quality | Update bank rules, review evaluation patterns, ensure compliance |

### 2.2 Secondary Actors (External Systems)

| Actor | Description | Interaction |
|-------|-----------|------------|
| Groq LLM API | Cloud-based LLM inference service | Receives prompts, returns AI-generated analysis and reasoning |
| ChromaDB | Local vector database | Stores and retrieves document embeddings for semantic search |
| Sentence Transformers | Embedding model (all-MiniLM-L6-v2) | Converts text into 384-dimensional vector representations |

---

## 3. Use Case Diagram

Refer to the PlantUML diagram in `docs/use_case_diagram.puml` or the rendered image.

**Summary of Actor-UseCase relationships:**

```
Bank Officer -----> UC1: Evaluate Single Application
Bank Officer -----> UC2: Batch Evaluate from CSV
Bank Officer -----> UC3: Ask about Bank Rules
Bank Officer -----> UC4: View Dashboard Analytics
Bank Officer -----> UC6: Export Evaluation Results

Risk Manager -----> UC3: Ask about Bank Rules
Risk Manager -----> UC4: View Dashboard Analytics
Risk Manager -----> UC5: Upload New Rules PDF

UC1 <<includes>> Hard Rules Check
UC1 <<includes>> Soft Score Calculation
UC1 <<includes>> RAG Retrieval
UC1 <<includes>> LLM Analysis

UC2 <<includes>> UC1 (for each application)
UC2 <<extends>>  UC6 (optional export)

UC3 <<includes>> RAG Retrieval
UC3 <<includes>> LLM Analysis
```

---

## 4. UC1: Evaluate Single Loan Application

### 4.1 Brief Description

A Bank Officer enters the details of a single loan applicant through a web form. The system evaluates the application using a combination of deterministic business rules and RAG-enhanced LLM analysis, returning a decision with full scoring breakdown and AI-generated explanation.

### 4.2 Use Case Details

| Field | Value |
|-------|-------|
| **Use Case ID** | UC1 |
| **Use Case Name** | Evaluate Single Loan Application |
| **Primary Actor** | Bank Officer |
| **Secondary Actors** | Groq LLM API, ChromaDB |
| **Priority** | High |
| **Complexity** | High |

### 4.3 Preconditions

| ID | Precondition |
|----|-------------|
| PRE-1 | The system is running and accessible via browser at localhost:8501 |
| PRE-2 | The embedding model (all-MiniLM-L6-v2) is loaded successfully |
| PRE-3 | The Groq LLM API is connected (valid API key in .env) |
| PRE-4 | The bank rules vector store is populated (bank-rules.pdf indexed) |
| PRE-5 | The customer history vector store is populated (customer CSV indexed) |

### 4.4 Postconditions

| ID | Postcondition |
|----|-------------|
| POST-1 | A decision (APPROVE, REJECT, or REFER_FOR_MANUAL_REVIEW) is displayed |
| POST-2 | A detailed score breakdown table is shown |
| POST-3 | An LLM-generated explanation is available (unless hard rule rejection) |
| POST-4 | The evaluation is stored in the session history for dashboard analytics |

### 4.5 Main Flow (Success Scenario)

| Step | Actor | System |
|------|-------|--------|
| 1 | Bank Officer navigates to the "New Application" tab | System displays the input form with 9 fields |
| 2 | Bank Officer enters applicant details: Full Name, Age, Annual Income, Credit Score, Past Delinquencies, Employment Years, Loan Amount, Account Balance, Has Collateral | System validates input types and ranges |
| 3 | Bank Officer clicks "Evaluate Application" button | - |
| 4 | - | System checks all hard rules against the applicant data |
| 5 | - | All hard rules pass. System proceeds to soft scoring |
| 6 | - | System calculates soft score across 9 factors (credit, income, DTI, balance, employment, delinquencies, collateral, age, loan-to-income) |
| 7 | - | System queries ChromaDB for relevant bank rule chunks using semantic similarity |
| 8 | - | System queries ChromaDB for similar historical customer records |
| 9 | - | System constructs a prompt with applicant data, retrieved rules, and historical context |
| 10 | - | System sends prompt to Groq LLM API and receives analysis |
| 11 | - | System displays result: Status banner (colour-coded), Risk Score, Deterministic Decision, Thresholds, Score Breakdown table, LLM Explanation (collapsible) |
| 12 | Bank Officer reviews the decision and explanation | - |

### 4.6 Alternative Flow A1: Hard Rule Rejection

| Step | Description |
|------|-----------|
| A1.1 | At Step 4, one or more hard rules are violated |
| A1.2 | System immediately returns REJECT decision |
| A1.3 | System displays red status banner with "Status: Rejected" |
| A1.4 | System shows which hard rule(s) were violated (e.g. "Age 19 is below minimum 21") |
| A1.5 | System does NOT proceed to soft scoring or LLM analysis |
| A1.6 | Evaluation is stored in session history with decision = REJECT |

### 4.7 Alternative Flow A2: Refer for Manual Review

| Step | Description |
|------|-----------|
| A2.1 | At Step 6, soft score falls between 150 and 199 points |
| A2.2 | Deterministic decision is set to REFER_FOR_MANUAL_REVIEW |
| A2.3 | System proceeds with RAG retrieval and LLM analysis (Steps 7-10) |
| A2.4 | System displays orange status banner with "Status: Refer for Manual Review" |
| A2.5 | LLM explanation may recommend approval or rejection based on contextual factors |

### 4.8 Exception Flow E1: Groq API Failure

| Step | Description |
|------|-----------|
| E1.1 | At Step 10, the Groq API request fails (timeout, rate limit, network error) |
| E1.2 | System displays the deterministic result (score + decision) without LLM explanation |
| E1.3 | System shows error message: "LLM analysis unavailable. Showing deterministic result only." |

### 4.9 Exception Flow E2: Invalid Input

| Step | Description |
|------|-----------|
| E2.1 | At Step 2, user enters invalid data (e.g. negative age, text in numeric field) |
| E2.2 | Streamlit form validation prevents submission |
| E2.3 | System highlights the invalid field with an error indicator |

### 4.10 Business Rules

| Rule ID | Description |
|---------|-----------|
| BR-01 | Hard rules are always evaluated before soft rules |
| BR-02 | A single hard rule violation results in immediate rejection |
| BR-03 | Soft score thresholds: >=200 APPROVE, 150-199 REFER, <150 REJECT |
| BR-04 | DTI is calculated as: (loan_amount / 60) / (income / 12) |
| BR-05 | Account balance coverage is measured in months of loan payments |

---

## 5. UC2: Batch Evaluate from CSV

### 5.1 Brief Description

A Bank Officer uploads a CSV file containing multiple loan applications. The system evaluates either a selected individual application or all applications in the file, displaying results in a table with an option to export.

### 5.2 Use Case Details

| Field | Value |
|-------|-------|
| **Use Case ID** | UC2 |
| **Use Case Name** | Batch Evaluate from CSV |
| **Primary Actor** | Bank Officer |
| **Secondary Actors** | Groq LLM API, ChromaDB |
| **Priority** | High |
| **Complexity** | Medium |

### 5.3 Preconditions

| ID | Precondition |
|----|-------------|
| PRE-1 | System is running with all services connected |
| PRE-2 | CSV file follows the required column format (customer_id, name_app, age, income, credit_score, delinquencies, employment_years, loan_amount, account_balance, collateral) |

### 5.4 Postconditions

| ID | Postcondition |
|----|-------------|
| POST-1 | Selected or all applications have been evaluated |
| POST-2 | Results are displayed in the UI |
| POST-3 | All evaluations are added to session history |
| POST-4 | CSV download is available (if batch evaluation performed) |

### 5.5 Main Flow (Success Scenario)

| Step | Actor | System |
|------|-------|--------|
| 1 | Bank Officer navigates to "Evaluate from CSV" tab | System displays file uploader and default application data |
| 2 | Bank Officer uploads a CSV file | System parses the CSV and displays a preview table |
| 3 | Bank Officer selects a customer from the dropdown | System highlights the selected customer |
| 4 | Bank Officer clicks "Evaluate Selected" | - |
| 5 | - | System evaluates the selected application through the full pipeline (UC1) |
| 6 | - | System displays the full result for the selected customer |

### 5.6 Alternative Flow A1: Evaluate All Applications

| Step | Description |
|------|-----------|
| A1.1 | At Step 4, Bank Officer clicks "Evaluate All" instead of "Evaluate Selected" |
| A1.2 | System iterates through all rows in the CSV |
| A1.3 | For each row, system performs the full evaluation pipeline (UC1) |
| A1.4 | System displays a progress indicator during processing |
| A1.5 | System displays a summary results table with all decisions |
| A1.6 | System offers "Download CSV" button for export (triggers UC6) |

### 5.7 Alternative Flow A2: No CSV Uploaded

| Step | Description |
|------|-----------|
| A2.1 | Bank Officer does not upload a CSV file |
| A2.2 | System loads the default application data from the built-in CSV files |
| A2.3 | Flow continues from Step 3 with default data |

### 5.8 Exception Flow E1: Invalid CSV Format

| Step | Description |
|------|-----------|
| E1.1 | At Step 2, the uploaded CSV has missing or incorrect columns |
| E1.2 | System displays an error message listing the expected column format |
| E1.3 | System prompts the user to upload a corrected file |

### 5.9 Exception Flow E2: Groq API Rate Limit During Batch

| Step | Description |
|------|-----------|
| E2.1 | During batch evaluation (A1.3), the Groq API returns a rate limit error |
| E2.2 | System pauses briefly and retries the request |
| E2.3 | If retry fails, system records the evaluation with deterministic result only |
| E2.4 | System continues with the remaining applications |

---

## 6. UC3: Ask about Bank Rules

### 6.1 Brief Description

A Bank Officer or Risk Manager asks a natural language question about bank lending policies. The system retrieves relevant sections from the bank rules PDF using semantic search and generates an accurate answer using the LLM.

### 6.2 Use Case Details

| Field | Value |
|-------|-------|
| **Use Case ID** | UC3 |
| **Use Case Name** | Ask about Bank Rules (Q&A) |
| **Primary Actor** | Bank Officer / Risk Manager |
| **Secondary Actors** | Groq LLM API, ChromaDB |
| **Priority** | Medium |
| **Complexity** | Medium |

### 6.3 Preconditions

| ID | Precondition |
|----|-------------|
| PRE-1 | Bank rules PDF has been indexed in ChromaDB |
| PRE-2 | LLM connection is active |

### 6.4 Postconditions

| ID | Postcondition |
|----|-------------|
| POST-1 | An accurate answer based on the bank rules is displayed |
| POST-2 | The question and answer are stored in chat history |

### 6.5 Main Flow (Success Scenario)

| Step | Actor | System |
|------|-------|--------|
| 1 | User navigates to "Ask about Rules" tab | System displays chat interface with input field |
| 2 | User types a question (e.g. "What credit score do I need to get approved?") | - |
| 3 | User presses Enter or clicks send button | - |
| 4 | - | System performs semantic similarity search on the rules vector store |
| 5 | - | System retrieves the top relevant rule chunks from ChromaDB |
| 6 | - | System constructs a prompt with the question and retrieved context |
| 7 | - | System sends the prompt to Groq LLM API |
| 8 | - | System displays the LLM-generated answer in the chat |
| 9 | User reads the answer and optionally asks a follow-up question | Chat history is maintained for context |

### 6.6 Alternative Flow A1: Follow-up Question

| Step | Description |
|------|-----------|
| A1.1 | At Step 9, user types a follow-up question |
| A1.2 | System maintains previous chat history in session state |
| A1.3 | System performs new retrieval and LLM query |
| A1.4 | Answer is appended to the chat history |

### 6.7 Exception Flow E1: No Relevant Rules Found

| Step | Description |
|------|-----------|
| E1.1 | At Step 5, semantic search returns low-relevance chunks |
| E1.2 | LLM generates a response based on available context |
| E1.3 | Response may indicate that the specific topic is not covered in the current rules document |

### 6.8 Example Queries

| Query | Expected Response Topic |
|-------|----------------------|
| "What credit score do I need to get approved?" | Credit score thresholds and point allocation |
| "What are the hard reject rules?" | List of automatic rejection conditions |
| "How is the debt-to-income ratio calculated?" | DTI formula and threshold values |
| "What is the minimum age for a loan application?" | Age hard rule (21-65 range) |
| "How does collateral affect the loan decision?" | Collateral scoring (+20 points for secured) |
| "What happens if I have past delinquencies?" | Delinquency hard rule (>2 reject) and soft scoring |
| "How many points do I need for approval?" | Threshold explanation (200+ approve, 150-199 refer, <150 reject) |

---

## 7. UC4: View Dashboard Analytics

### 7.1 Brief Description

A Bank Officer or Risk Manager views aggregated statistics and visualisations of all loan evaluations performed during the current session, including decision distribution, score trends, and evaluation history.

### 7.2 Use Case Details

| Field | Value |
|-------|-------|
| **Use Case ID** | UC4 |
| **Use Case Name** | View Dashboard Analytics |
| **Primary Actor** | Bank Officer / Risk Manager |
| **Secondary Actors** | None |
| **Priority** | Medium |
| **Complexity** | Low |

### 7.3 Preconditions

| ID | Precondition |
|----|-------------|
| PRE-1 | At least one evaluation has been performed in the current session |

### 7.4 Postconditions

| ID | Postcondition |
|----|-------------|
| POST-1 | Dashboard displays current session statistics (read-only, no data modified) |

### 7.5 Main Flow (Success Scenario)

| Step | Actor | System |
|------|-------|--------|
| 1 | User navigates to "Dashboard" tab | - |
| 2 | - | System retrieves all evaluations from session state |
| 3 | - | System calculates aggregate metrics: total evaluations, approve count, reject count, refer count, average risk score |
| 4 | - | System generates decision distribution bar chart |
| 5 | - | System generates score distribution chart |
| 6 | - | System displays evaluation history table with columns: Name, Decision, Score, Timestamp |
| 7 | User reviews the analytics and identifies patterns | - |

### 7.6 Alternative Flow A1: No Evaluations Yet

| Step | Description |
|------|-----------|
| A1.1 | At Step 2, session state contains no evaluations |
| A1.2 | System displays a message: "No evaluations performed yet. Evaluate applications to see analytics." |
| A1.3 | Dashboard charts and metrics are empty or show zero values |

### 7.7 Dashboard Metrics Specification

| Metric | Calculation | Display |
|--------|-----------|---------|
| Total Evaluations | Count of all evaluations in session | Large number |
| Approved | Count where decision = APPROVE | Green number |
| Rejected | Count where decision = REJECT | Red number |
| Referred | Count where decision = REFER_FOR_MANUAL_REVIEW | Orange number |
| Average Score | Mean of all soft scores | Number with "pts" suffix |
| Decision Distribution | Count per decision type | Bar chart |
| Score Distribution | Histogram of soft scores | Bar chart |

---

## 8. UC5: Upload New Rules PDF

### 8.1 Brief Description

A Risk Manager uploads a new bank rules PDF document to replace the existing lending policy. The system re-indexes the vector store so that all subsequent evaluations and Q&A queries use the updated rules.

### 8.2 Use Case Details

| Field | Value |
|-------|-------|
| **Use Case ID** | UC5 |
| **Use Case Name** | Upload New Rules PDF |
| **Primary Actor** | Risk Manager |
| **Secondary Actors** | ChromaDB, Sentence Transformers |
| **Priority** | Medium |
| **Complexity** | Medium |

### 8.3 Preconditions

| ID | Precondition |
|----|-------------|
| PRE-1 | System is running with embedding model loaded |
| PRE-2 | New bank rules document is available in PDF format |

### 8.4 Postconditions

| ID | Postcondition |
|----|-------------|
| POST-1 | Old rules vector store is cleared |
| POST-2 | New PDF is chunked, embedded, and stored in ChromaDB |
| POST-3 | All subsequent evaluations use the new rules |
| POST-4 | All subsequent Q&A queries reference the new rules |
| POST-5 | System status confirms successful update |

### 8.5 Main Flow (Success Scenario)

| Step | Actor | System |
|------|-------|--------|
| 1 | Risk Manager locates the "Upload New Rules PDF" section in the sidebar | System displays file uploader (accepts PDF only, max 200MB) |
| 2 | Risk Manager uploads the new PDF file | - |
| 3 | - | System extracts text content from the PDF |
| 4 | - | System splits the text into chunks (size: 300 characters, overlap: 20 characters) |
| 5 | - | System generates embeddings for each chunk using Sentence Transformers |
| 6 | - | System clears the existing rules collection in ChromaDB |
| 7 | - | System stores the new embeddings and chunks in ChromaDB |
| 8 | - | System updates the rules retriever with the new vector store |
| 9 | - | System displays success confirmation message |
| 10 | Risk Manager verifies by asking a question about the new rules in the Q&A tab | System returns answers based on the new rules |

### 8.6 Exception Flow E1: Invalid PDF

| Step | Description |
|------|-----------|
| E1.1 | At Step 3, the uploaded file is corrupted or not a valid PDF |
| E1.2 | System displays an error message: "Unable to process the uploaded file. Please ensure it is a valid PDF." |
| E1.3 | The existing rules remain unchanged |

### 8.7 Exception Flow E2: Empty PDF

| Step | Description |
|------|-----------|
| E2.1 | At Step 3, the PDF contains no extractable text (e.g. scanned image without OCR) |
| E2.2 | System displays a warning: "No text content found in the uploaded PDF." |
| E2.3 | The existing rules remain unchanged |

---

## 9. UC6: Export Evaluation Results

### 9.1 Brief Description

After performing batch evaluations, a Bank Officer downloads the results as a CSV file for reporting, record-keeping, or further analysis.

### 9.2 Use Case Details

| Field | Value |
|-------|-------|
| **Use Case ID** | UC6 |
| **Use Case Name** | Export Evaluation Results |
| **Primary Actor** | Bank Officer |
| **Secondary Actors** | None |
| **Priority** | Low |
| **Complexity** | Low |

### 9.3 Preconditions

| ID | Precondition |
|----|-------------|
| PRE-1 | A batch evaluation (UC2 - Evaluate All) has been completed |
| PRE-2 | Results are available in the session state |

### 9.4 Postconditions

| ID | Postcondition |
|----|-------------|
| POST-1 | CSV file is downloaded to the user's local machine |

### 9.5 Main Flow (Success Scenario)

| Step | Actor | System |
|------|-------|--------|
| 1 | Bank Officer has completed a batch evaluation (UC2) | System displays results table with "Download CSV" button |
| 2 | Bank Officer clicks the "Download CSV" button | - |
| 3 | - | System converts the evaluation results to CSV format |
| 4 | - | System triggers a file download in the browser |
| 5 | Bank Officer saves the file to their local machine | - |

### 9.6 Exported CSV Format

| Column | Description |
|--------|-----------|
| customer_id | Unique applicant identifier |
| name | Applicant name |
| decision | APPROVE / REJECT / REFER_FOR_MANUAL_REVIEW |
| risk_score | Soft score total (integer) |
| hard_rules_passed | TRUE / FALSE |
| hard_rule_failures | List of violated hard rules (if any) |

---

## 10. Use Case Traceability Matrix

### 10.1 Use Case to Functional Requirements

| Use Case | Related Functional Requirements |
|----------|-------------------------------|
| UC1 | FR-01 to FR-12 |
| UC2 | FR-13 to FR-17 |
| UC3 | FR-22 to FR-24 |
| UC4 | FR-18 to FR-21 |
| UC5 | FR-25 to FR-27 |
| UC6 | FR-17 |

### 10.2 Use Case to System Components

| Use Case | app.py | rag_engine.py | rules_engine.py | llmapi.py | ChromaDB |
|----------|--------|--------------|----------------|-----------|----------|
| UC1 | X | X | X | X | X |
| UC2 | X | X | X | X | X |
| UC3 | X | X | - | X | X |
| UC4 | X | - | - | - | - |
| UC5 | X | X | - | - | X |
| UC6 | X | - | - | - | - |

### 10.3 Use Case to Actors

| Use Case | Bank Officer | Risk Manager |
|----------|-------------|-------------|
| UC1 | Primary | - |
| UC2 | Primary | - |
| UC3 | Primary | Primary |
| UC4 | Primary | Primary |
| UC5 | - | Primary |
| UC6 | Primary | - |

### 10.4 Use Case Dependencies

```
UC2 depends on UC1 (batch evaluation calls single evaluation for each row)
UC6 depends on UC2 (export requires batch evaluation results)
UC3 depends on UC5 (Q&A quality depends on indexed rules)
UC1 depends on UC5 (evaluation uses indexed rules for RAG retrieval)
```

---

**Document End**
