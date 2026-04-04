# User Interface Prototype Document
# RAG Bank Loan Evaluator

**Version:** 1.0
**Date:** March 2026
**Module:** CCS6430 - Industrial Group Project
**Team:** [Team Name]

---

## Table of Contents

1. Introduction
2. UI Overview
3. Layout Structure
4. Screen Descriptions
   - 4.1 Sidebar
   - 4.2 Tab 1: Evaluate from CSV
   - 4.3 Tab 2: New Application
   - 4.4 Tab 3: Dashboard
   - 4.5 Tab 4: Ask about Rules
5. Evaluation Result Display
6. UI Components Specification
7. Colour Scheme and Visual Design
8. User Interaction Flows
9. Responsive Behaviour
10. Accessibility Considerations

---

## 1. Introduction

### 1.1 Purpose

This document describes the user interface design of the RAG Bank Loan Evaluator system. It provides wireframes, component specifications, and interaction descriptions for each screen. It serves as a reference for understanding the UI layout, visual design, and user workflows.

### 1.2 UI Framework

The interface is built using Streamlit, a Python-based web framework for data applications. Streamlit provides built-in components for forms, charts, file uploads, and session state management.

### 1.3 Access

The application is accessed via a web browser at `http://localhost:8501` after starting the Streamlit server.

---

## 2. UI Overview

The application uses a single-page layout with a **sidebar** on the left and a **tabbed main content area** on the right. The four tabs represent the core functionalities of the system.

```
+------------------------------------------------------------------+
|                     Bank Loan Evaluator                           |
|          RAG-powered loan application evaluation system           |
+------------------------------------------------------------------+
|          |                                                        |
| SIDEBAR  |   [Evaluate from CSV] [New Application]               |
|          |   [Dashboard] [Ask about Rules]                        |
|          |                                                        |
| System   |   +------------------------------------------------+  |
| Status   |   |                                                |  |
|          |   |          ACTIVE TAB CONTENT                    |  |
| Upload   |   |                                                |  |
| Rules    |   |                                                |  |
| PDF      |   |                                                |  |
|          |   +------------------------------------------------+  |
+------------------------------------------------------------------+
```

---

## 3. Layout Structure

### 3.1 Page Configuration

| Property | Value |
|----------|-------|
| Page Title | Bank Loan Evaluator |
| Page Icon | (none) |
| Layout | Wide |
| Initial Sidebar State | Expanded |

### 3.2 Header

| Element | Description |
|---------|-----------|
| Title | "Bank Loan Evaluator" - large bold heading (h1) |
| Subtitle | "RAG-powered loan application evaluation system" - grey caption text |
| Separator | Horizontal divider line below subtitle |

### 3.3 Navigation

| Element | Description |
|---------|-----------|
| Type | Horizontal tab bar |
| Tabs | Evaluate from CSV, New Application, Dashboard, Ask about Rules |
| Behaviour | Clicking a tab switches the main content area. Active tab is underlined. |

---

## 4. Screen Descriptions

### 4.1 Sidebar

The sidebar is persistent across all tabs and contains system information and configuration options.

**Wireframe:**

```
+---------------------------+
|  System Status            |
|                           |
|  [=] Embeddings loaded    |
|  [=] LLM connected (Groq)|
|  [=] Vector databases     |
|      ready                |
|                           |
|  ________________________ |
|                           |
|  Upload New Rules PDF     |
|  Replace bank rules       |
|                           |
|  +---------------------+  |
|  | Drag and drop file  |  |
|  | here                |  |
|  | Limit 200MB - PDF   |  |
|  |                     |  |
|  | [Browse files]      |  |
|  +---------------------+  |
+---------------------------+
```

**Component Specification:**

| Component | Type | Description |
|-----------|------|-----------|
| System Status heading | st.header | Section title |
| Embeddings loaded | st.success | Green indicator showing embedding model is ready |
| LLM connected (Groq) | st.success | Green indicator showing Groq API connection is active |
| Vector databases ready | st.success | Green indicator showing ChromaDB stores are populated |
| Upload New Rules PDF heading | st.header | Section title |
| Replace bank rules | st.caption | Instructional text |
| File uploader | st.file_uploader | Accepts PDF files only, max 200MB, drag-and-drop enabled |

