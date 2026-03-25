"""
rag_engine.py
Reusable RAG backend for bank loan evaluation.
Extracted from bank_main.py for use by Streamlit UI and other consumers.
"""

import os
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from PyPDF2 import PdfReader
import llmapi
import rules_engine


def init_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def init_llm():
    return llmapi.get_groqllm()


def load_rules_vectorstore(embeddings, pdf_path=None):
    if pdf_path is None:
        pdf_path = "bank_data/bank-rules.pdf"
    persist_dir = "chroma_db_bank_rules"
    collection_name = "loan_rules"

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

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )


def reindex_rules(embeddings, pdf_path):
    """Delete existing rules DB and re-create from a new PDF."""
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
    csv_path = "bank_data/bank_customers.csv"
    df_customers = pd.read_csv(csv_path)

    def summarize_customer_loan(row):
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


def load_applications():
    df_applications = pd.read_csv("bank_data/loan_applications.csv")
    df_customers = pd.read_csv("bank_data/bank_customers.csv")
    return df_applications.merge(
        df_customers,
        on="customer_id",
        how="left",
        suffixes=("_app", "_cust"),
    )


def evaluate_application(applicant, retriever_rules, retriever_customers, llm):
    """Full evaluation: hard rules -> soft score -> LLM analysis.
    Returns dict with deterministic results + LLM explanation."""

    # Step 1: Deterministic evaluation
    det_result = rules_engine.full_evaluation(applicant)

    # Step 2: If hard rules failed, skip LLM
    if not det_result["hard_passed"]:
        det_result["llm_explanation"] = (
            "Application automatically rejected due to hard rule violations. "
            "No LLM analysis performed."
        )
        return det_result

    # Step 3: LLM analysis for applications that pass hard rules
    applicant_text = (
        f"Applicant {applicant.get('name_app', applicant.get('name', 'Unknown'))}, "
        f"age {applicant['age']}, income {applicant['income']}, "
        f"credit_score {applicant['credit_score']}, delinquencies {applicant['delinquencies']}, "
        f"loan_amount {applicant['loan_amount']}, employment_years {applicant['employment_years']}, "
        f"account_balance {applicant['account_balance']}, collateral {applicant.get('collateral', False)}."
    )

    rules_docs = retriever_rules.invoke(applicant_text)
    history_docs = retriever_customers.invoke(applicant_text)

    combined_context = "\n".join(
        [doc.page_content for doc in rules_docs + history_docs]
    )
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

    try:
        response = llm.invoke(prompt)
        det_result["llm_explanation"] = response.content
    except Exception as e:
        det_result["llm_explanation"] = f"LLM analysis unavailable: {str(e)}"

    return det_result


def ask_rules_question(question, retriever_rules, llm):
    """Answer a natural language question about the bank rules using RAG."""
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
