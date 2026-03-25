"""
example2.py
Standalone RAG demonstration script.

Shows the end-to-end flow of a minimal Retrieval-Augmented Generation
pipeline using ChromaDB for vector storage and the Groq API (LLaMA) as
the language model.

Steps:
    1. Define a small set of sample documents.
    2. Split them into chunks with overlap.
    3. Embed the chunks using sentence-transformers/all-MiniLM-L6-v2.
    4. Store the embeddings in a ChromaDB collection.
    5. Retrieve the most relevant chunks for a given question.
    6. Ask the LLM to answer using only the retrieved context.
"""

import os
import shutil
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables (.env file in the project root)
load_dotenv()


# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "demo_rag"


# ---------------------------------------------------------------------------
# 2. Sample source documents
# ---------------------------------------------------------------------------

raw_docs = [
    Document(
        page_content=(
            "Retrieval-Augmented Generation (RAG) is an architecture that combines "
            "information retrieval with large language models. Instead of relying only "
            "on parametric memory, the system retrieves relevant external documents "
            "and uses them as context during answer generation."
        ),
        metadata={"source": "rag_intro.txt"},
    ),
    Document(
        page_content=(
            "A vector database stores embeddings, which are dense numerical "
            "representations of text. Similarity search is typically performed with "
            "cosine similarity or dot product in the embedding space."
        ),
        metadata={"source": "vector_db.txt"},
    ),
    Document(
        page_content=(
            "The sentence-transformers/all-MiniLM-L6-v2 model produces 384-dimensional "
            "embeddings and is widely used for lightweight semantic search and RAG pipelines."
        ),
        metadata={"source": "minilm.txt"},
    ),
    Document(
        page_content=(
            "Chunking is important in RAG because long documents must be split into "
            "smaller overlapping pieces. Good chunking improves retrieval precision "
            "and reduces irrelevant context."
        ),
        metadata={"source": "chunking.txt"},
    ),
]


# ---------------------------------------------------------------------------
# 3. Clean up any previous demo data for a fresh run
# ---------------------------------------------------------------------------

if Path(CHROMA_DIR).exists():
    shutil.rmtree(CHROMA_DIR)


# ---------------------------------------------------------------------------
# 4. Split documents into overlapping chunks
# ---------------------------------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)

chunks = splitter.split_documents(raw_docs)

print(f"Original documents: {len(raw_docs)}")
print(f"Chunks created: {len(chunks)}")


# ---------------------------------------------------------------------------
# 5. Initialise the embedding model
# ---------------------------------------------------------------------------

embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"

embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model_name,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


# ---------------------------------------------------------------------------
# 6. Create the vector store and retriever
# ---------------------------------------------------------------------------

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_DIR,
    collection_name=COLLECTION_NAME,
)

# Retrieve the 3 most similar chunks for each query
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)


# ---------------------------------------------------------------------------
# 7. Initialise the LLM via Groq API
# ---------------------------------------------------------------------------

llm = ChatOpenAI(
    api_key=os.getenv("GROQ_KEY"),
    base_url=os.getenv("GROQ_ENDPOINT"),
    model=os.getenv("GROQ_MODEL"),
    temperature=0,
)


# ---------------------------------------------------------------------------
# 8. Define the prompt template
# ---------------------------------------------------------------------------

prompt = ChatPromptTemplate.from_template(
    """You are a precise assistant.
Answer the question using ONLY the provided context.
If the answer is not in the context, say clearly: "I do not know based on the provided context."

Context:
{context}

Question:
{question}
"""
)


# ---------------------------------------------------------------------------
# 9. Helper: format retrieved documents for the prompt
# ---------------------------------------------------------------------------

def format_docs(docs: list[Document]) -> str:
    """Join retrieved documents into a numbered, labelled string."""
    formatted_parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        formatted_parts.append(
            f"[Document {i} | source={source}]\n{doc.page_content}"
        )
    return "\n\n".join(formatted_parts)


# ---------------------------------------------------------------------------
# 10. Run a sample question through the full RAG pipeline
# ---------------------------------------------------------------------------

question = "Why is chunking important in a RAG pipeline?"

# Retrieve the most relevant chunks
retrieved_docs = retriever.invoke(question)
context_text = format_docs(retrieved_docs)

# Fill the prompt template and invoke the LLM
final_prompt = prompt.invoke({
    "context": context_text,
    "question": question,
})

response = llm.invoke(final_prompt)

# Print the results
print("\n" + "=" * 80)
print("QUESTION:")
print(question)

print("\n" + "=" * 80)
print("RETRIEVED DOCUMENTS:")
for idx, doc in enumerate(retrieved_docs, start=1):
    print(f"\n--- Retrieved Doc {idx} ---")
    print(f"Source: {doc.metadata.get('source', 'unknown')}")
    print(doc.page_content)

print("\n" + "=" * 80)
print("FINAL ANSWER:")
print(response.content)
print("=" * 80)