---

### 4.2 Tab 1: Evaluate from CSV

This tab allows batch evaluation of loan applications from a CSV file.

**Wireframe - Initial State (before evaluation):**

```
+----------------------------------------------------------+
|  Loan Applications                                        |
|  Upload custom applications CSV (optional)                |
|                                                           |
|  +-----------------------------------------------------+ |
|  | Drag and drop file here         [Browse files]       | |
|  | Limit 200MB per file - CSV                           | |
|  +-----------------------------------------------------+ |
|                                                           |
|  +-----------------------------------------------------+ |
|  | customer_id | name_app | age | income | credit_score | |
|  |-------------|----------|-----|--------|--------------|  |
|  | C001        | Maria A. | 67  | 51048  | 625          | |
|  | C002        | Giorgos  | 57  | 70302  | 516          | |
|  | C003        | Sophia A.| 55  | 41062  | 779          | |
|  | C004        | Petros C.| 64  | 70392  | 674          | |
|  | C005        | Maria G. | 26  | 62052  | 676          | |
|  +-----------------------------------------------------+ |
|                                                           |
|  Select a customer to evaluate          [Evaluate All]    |
|  [C001 - Maria A.            v]                           |
|                                                           |
|  [Evaluate Selected]                                      |
+----------------------------------------------------------+
```

**Wireframe - After Single Evaluation:**

```
+----------------------------------------------------------+
|  +-----------------------------------------------------+ |
|  |              Status: Approved                        | |
|  +-----------------------------------------------------+ |
|                                                           |
|  +-----------------+-----------------+-----------------+  |
|  |   Risk Score    | Deterministic   |   Thresholds    |  |
|  |                 |   Decision      |                 |  |
|  |   220 pts       |   APPROVE       | >=200 Approve   |  |
|  |                 |                 | 150-199 Refer   |  |
|  |                 |                 | <150 Reject     |  |
|  +-----------------+-----------------+-----------------+  |
|                                                           |
|  Score Breakdown:                                         |
|  +-----------------------------------------------------+ |
|  | factor              | condition        | points      | |
|  |---------------------|------------------|-------------|  |
|  | Credit Score        | 780 (750+)       | 50          | |
|  | Income Level        | 72,000 (>=60K)   | 30          | |
|  | DTI Ratio           | 0.04 (<=0.20)    | 30          | |
|  | Account Balance     | 25,000 (>=6 mo)  | 20          | |
|  | Employment          | 8 years (>=5)    | 20          | |
|  | Delinquency History | 0 defaults       | 20          | |
|  | Collateral          | Secured          | 20          | |
|  | Age                 | 32 (25-55)       | 10          | |
|  | Loan-to-Income      | 0.21 (0.30-0.50)| 30          | |
|  +-----------------------------------------------------+ |
|                                                           |
|  > LLM Explanation (click to expand)                      |
|    [Detailed AI-generated analysis of the application...] |
+----------------------------------------------------------+
```

**Wireframe - After Batch Evaluation (Evaluate All):**

```
+----------------------------------------------------------+
|  Results:                                                 |
|  +-----------------------------------------------------+ |
|  |   | name      | decision                            | |
|  |---|-----------|-------------------------------------| |
|  |   | Maria A.  | REJECT                              | |
|  |   | Giorgos B.| REJECT                              | |
|  |   | Sophia A. | APPROVE                             | |
|  |   | Petros C. | REJECT                              | |
|  |   | Maria G.  | REJECT                              | |
|  +-----------------------------------------------------+ |
|                                                           |
|  [Download results as CSV]                                |
+----------------------------------------------------------+
```

**Component Specification:**

