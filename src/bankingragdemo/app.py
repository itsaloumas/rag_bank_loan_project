"""
app.py
Streamlit web interface for the Bank Loan RAG Evaluation System.

Provides four tabs:
    1. Evaluate from CSV  -- load or upload applications and evaluate them.
    2. New Application    -- manual single-applicant form.
    3. Dashboard          -- summary statistics and charts of past evaluations.
    4. Ask about Rules    -- RAG-powered Q&A chatbot for bank policies.

Run with:
    streamlit run src/bankingragdemo/app.py
"""

import sys
import os
import tempfile

# Ensure sibling modules (rag_engine, rules_engine, llmapi) are importable
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import rag_engine
import rules_engine


# ---------------------------------------------------------------------------
# Cached resource loaders (run once and persist across reruns)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading embeddings model...")
def get_embeddings():
    """Initialise the HuggingFace sentence-transformer embedding model."""
    return rag_engine.init_embeddings()


@st.cache_resource(show_spinner="Connecting to LLM...")
def get_llm():
    """Create the Groq LLM connection."""
    return rag_engine.init_llm()


@st.cache_resource(show_spinner="Loading loan rules database...")
def get_rules_retriever(_embeddings):
    """Build or load the rules vector store and return a retriever."""
    vs = rag_engine.load_rules_vectorstore(_embeddings)
    return vs.as_retriever()


@st.cache_resource(show_spinner="Loading customer history database...")
def get_customers_retriever(_embeddings):
    """Build or load the customer history vector store and return a retriever."""
    vs = rag_engine.load_customers_vectorstore(_embeddings)
    return vs.as_retriever()


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Bank Loan Evaluator", layout="wide")
st.title("Bank Loan Evaluator")
st.caption("RAG-powered loan application evaluation system")

# Session state for keeping evaluation history within the current session
if "evaluation_history" not in st.session_state:
    st.session_state.evaluation_history = []

# ---------------------------------------------------------------------------
# Environment variable validation
# ---------------------------------------------------------------------------

missing_env = []
for var in ["GROQ_KEY", "GROQ_MODEL", "GROQ_ENDPOINT"]:
    if not os.environ.get(var):
        missing_env.append(var)

if missing_env:
    st.error(f"Missing environment variables: {', '.join(missing_env)}. Check your .env file.")
    st.stop()

# ---------------------------------------------------------------------------
# Backend initialisation
# ---------------------------------------------------------------------------

try:
    embeddings = get_embeddings()
    llm = get_llm()
    retriever_rules = get_rules_retriever(embeddings)
    retriever_customers = get_customers_retriever(embeddings)
except Exception as e:
    st.error(f"Failed to initialize system: {str(e)}")
    st.stop()


