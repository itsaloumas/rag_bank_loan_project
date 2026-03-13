import os
import shutil
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_openai import ChatOpenAI


# -----------------------------------------------------------------------------
# 1. Configuration
# -----------------------------------------------------------------------------

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "demo_rag"

# Set your API key before running:
# Windows CMD:
#   set OPENAI_API_KEY=your_key_here
# PowerShell:
#   $env:OPENAI_API_KEY="your_key_here"
# macOS/Linux:
#   export OPENAI_API_KEY=your_key_here
from dotenv import load_dotenv
import os
 
# Load environment variables from the .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "Missing OPENAI_API_KEY environment variable."
    )


# -----------------------------------------------------------------------------
# 2. Sample source documents
# -----------------------------------------------------------------------------

raw_docs = [
    Document(
        page_content=(
            "Retrieval-Augmented Generation (RAG) is an architecture that combines "
            "information retrieval with large language models. Instead of relying only "
            "on parametric memory, the system retrieves relevant external documents "
            "and uses them as context during answer generation."
        ),
        metadata={"source": "rag_intro.txt"}
    ),
    Document(
        page_content=(
            "A vector database stores embeddings, which are dense numerical "
            "representations of text. Similarity search is typically performed with "
            "cosine similarity or dot product in the embedding space."
        ),
        metadata={"source": "vector_db.txt"}
    ),
    Document(
        page_content=(
            "The sentence-transformers/all-MiniLM-L6-v2 model produces 384-dimensional "
            "embeddings and is widely used for lightweight semantic search and RAG pipelines."
        ),
        metadata={"source": "minilm.txt"}
    ),
    Document(
        page_content=(
            "Chunking is important in RAG because long documents must be split into "
            "smaller overlapping pieces. Good chunking improves retrieval precision "
            "and reduces irrelevant context."
        ),
        metadata={"source": "chunking.txt"}
    ),
]


# -----------------------------------------------------------------------------
# 3. Optional cleanup for a fresh demo run
# -----------------------------------------------------------------------------

if Path(CHROMA_DIR).exists():
    shutil.rmtree(CHROMA_DIR)


# -----------------------------------------------------------------------------
# 4. Split documents into chunks
# -----------------------------------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)

chunks = splitter.split_documents(raw_docs)

print(f"Original documents: {len(raw_docs)}")
print(f"Chunks created: {len(chunks)}")


# -----------------------------------------------------------------------------
# 5. Embedding model
# -----------------------------------------------------------------------------

embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"

embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model_name,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)


# -----------------------------------------------------------------------------
# 6. Create vector store
# -----------------------------------------------------------------------------

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_DIR,
    collection_name=COLLECTION_NAME
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)


# -----------------------------------------------------------------------------
# 7. LLM
# -----------------------------------------------------------------------------

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
    )


# -----------------------------------------------------------------------------
# 8. Prompt template
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# 9. Helper function to format retrieved docs
# -----------------------------------------------------------------------------

def format_docs(docs: list[Document]) -> str:
    formatted_parts = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        formatted_parts.append(
            f"[Document {i} | source={source}]\n{doc.page_content}"
        )
    return "\n\n".join(formatted_parts)


# -----------------------------------------------------------------------------
# 10. Ask a question
# -----------------------------------------------------------------------------

question = "Why is chunking important in a RAG pipeline?"

retrieved_docs = retriever.invoke(question)
context_text = format_docs(retrieved_docs)

final_prompt = prompt.invoke({
    "context": context_text,
    "question": question
})

response = llm.invoke(final_prompt)

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