| Component | Type | Description |
|-----------|------|-----------|
| Heading | st.header | "Loan Applications" |
| Caption | st.caption | "Upload custom applications CSV (optional)" |
| CSV Uploader | st.file_uploader | Accepts CSV files, drag-and-drop |
| Data Preview | st.dataframe | Shows uploaded or default data in table format |
| Customer Selector | st.selectbox | Dropdown list of all customers (ID - Name) |
| Evaluate Selected | st.button | Red button, evaluates the selected customer |
| Evaluate All | st.button | Outlined button, evaluates all customers in CSV |
| Status Banner | st.markdown (HTML) | Colour-coded banner: green (approve), red (reject), orange (refer) |
| Metrics Row | st.markdown (HTML table) | Three-column layout: Risk Score, Decision, Thresholds |
| Score Breakdown | st.dataframe | Table showing points per scoring factor |
| LLM Explanation | st.expander | Collapsible section with AI-generated analysis |
| Results Table | st.dataframe | Summary table after batch evaluation |
| Download Button | st.download_button | Export results as CSV file |

---

### 4.3 Tab 2: New Application

This tab provides a manual input form for evaluating a single loan application.

**Wireframe:**

```
+----------------------------------------------------------+
|  New Loan Application                                     |
|  Enter applicant details manually                         |
|                                                           |
|  +-----------------------------------------------------+ |
|  |                                                     | |
|  |  Full Name:      [________________________]         | |
|  |                                                     | |
|  |  Age:             [___] (min: 18, max: 100)         | |
|  |                                                     | |
|  |  Annual Income:   [___________] (EUR)               | |
|  |                                                     | |
|  |  Credit Score:    [___] (min: 300, max: 850)        | |
|  |                                                     | |
|  |  Past             [___] (min: 0)                    | |
|  |  Delinquencies:                                     | |
|  |                                                     | |
|  |  Employment       [___] (years)                     | |
|  |  Years:                                             | |
|  |                                                     | |
|  |  Loan Amount      [___________] (EUR)               | |
|  |  Requested:                                         | |
|  |                                                     | |
|  |  Account          [___________] (EUR)               | |
|  |  Balance:                                           | |
|  |                                                     | |
|  |  Has Collateral:  [ ] (checkbox)                    | |
|  |                                                     | |
|  |  [Evaluate Application]                             | |
|  |                                                     | |
|  +-----------------------------------------------------+ |
|                                                           |
|  (Result displayed below after evaluation - same format   |
|   as Tab 1: Status Banner + Metrics + Breakdown + LLM)    |
+----------------------------------------------------------+
```

**Form Field Specification:**

| Field | Widget Type | Default | Min | Max | Step | Required |
|-------|-----------|---------|-----|-----|------|----------|
| Full Name | st.text_input | "" | - | - | - | Yes |
| Age | st.number_input | 30 | 18 | 100 | 1 | Yes |
| Annual Income | st.number_input | 30000 | 0 | - | 1000 | Yes |
| Credit Score | st.number_input | 650 | 300 | 850 | 1 | Yes |
| Past Delinquencies | st.number_input | 0 | 0 | - | 1 | Yes |
| Employment Years | st.number_input | 5 | 0 | - | 1 | Yes |
| Loan Amount Requested | st.number_input | 10000 | 0 | - | 1000 | Yes |
| Account Balance | st.number_input | 5000 | 0 | - | 500 | Yes |
| Has Collateral | st.checkbox | False | - | - | - | Yes |
| Submit Button | st.form_submit_button | - | - | - | - | - |

---

### 4.4 Tab 3: Dashboard

This tab displays aggregated analytics for all evaluations performed in the current session.

**Wireframe - With Data:**