# ---------------------------------------------------------------------------
# Sidebar -- system status and PDF upload
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("System Status")
    st.success("Embeddings loaded")
    st.success("LLM connected (Groq)")
    st.success("Vector databases ready")

    st.divider()

    # Allow the user to upload a new rules PDF and re-index the vector store
    st.header("Upload New Rules PDF")
    uploaded_pdf = st.file_uploader("Replace bank rules", type=["pdf"], key="pdf_upload")
    if uploaded_pdf is not None:
        if st.button("Re-index Rules"):
            with st.spinner("Re-indexing rules from uploaded PDF..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_pdf.read())
                    tmp_path = tmp.name
                try:
                    new_vs = rag_engine.reindex_rules(embeddings, tmp_path)
                    retriever_rules = new_vs.as_retriever()
                    get_rules_retriever.clear()
                    st.success("Rules re-indexed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to re-index: {str(e)}")
                finally:
                    os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Helper: render a structured decision card
# ---------------------------------------------------------------------------

def render_decision(result, name):
    """Display the evaluation result for one applicant including the
    status badge, score metrics, breakdown table and LLM explanation."""

    decision = result["decision"]

    # Hard-rule rejection -- show violations and return early
    if not result["hard_passed"]:
        st.error("**Hard Rule Violations:**")
        for f in result["hard_failures"]:
            st.markdown(f"- {f}")
        return

    # Determine colours based on decision outcome
    if decision == "APPROVE":
        badge_color, badge_bg = "#2ecc71", "rgba(46,204,113,0.15)"
        badge_text = "Approved"
    elif decision == "REJECT":
        badge_color, badge_bg = "#e74c3c", "rgba(231,76,60,0.15)"
        badge_text = "Rejected"
    else:
        badge_color, badge_bg = "#f39c12", "rgba(243,156,18,0.15)"
        badge_text = "Refer for Manual Review"

    # Status banner and score metrics rendered as HTML for precise layout
    st.markdown(
        """
        <div style="background: {bg}; border: 1px solid {color}; border-radius: 8px;
                    padding: 12px 20px; text-align: center; margin-bottom: 20px;">
            <span style="font-size: 1.1rem; font-weight: 600; color: {color};">
                Status: {text}
            </span>
        </div>
        <table style="width: 100%; margin-bottom: 10px;">
            <tr>
                <td style="text-align: center; width: 33%; padding: 10px 0;">
                    <div style="font-size: 0.8rem; color: #aaa; margin-bottom: 4px;">Risk Score</div>
                    <div style="font-size: 1.1rem; font-weight: 600;">{score} pts</div>
                </td>
                <td style="text-align: center; width: 34%; padding: 10px 0;">
                    <div style="font-size: 0.8rem; color: #aaa; margin-bottom: 4px;">Deterministic Decision</div>
                    <div style="font-size: 1.1rem; font-weight: 600;">{decision}</div>
                </td>
                <td style="text-align: center; width: 33%; padding: 10px 0;">
                    <div style="font-size: 0.8rem; color: #aaa; margin-bottom: 4px;">Thresholds</div>
                    <div style="font-size: 1.1rem; font-weight: 600;">&ge;200 Approve | 150-199 Refer | &lt;150 Reject</div>
                </td>
            </tr>
        </table>
        """.format(bg=badge_bg, color=badge_color, text=badge_text,
                   score=result["soft_score"], decision=result["decision"]),
        unsafe_allow_html=True,
    )

    # Score breakdown table
    if result["soft_breakdown"]:
        st.markdown("**Score Breakdown:**")
        df_breakdown = pd.DataFrame(result["soft_breakdown"])
        st.dataframe(df_breakdown, hide_index=True, width=700)

    # Collapsible LLM explanation
    with st.expander("LLM Analysis (RAG-powered)", expanded=False):
        st.markdown(result.get("llm_explanation", "No LLM analysis available."))

    # Record this evaluation in session history for the Dashboard tab
    st.session_state.evaluation_history.append({
        "name": name,
        "decision": decision,
        "score": result["soft_score"],
    })


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Evaluate from CSV",
    "New Application",
    "Dashboard",
    "Ask about Rules",
])

# ========================= TAB 1: CSV Applications =========================

with tab1:
    st.subheader("Loan Applications")

    # Optional CSV upload -- falls back to the default dataset
    uploaded_csv = st.file_uploader(
        "Upload custom applications CSV (optional)",
        type=["csv"],
        key="csv_upload",
    )

    if uploaded_csv is not None:
        try:
            df = pd.read_csv(uploaded_csv)
            st.info(f"Loaded {len(df)} applications from uploaded file.")
        except Exception as e:
            st.error(f"Failed to read CSV: {str(e)}")
            df = rag_engine.load_applications()
    else:
        df = rag_engine.load_applications()

    st.dataframe(df, hide_index=True, width="stretch")
    st.divider()

    # Determine which column holds the applicant name
    name_col = "name_app" if "name_app" in df.columns else "name"

    col1, col2 = st.columns(2)

    with col1:
        selected_customer = st.selectbox(
            "Select a customer to evaluate",
            options=df.index.tolist(),
            format_func=lambda idx: f"{df.loc[idx].get('customer_id', idx)} - {df.loc[idx][name_col]}",
        )

    with col2:
        evaluate_all = st.button("Evaluate All", key="eval_all")

    # Evaluate a single selected customer
    if st.button("Evaluate Selected", type="primary", key="eval_selected"):
        row = df.loc[selected_customer].to_dict()
        if "name_app" not in row and "name" in row:
            row["name_app"] = row["name"]
        with st.spinner(f"Evaluating {row.get('name_app', 'applicant')}..."):
            result = rag_engine.evaluate_application(
                row, retriever_rules, retriever_customers, llm
            )
        render_decision(result, row.get("name_app", "Unknown"))

    # Evaluate all customers in the dataset
    if evaluate_all:
        results_for_export = []
        for idx, row in df.iterrows():
            app = row.to_dict()
            if "name_app" not in app and "name" in app:
                app["name_app"] = app["name"]
            with st.spinner(f"Evaluating {app.get('name_app', 'applicant')}..."):
                result = rag_engine.evaluate_application(
                    app, retriever_rules, retriever_customers, llm
                )
            with st.expander(
                f"{app.get('customer_id', idx)} - {app.get('name_app', 'Unknown')}",
                expanded=True,
            ):
                render_decision(result, app.get("name_app", "Unknown"))

            results_for_export.append({
                "customer_id": app.get("customer_id", idx),
                "name": app.get("name_app", "Unknown"),
                "decision": result["decision"],
                "score": result["soft_score"],
                "hard_passed": result["hard_passed"],
            })

        # Allow the user to download the results as CSV
        if results_for_export:
            df_export = pd.DataFrame(results_for_export)
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="Download Results CSV",
                data=csv_data,
                file_name="evaluation_results.csv",
                mime="text/csv",
            )


