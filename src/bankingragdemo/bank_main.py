"""

file: bank_main.py
author: Dimitrios Iracleous
date: 2024-06-10
description: Example of using Retrieval-Augmented Generation (RAG) for bank loan evaluation.
This example will:

    create a set of rules for someone to get a loan, 
    give some demo data of bank customers and create a RAG to evaluate loan applications

How it works:
    Loads your loan rules from pdf file, the customers credit history from csv.
    Splits them into chunks (for easier retrieval).
    Embeds them using a Hugging Face embeddings model.
    Stores them in a Chroma vector database.
    Uses OpenAI (or any PEAI-compatible) LLM to evaluate a loan application.
    Prints test outputs.


"""

import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


from PyPDF2 import PdfReader
import os

embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model_name,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# --- 1️⃣ Load loan rules from PDF ---
def load_loan_rules_from_pdf() -> Chroma:
    pdf_path = "bank_data/bank-rules.pdf"
    persist_dir = "chroma_db_bank_rules"
    collection_name = "loan_rules"


    if not os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
        reader = PdfReader(pdf_path)
        loan_rules_text = "".join([page.extract_text() + "\n" for page in reader.pages])

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
        rule_chunks = text_splitter.split_text(loan_rules_text)

        return Chroma.from_texts(
            rule_chunks, 
            embeddings, 
            collection_name=collection_name,
            persist_directory=persist_dir
            )
    # If DB already exists, load it
    db = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir
        )
    return db

# --- 2️⃣ Load historical customer data from CSV ---
def load_customer_data_from_csv() -> Chroma:

    csv_path = "bank_data/bank_customers.csv"
    df_customers = pd.read_csv(csv_path)

    # Create textual summaries of historical loans for embeddings
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
        collection_name="customer_history"
        ,persist_directory="chroma_db_customer_history"
        )


# --- 3️⃣ Define the RAG chain ---
#llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
import llmapi as sp
llm = sp.get_groqllm()

# We will retrieve both rules and customer history separately
vectorstore_rules = load_loan_rules_from_pdf()
vectorstore_customers = load_customer_data_from_csv()
retriever_rules = vectorstore_rules.as_retriever()
retriever_customers = vectorstore_customers.as_retriever()

# --- 4️⃣ Function to evaluate new application ---
def evaluate_application_with_history(applicant):
    print(applicant)
    # Build textual description of the new application
    applicant_text = (
        f"Applicant {applicant['name_app']}, age {applicant['age']}, income {applicant['income']}, "
        f"credit_score {applicant['credit_score']}, delinquencies {applicant['delinquencies']}, "
        f"loan_amount {applicant['loan_amount']}, employment_years {applicant['employment_years']}, "
        f"account_balance {applicant['account_balance']}, collateral {applicant.get('collateral', False)}."
    )

    # Retrieve top rules
    rules_docs = retriever_rules.invoke(applicant_text)
    # Retrieve historical loans for same or similar customer
    history_docs = retriever_customers.invoke(applicant_text)

    # Combine retrieved info into a single prompt
    combined_context = "\n".join([doc.page_content for doc in rules_docs + history_docs])
    prompt = f"""
    You are a bank loan evaluator AI. Evaluate the following loan application using the retrieved rules 
    and historical customer data. Provide a clear decision (APPROVE / REFER_FOR_MANUAL_REVIEW / REJECT) 
    and briefly explain why.

    New Application:
    {applicant_text}

    Context (rules + historical data):
    {combined_context}
    """

    # Run LLM
    return llm.invoke(prompt)  # for LangChain ChatOpenAI, can also use qa_chain.run(prompt)


# --- 5️⃣ Test with applicants from CSV ---

csv_path_applications = "bank_data/loan_applications.csv"
df_applications = pd.read_csv(csv_path_applications)

csv_path = "bank_data/bank_customers.csv"
df_customers = pd.read_csv(csv_path)

test_apps = df_applications.head(5).to_dict(orient='records')  # new applications same people

df_applications_full = df_applications.merge(
    df_customers,
    on="customer_id",         # or on="name" if ID is missing
    how="left",      # keep applications even if some customer fields are missing
    suffixes=("_app", "_cust")
)


# for idx,app in df_applications_full.iterrows():
for app in df_applications_full.to_dict(orient="records"):
    print("\nEvaluating application for:", app['customer_id'])
    print("--------------------------")
    decision = evaluate_application_with_history(app)
    print(f"\n--- Decision for {app['name_app']} ---")
    print(decision)