```
+----------------------------------------------------------+
|  Evaluation Dashboard                                     |
|                                                           |
|  +----------+  +----------+  +----------+  +-----------+ |
|  |  Total   |  | Approved |  | Rejected |  | Referred  | |
|  |    8     |  |    3     |  |    4     |  |    1      | |
|  +----------+  +----------+  +----------+  +-----------+ |
|                                                           |
|  +----------+                                             |
|  | Avg Score|                                             |
|  |  165 pts |                                             |
|  +----------+                                             |
|                                                           |
|  Decision Distribution:                                   |
|  +-----------------------------------------------------+ |
|  |  APPROVE   |||||||||||                     37.5%     | |
|  |  REJECT    ||||||||||||||||                50.0%     | |
|  |  REFER     ||||                            12.5%     | |
|  +-----------------------------------------------------+ |
|                                                           |
|  Score Distribution:                                      |
|  +-----------------------------------------------------+ |
|  |       *                                              | |
|  |    *  *  *                                           | |
|  |  * *  *  * *                                         | |
|  |  * *  *  * *  *                                      | |
|  +--+--+--+--+--+--+--+--+--+--> Score                 | |
|  100  120  140  160  180  200  220                       | |
|  +-----------------------------------------------------+ |
|                                                           |
|  Evaluation History:                                      |
|  +-----------------------------------------------------+ |
|  | Name      | Decision  | Score | Timestamp            | |
|  |-----------|-----------|-------|----------------------| |
|  | Elena K.  | APPROVE   | 220   | 2026-03-27 14:30:00 | |
|  | Dimitris  | REJECT    | 115   | 2026-03-27 14:31:00 | |
|  | Anna P.   | REJECT    | 0     | 2026-03-27 14:32:00 | |
|  | Kostas R. | APPROVE   | 240   | 2026-03-27 14:33:00 | |
|  +-----------------------------------------------------+ |
+----------------------------------------------------------+
```

**Wireframe - Empty State:**

```
+----------------------------------------------------------+
|  Evaluation Dashboard                                     |
|                                                           |
|  No evaluations performed yet.                            |
|  Evaluate applications to see analytics here.             |
+----------------------------------------------------------+
```

**Component Specification:**

| Component | Type | Description |
|-----------|------|-----------|
| Heading | st.header | "Evaluation Dashboard" |
| Total Evaluations | st.metric | Count of all evaluations |
| Approved Count | st.metric | Count of APPROVE decisions (green) |
| Rejected Count | st.metric | Count of REJECT decisions (red) |
| Referred Count | st.metric | Count of REFER decisions (orange) |
| Average Score | st.metric | Mean risk score across all evaluations |
| Decision Distribution | st.bar_chart | Bar chart showing count per decision type |
| Score Distribution | st.bar_chart | Histogram of risk scores |
| History Table | st.dataframe | Scrollable table of all past evaluations |

---

### 4.5 Tab 4: Ask about Rules

This tab provides a chat-style interface for asking questions about bank lending policies.

**Wireframe:**

```
+----------------------------------------------------------+
|  Ask about Bank Rules                                     |
|  Ask any question about loan approval rules and policies. |
|                                                           |
|  +-----------------------------------------------------+ |
|  |                                                     | |
|  |  User: What credit score do I need to get           | |
|  |        approved?                                    | |
|  |                                                     | |
|  |  AI: Based on the bank rules, the credit score      | |
|  |  plays a significant role in the loan evaluation.   | |
|  |  The scoring system awards points as follows:       | |
|  |  - 750+: 50 points                                  | |
|  |  - 700-749: 40 points                               | |
|  |  - 650-699: 20 points                               | |
|  |  ...                                                | |
|  |                                                     | |
|  |  User: What happens if I have 2 delinquencies?      | |
|  |                                                     | |
|  |  AI: According to the bank rules, having 2 past     | |
|  |  delinquencies does not trigger the hard reject     | |
|  |  rule (which requires more than 2). However...      | |
|  |                                                     | |
|  +-----------------------------------------------------+ |
|                                                           |
|  +---------------------------------------------------+   |
|  | e.g. What credit score do I need to get approved?  |   |
|  +---------------------------------------------------+   |
+----------------------------------------------------------+
```

**Component Specification:**

| Component | Type | Description |
|-----------|------|-----------|
| Heading | st.header | "Ask about Bank Rules" |
| Caption | st.caption | "Ask any question about loan approval rules and policies." |
| Chat History | st.chat_message | Alternating user/assistant message bubbles |
| User Messages | st.chat_message("user") | Right-aligned, user icon |
| AI Responses | st.chat_message("assistant") | Left-aligned, AI icon |
| Input Field | st.chat_input | Bottom-fixed text input with placeholder text |

---

## 5. Evaluation Result Display

The result display is consistent across Tab 1 (CSV) and Tab 2 (New Application).

### 5.1 Status Banner

| Decision | Background Colour | Text Colour | Text |
|----------|------------------|-------------|------|
| APPROVE | rgba(0,128,0,0.15) | #00c853 | Status: Approved |
| REJECT | rgba(255,0,0,0.15) | #ff1744 | Status: Rejected |
| REFER | rgba(243,156,18,0.15) | #f39c12 | Status: Refer for Manual Review |