# ========================= TAB 2: New Application =========================

with tab2:
    st.subheader("Submit a New Loan Application")

    with st.form("new_application"):
        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input("Full Name", placeholder="e.g. Nikos P.")
            age = st.number_input("Age", min_value=18, max_value=100, value=35)
            income = st.number_input("Annual Income", min_value=0, value=40000, step=1000)

        with col2:
            credit_score = st.number_input("Credit Score", min_value=0, max_value=850, value=650)
            delinquencies = st.number_input("Past Delinquencies", min_value=0, max_value=10, value=0)
            employment_years = st.number_input("Employment Years", min_value=0, max_value=50, value=5)

        with col3:
            loan_amount = st.number_input("Loan Amount Requested", min_value=0, value=20000, step=1000)
            account_balance = st.number_input("Account Balance", min_value=0, value=10000, step=1000)
            collateral = st.checkbox("Has Collateral")

        submitted = st.form_submit_button("Evaluate Application", type="primary")

    if submitted:
        if not name:
            st.error("Please enter the applicant's name.")
        else:
            applicant = {
                "name_app": name,
                "age": age,
                "income": income,
                "credit_score": credit_score,
                "delinquencies": delinquencies,
                "loan_amount": loan_amount,
                "employment_years": employment_years,
                "account_balance": account_balance,
                "collateral": collateral,
            }

            with st.spinner("Evaluating application..."):
                result = rag_engine.evaluate_application(
                    applicant, retriever_rules, retriever_customers, llm
                )

            render_decision(result, name)


# ========================= TAB 3: Dashboard =========================

with tab3:
    st.subheader("Evaluation Dashboard")

    history = st.session_state.evaluation_history

    if not history:
        st.info("No evaluations yet. Evaluate some applications to see stats here.")
    else:
        df_hist = pd.DataFrame(history)

        # Summary metrics
        total = len(df_hist)
        approved = len(df_hist[df_hist["decision"] == "APPROVE"])
        rejected = len(df_hist[df_hist["decision"] == "REJECT"])
        referred = len(df_hist[df_hist["decision"] == "REFER_FOR_MANUAL_REVIEW"])
        avg_score = df_hist["score"].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Evaluated", total)
        col2.metric("Approved", approved, delta=f"{approved/total*100:.0f}%")
        col3.metric("Rejected", rejected)
        col4.metric("Avg Score", f"{avg_score:.0f} pts")

        st.divider()

        # Charts side by side
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Decision Distribution**")
            decision_counts = df_hist["decision"].value_counts()
            st.bar_chart(decision_counts)

        with chart_col2:
            st.markdown("**Score Distribution**")
            st.bar_chart(df_hist.set_index("name")["score"])

        # Full history table
        st.divider()
        st.markdown("**Evaluation History**")
        st.dataframe(df_hist, hide_index=True, width="stretch")


# ========================= TAB 4: Chat about Rules =========================

with tab4:
    st.subheader("Ask about Bank Rules")
    st.caption("Ask any question about loan approval rules and policies.")

    # Maintain chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display previous messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input box
    question = st.chat_input("e.g. What credit score do I need to get approved?")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching rules..."):
                answer = rag_engine.ask_rules_question(question, retriever_rules, llm)
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
