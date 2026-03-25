"""
bank_main.py
Author: Dimitrios Iracleous
Date: 2024-06-10

Standalone script demonstrating Retrieval-Augmented Generation (RAG) for
bank loan evaluation.

Workflow:
    1. Load loan approval rules from a PDF and embed them into a vector store.
    2. Load historical customer data from a CSV and embed it likewise.
    3. For each new loan application, retrieve the most relevant rules and
       historical records, then ask the LLM to produce a decision.

This file is kept for reference and manual testing.  The Streamlit UI
(app.py) uses rag_engine.py which wraps the same logic in reusable functions.
"""

import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from PyPDF2 import PdfReader
import os

# -- Embedding model setup --
# all-MiniLM-L6-v2 produces 384-dimensional vectors suitable for semantic search
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model_name,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


# -- Step 1: Load loan rules from PDF --
def load_loan_rules_from_pdf() -> Chroma:
    """Read the bank-rules PDF, split it into chunks and store the
    embeddings in a ChromaDB collection.  If the database already
    exists on disk it is loaded directly to avoid re-processing."""

    pdf_path = "bank_data/bank-rules.pdf"
    persist_dir = "chroma_db_bank_rules"
    collection_name = "loan_rules"

    # Only create the vector store if it does not already exist
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

    # Database already exists -- load it
    db = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    return db


# -- Step 2: Load historical customer data from CSV --
def load_customer_data_from_csv() -> Chroma:
    """Convert each row of the customer CSV into a textual summary,
    embed the summaries and store them in a ChromaDB collection."""

    csv_path = "bank_data/bank_customers.csv"
    df_customers = pd.read_csv(csv_path)

    def summarize_customer_loan(row):
        """Return a plain-text summary of one customer record."""
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


# -- Step 3: Initialise LLM and vector stores --
import llmapi as sp

llm = sp.get_groqllm()

vectorstore_rules = load_loan_rules_from_pdf()
vectorstore_customers = load_customer_data_from_csv()
retriever_rules = vectorstore_rules.as_retriever()
retriever_customers = vectorstore_customers.as_retriever()


# -- Step 4: Evaluate a single loan application --
def evaluate_application_with_history(applicant):
    """Retrieve relevant rules and historical records, build a prompt
    and ask the LLM for a loan decision with reasoning."""

    print(applicant)

    # Build a textual description of the applicant
    applicant_text = (
        f"Applicant {applicant['name_app']}, age {applicant['age']}, income {applicant['income']}, "
        f"credit_score {applicant['credit_score']}, delinquencies {applicant['delinquencies']}, "
        f"loan_amount {applicant['loan_amount']}, employment_years {applicant['employment_years']}, "
        f"account_balance {applicant['account_balance']}, collateral {applicant.get('collateral', False)}."
    )

    # Retrieve the most relevant rule chunks
    rules_docs = retriever_rules.invoke(applicant_text)
    # Retrieve historical customer records that are most similar
    history_docs = retriever_customers.invoke(applicant_text)

    # Combine retrieved context into one prompt
    combined_context = "\n".join(
        [doc.page_content for doc in rules_docs + history_docs]
    )
    prompt = f"""
    You are a bank loan evaluator AI. Evaluate the following loan application using the retrieved rules
    and historical customer data. Provide a clear decision (APPROVE / REFER_FOR_MANUAL_REVIEW / REJECT)
    and briefly explain why.

    New Application:
    {applicant_text}

    Context (rules + historical data):
    {combined_context}
    """

    # Send the prompt to the LLM and return its response
    return llm.invoke(prompt)


# -- Step 5: Run evaluation on all applications --
csv_path_applications = "bank_data/loan_applications.csv"
df_applications = pd.read_csv(csv_path_applications)

csv_path = "bank_data/bank_customers.csv"
df_customers = pd.read_csv(csv_path)

# Merge applications with customer details for a complete picture
df_applications_full = df_applications.merge(
    df_customers,
    on="customer_id",
    how="left",
    suffixes=("_app", "_cust"),
)

# Iterate over every application and print the LLM decision
for app in df_applications_full.to_dict(orient="records"):
    print("\nEvaluating application for:", app["customer_id"])
    print("--------------------------")
    decision = evaluate_application_with_history(app)
    print(f"\n--- Decision for {app['name_app']} ---")
    print(decision)