**CSS Properties:**

| Property | Value |
|----------|-------|
| Border radius | 8px |
| Padding | 12px 20px |
| Text alignment | Center |
| Font size | 1.1rem |
| Font weight | 600 |
| Border | 1px solid (decision colour) |

### 5.2 Metrics Row

Three-column table layout with equal column widths (33%/34%/33%):

| Column | Label (grey, 0.8rem) | Value (white, 1.1rem bold) |
|--------|---------------------|---------------------------|
| Left | Risk Score | {score} pts |
| Centre | Deterministic Decision | APPROVE / REJECT / REFER |
| Right | Thresholds | >=200 Approve | 150-199 Refer | <150 Reject |

### 5.3 Score Breakdown Table

| Column | Description |
|--------|-----------|
| factor | Scoring factor name (e.g. Credit Score, Income Level) |
| condition | Applicant's value and which bracket it falls into |
| points | Points awarded for this factor |

### 5.4 LLM Explanation

| Property | Value |
|----------|-------|
| Container | st.expander (collapsible) |
| Label | "LLM Explanation" |
| Default state | Collapsed |
| Content | AI-generated analysis text |

---

## 6. UI Components Specification

### 6.1 Buttons

| Button | Style | Location | Action |
|--------|-------|----------|--------|
| Evaluate Selected | Red background, white text | Tab 1 | Evaluate selected customer from dropdown |
| Evaluate All | Outlined (border only) | Tab 1 | Evaluate all customers in CSV |
| Evaluate Application | Red background, white text | Tab 2 | Submit form and evaluate |
| Download results as CSV | Default Streamlit style | Tab 1 (after batch) | Download CSV file |
| Browse files | Default Streamlit style | Sidebar, Tab 1 | Open file picker |

### 6.2 Input Widgets

| Widget | Streamlit Component | Usage |
|--------|-------------------|-------|
| Text field | st.text_input | Full Name |
| Number field | st.number_input | Age, Income, Credit Score, etc. |
| Checkbox | st.checkbox | Has Collateral |
| Dropdown | st.selectbox | Customer selector |
| File uploader | st.file_uploader | CSV upload, PDF upload |
| Chat input | st.chat_input | Q&A question entry |

### 6.3 Display Widgets

| Widget | Streamlit Component | Usage |
|--------|-------------------|-------|
| Data table | st.dataframe | CSV preview, Score breakdown, History |
| Metric card | st.metric | Dashboard KPIs |
| Bar chart | st.bar_chart | Decision distribution, Score distribution |
| Expander | st.expander | LLM explanation (collapsible) |
| Success indicator | st.success | Sidebar system status |
| Chat message | st.chat_message | Q&A conversation |
| HTML block | st.markdown (unsafe_allow_html) | Status banner, Metrics row |

---

## 7. Colour Scheme and Visual Design

### 7.1 Theme

The application uses Streamlit's default **dark theme**.

| Element | Colour |
|---------|--------|
| Background (main) | #0e1117 |
| Background (sidebar) | #262730 |
| Text (primary) | #fafafa |
| Text (secondary/caption) | #aaaaaa |
| Accent (buttons, links) | #ff4b4b (Streamlit red) |
| Tab active underline | #ff4b4b |

### 7.2 Decision Colours

| Decision | Primary Colour | Background | Usage |
|----------|---------------|-----------|-------|
| Approve | #00c853 (green) | rgba(0,128,0,0.15) | Status banner, text |
| Reject | #ff1744 (red) | rgba(255,0,0,0.15) | Status banner, text |
| Refer | #f39c12 (orange) | rgba(243,156,18,0.15) | Status banner, text |

### 7.3 System Status Colours

| Status | Colour | Widget |
|--------|--------|--------|
| Connected / Ready | Green | st.success |
| Warning | Yellow | st.warning |
| Error / Disconnected | Red | st.error |

---

## 8. User Interaction Flows

### 8.1 Flow 1: Single Evaluation from CSV

