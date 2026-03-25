"""
rag_engine.py
Reusable RAG backend for bank loan evaluation.
Provides functions to initialise embeddings, vector stores and the LLM,
and exposes evaluate_application() and ask_rules_question() for the
Streamlit UI (app.py) and any other consumer.
"""

import os
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from PyPDF2 import PdfReader
import llmapi
import rules_engine


# ---------------------------------------------------------------------------
# Initialisation helpers
# ---------------------------------------------------------------------------

def init_embeddings():
    """Create a HuggingFace embedding model (all-MiniLM-L6-v2).
    This model produces 384-dimensional vectors and runs on CPU."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def init_llm():
    """Return a Groq-backed LLM instance ready for LangChain usage."""
    return llmapi.get_groqllm()


# ---------------------------------------------------------------------------
# Vector store loaders
# ---------------------------------------------------------------------------

def load_rules_vectorstore(embeddings, pdf_path=None):
    """Load (or create) the ChromaDB vector store that holds the
    bank loan rules extracted from the PDF.

    Args:
        embeddings: HuggingFaceEmbeddings instance.
        pdf_path:   Optional path to a custom rules PDF.
                    Defaults to bank_data/bank-rules.pdf.

    Returns:
        Chroma vector store containing the rule chunks.
    """
    if pdf_path is None:
        pdf_path = "bank_data/bank-rules.pdf"
    persist_dir = "chroma_db_bank_rules"
    collection_name = "loan_rules"

    # Build the vector store only if one does not already exist on disk
    if not os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
        reader = PdfReader(pdf_path)
        loan_rules_text = "".join(
            [page.extract_text() + "\n" for page in reader.pages]
        )
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300, chunk_overlap=20
        )
        rule_chunks = text_splitter.split_text(loan_rules_text)
        return Chroma.from_texts(
            rule_chunks,
            embeddings,
            collection_name=collection_name,
            persist_directory=persist_dir,
        )

    # Vector store already exists on disk -- load it
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )


def reindex_rules(embeddings, pdf_path):
    """Delete the existing rules vector store and rebuild it from a new PDF.
    Used when the bank uploads an updated rules document via the UI."""
    import shutil

    persist_dir = "chroma_db_bank_rules"
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    reader = PdfReader(pdf_path)
    loan_rules_text = "".join(
        [page.extract_text() + "\n" for page in reader.pages]
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=20
    )
    rule_chunks = text_splitter.split_text(loan_rules_text)
    return Chroma.from_texts(
        rule_chunks,
        embeddings,
        collection_name="loan_rules",
        persist_directory=persist_dir,
    )


def load_customers_vectorstore(embeddings):
    """Load historical customer data from CSV, convert each row into a
    textual summary, embed the summaries and store them in ChromaDB."""
    csv_path = "bank_data/bank_customers.csv"
    df_customers = pd.read_csv(csv_path)

    def summarize_customer_loan(row):
        """Create a plain-text summary of one customer record."""
        return (
            f"Customer {row['name']}, age {row['age']}, income {row['income']}, "
            f"credit_score {row['credit_score']}, delinquencies {row['delinquencies']}, "
            f"loan_amount {row['loan_amount']}, loan_outcome {row['loan_outcome']}, "
            f"employment_years {row['employment_years']}, account_balance {row['account_balance']}."
        )

    historical_texts = df_customers.apply(summarize_customer_loan, axis=1).tolist()
    return Chroma.from_texts(
        historical_texts,
        embeddings,
        collection_name="customer_history",
        persist_directory="chroma_db_customer_history",
    )


# ---------------------------------------------------------------------------
# Application data helpers
# ---------------------------------------------------------------------------

def load_applications():
    """Load loan applications and merge them with customer details.
    Returns a single DataFrame with all fields needed for evaluation."""
    df_applications = pd.read_csv("bank_data/loan_applications.csv")
    df_customers = pd.read_csv("bank_data/bank_customers.csv")
    return df_applications.merge(
        df_customers,
        on="customer_id",
        how="left",
        suffixes=("_app", "_cust"),
    )


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

def evaluate_application(applicant, retriever_rules, retriever_customers, llm):
    """Run the full evaluation pipeline for one applicant.

    Pipeline steps:
        1. Deterministic evaluation (hard rules then soft scoring).
        2. If hard rules fail the application is rejected immediately.
        3. Otherwise, relevant rules and historical records are retrieved
           and the LLM provides a reasoned decision.

    Args:
        applicant:           dict with applicant fields.
        retriever_rules:     LangChain retriever for the rules vector store.
        retriever_customers: LangChain retriever for the customer history store.
        llm:                 ChatOpenAI (Groq) instance.

    Returns:
        dict containing hard/soft results, decision and LLM explanation.
    """

    # Step 1 -- deterministic checks (hard rules + soft score)
    det_result = rules_engine.full_evaluation(applicant)

    # Step 2 -- if hard rules failed, skip the LLM call
    if not det_result["hard_passed"]:
        det_result["llm_explanation"] = (
            "Application automatically rejected due to hard rule violations. "
            "No LLM analysis performed."
        )
        return det_result

    # Step 3 -- build a textual description of the applicant
    applicant_text = (
        f"Applicant {applicant.get('name_app', applicant.get('name', 'Unknown'))}, "
        f"age {applicant['age']}, income {applicant['income']}, "
        f"credit_score {applicant['credit_score']}, delinquencies {applicant['delinquencies']}, "
        f"loan_amount {applicant['loan_amount']}, employment_years {applicant['employment_years']}, "
        f"account_balance {applicant['account_balance']}, collateral {applicant.get('collateral', False)}."
    )

    # Retrieve the most relevant rule chunks and historical customer records
    rules_docs = retriever_rules.invoke(applicant_text)
    history_docs = retriever_customers.invoke(applicant_text)

    # Combine all retrieved context into one block
    combined_context = "\n".join(
        [doc.page_content for doc in rules_docs + history_docs]
    )

    # Build the prompt for the LLM
    prompt = f"""You are a bank loan evaluator AI. Evaluate the following loan application using the retrieved rules
and historical customer data. Provide a clear decision (APPROVE / REFER_FOR_MANUAL_REVIEW / REJECT)
and briefly explain why.

The deterministic scoring system has already calculated a score of {det_result['soft_score']} points
with decision: {det_result['decision']}.

New Application:
{applicant_text}

Context (rules + historical data):
{combined_context}
"""

    # Step 4 -- invoke the LLM and attach its response
    try:
        response = llm.invoke(prompt)
        det_result["llm_explanation"] = response.content
    except Exception as e:
        det_result["llm_explanation"] = f"LLM analysis unavailable: {str(e)}"

    return det_result


def ask_rules_question(question, retriever_rules, llm):
    """Answer a natural-language question about the bank rules using RAG.

    Retrieves the most relevant chunks from the rules vector store and
    asks the LLM to formulate a concise answer based on that context.
    """
    docs = retriever_rules.invoke(question)
    context = "\n".join([doc.page_content for doc in docs])
    prompt = f"""You are a helpful banking assistant. Answer the following question about loan approval rules
based on the provided context. Be concise and accurate.

Question: {question}

Context:
{context}
"""
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"