```
User opens application
  |
  v
Tab "Evaluate from CSV" is active (default)
  |
  v
User sees default data OR uploads CSV
  |
  v
User selects customer from dropdown
  |
  v
User clicks "Evaluate Selected"
  |
  v
Loading spinner appears
  |
  v
Result appears below:
  Status Banner --> Metrics Row --> Score Breakdown --> LLM Explanation
```

### 8.2 Flow 2: Batch Evaluation

```
User uploads CSV or uses default data
  |
  v
User clicks "Evaluate All"
  |
  v
Progress indicator shows processing
  |
  v
Summary table appears with all decisions
  |
  v
"Download results as CSV" button appears
  |
  v
User clicks download --> CSV saved to local machine
```

### 8.3 Flow 3: Manual Application

```
User navigates to "New Application" tab
  |
  v
Empty form displayed with default values
  |
  v
User fills in all 9 fields
  |
  v
User clicks "Evaluate Application"
  |
  v
Result appears below the form (same format as Flow 1)
```

### 8.4 Flow 4: Q&A

```
User navigates to "Ask about Rules" tab
  |
  v
Empty chat interface with input field at bottom
  |
  v
User types question and presses Enter
  |
  v
User message appears in chat
  |
  v
AI response appears below (with loading indicator)
  |
  v
User can ask follow-up questions (chat history maintained)
```

### 8.5 Flow 5: Upload New Rules

```
User locates "Upload New Rules PDF" in sidebar
  |
  v
User drags PDF or clicks "Browse files"
  |
  v
System processes and re-indexes the PDF
  |
  v
Success message displayed
  |
  v
All subsequent evaluations and Q&A use new rules
```

---

## 9. Responsive Behaviour

### 9.1 Desktop (>1024px)

- Sidebar visible on the left (collapsible)
- Main content area uses full remaining width
- Metrics row displays 3 columns side by side
- Dashboard metrics display 4 columns in one row

### 9.2 Tablet/Small Desktop (768-1024px)

- Sidebar can be collapsed to gain space
- Tables may require horizontal scrolling
- Metrics layout may wrap to 2 columns

### 9.3 Mobile (<768px)

- Sidebar hidden by default (hamburger menu)
- All layouts stack vertically
- Tables use horizontal scrolling
- Charts resize to fit screen width

---

## 10. Accessibility Considerations

### 10.1 Current Implementation

| Feature | Status |
|---------|--------|
| Keyboard navigation | Supported (Streamlit default) |
| Screen reader support | Partial (Streamlit default) |
| Colour contrast | Decision colours meet WCAG AA standards on dark background |
| Form labels | All input fields have visible labels |
| Alt text for charts | Not implemented (Streamlit limitation) |
| Tab order | Logical (follows visual layout) |

### 10.2 Recommendations for Production

| Improvement | Description |
|-------------|-----------|
| ARIA labels | Add descriptive labels to custom HTML components |
| High contrast mode | Provide alternative colour scheme for visually impaired users |
| Font scaling | Support browser-level font size adjustments |
| Error announcements | Screen reader announcements for evaluation results |

---

## Appendix A: Screenshots

**Instructions:** Insert actual screenshots from the running application below each description.

### A.1 - Evaluate from CSV (Initial State)
*[Insert screenshot: Tab 1 showing file uploader and data preview table]*

### A.2 - Evaluate from CSV (After Evaluation)
*[Insert screenshot: Tab 1 showing status banner, metrics, score breakdown]*

### A.3 - New Application (Empty Form)
*[Insert screenshot: Tab 2 showing the input form with default values]*

### A.4 - New Application (After Evaluation)
*[Insert screenshot: Tab 2 showing form and evaluation result]*

### A.5 - Dashboard (With Data)
*[Insert screenshot: Tab 3 showing metrics, charts, and history table]*

### A.6 - Dashboard (Empty State)
*[Insert screenshot: Tab 3 showing empty state message]*

### A.7 - Ask about Rules (Conversation)
*[Insert screenshot: Tab 4 showing Q&A chat with question and answer]*

### A.8 - Sidebar (System Status)
*[Insert screenshot: Sidebar showing status indicators and PDF upload]*

---

**Document End**
