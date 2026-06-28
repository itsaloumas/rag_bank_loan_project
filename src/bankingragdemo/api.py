"""
api.py
FastAPI REST backend for the Bank Loan RAG Evaluation System.

Exposes all evaluation, Q&A, and management functionality as REST endpoints.
The Streamlit frontend (app.py) communicates with this server via HTTP.

Run with:
    python src/bankingragdemo/api.py
"""

import os
import sys
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Ensure sibling modules are importable
sys.path.insert(0, os.path.dirname(__file__))

import rag_engine


# ---------------------------------------------------------------------------
# Pydantic models for request / response validation
# ---------------------------------------------------------------------------

class ApplicantRequest(BaseModel):
    """Input schema for a single loan application."""
    name_app: str = "Unknown"
    age: int = Field(ge=18, le=100)
    income: float = Field(gt=0)
    credit_score: int = Field(ge=0, le=850)
    delinquencies: int = Field(default=0, ge=0)
    loan_amount: float = Field(gt=0)
    employment_years: float = Field(default=0, ge=0)
    account_balance: float = Field(default=0, ge=0)
    collateral: bool | None = None
    customer_id: str | None = None


class ScoreBreakdownItem(BaseModel):
    """One row in the soft-score breakdown table."""
    factor: str
    condition: str
    points: int


class EvaluationResponse(BaseModel):
    """Full evaluation result for one applicant."""
    hard_passed: bool
    hard_failures: list[str]
    soft_score: int
    soft_breakdown: list[ScoreBreakdownItem]
    decision: str
    reason: str
    llm_explanation: str


class BatchEvaluateRequest(BaseModel):
    """Request body for batch evaluation."""
    applications: list[ApplicantRequest]


class BatchEvaluationResponse(BaseModel):
    """Response body for batch evaluation."""
    results: list[EvaluationResponse]


class AskRequest(BaseModel):
    """Request body for the Q&A endpoint."""
    question: str


class AskResponse(BaseModel):
    """Response body for the Q&A endpoint."""
    answer: str


class HealthResponse(BaseModel):
    """System health status."""
    status: str
    embeddings_loaded: bool
    llm_connected: bool
    rules_db_ready: bool
    customers_db_ready: bool


# ---------------------------------------------------------------------------
# Application lifecycle -- load heavy resources on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise embeddings, LLM and vector stores before the first request."""
    # rag_engine uses relative paths (bank_data/, chroma_db_*) so we need
    # to set the working directory to the project root.
    project_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    # Load all resources
    app.state.embeddings = rag_engine.init_embeddings()
    try:
        app.state.llm = rag_engine.init_llm()
        app.state.llm.invoke("ping")
        app.state.llm_ok = True
    except Exception:
        app.state.llm = None
        app.state.llm_ok = False

    rules_vs = rag_engine.load_rules_vectorstore(app.state.embeddings)
    app.state.retriever_rules = rules_vs.as_retriever()

    customers_vs = rag_engine.load_customers_vectorstore(app.state.embeddings)
    app.state.retriever_customers = customers_vs.as_retriever()

    app.state.ready = True

    yield  # application runs here

    # Shutdown -- nothing to clean up


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bank Loan Evaluator API",
    description="REST API for RAG-powered bank loan evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow requests from the Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """Return the current status of all backend resources."""
    ready = getattr(app.state, "ready", False)
    return HealthResponse(
        status="ok" if ready else "initialising",
        embeddings_loaded=hasattr(app.state, "embeddings"),
        llm_connected=getattr(app.state, "llm_ok", False),
        rules_db_ready=hasattr(app.state, "retriever_rules"),
        customers_db_ready=hasattr(app.state, "retriever_customers"),
    )


@app.post("/api/evaluate", response_model=EvaluationResponse)
def evaluate_single(applicant: ApplicantRequest):
    """Evaluate a single loan application through the full pipeline."""
    try:
        result = rag_engine.evaluate_application(
            applicant.model_dump(),
            app.state.retriever_rules,
            app.state.retriever_customers,
            app.state.llm,
        )
        return EvaluationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/evaluate/batch", response_model=BatchEvaluationResponse)
def evaluate_batch(request: BatchEvaluateRequest):
    """Evaluate multiple loan applications sequentially."""
    results = []
    for applicant in request.applications:
        try:
            result = rag_engine.evaluate_application(
                applicant.model_dump(),
                app.state.retriever_rules,
                app.state.retriever_customers,
                app.state.llm,
            )
            results.append(EvaluationResponse(**result))
        except Exception as e:
            results.append(EvaluationResponse(
                hard_passed=False,
                hard_failures=[f"Evaluation error: {str(e)}"],
                soft_score=0,
                soft_breakdown=[],
                decision="REJECT",
                reason=f"Error: {str(e)}",
                llm_explanation="Evaluation failed due to an internal error.",
            ))
    return BatchEvaluationResponse(results=results)


@app.get("/api/applications")
def get_applications():
    """Return the default loan applications dataset as a list of records."""
    try:
        df = rag_engine.load_applications()
        # Convert numpy types to native Python for JSON serialisation
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask", response_model=AskResponse)
def ask_about_rules(request: AskRequest):
    """Answer a natural-language question about bank rules using RAG."""
    try:
        answer = rag_engine.ask_rules_question(
            request.question,
            app.state.retriever_rules,
            app.state.llm,
        )
        return AskResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rules/upload")
def upload_rules(file: UploadFile = File(...)):
    """Upload a new bank rules PDF and re-index the vector store."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        # Re-index the rules vector store
        new_vs = rag_engine.reindex_rules(app.state.embeddings, tmp_path)
        app.state.retriever_rules = new_vs.as_retriever()

        return {"message": "Rules re-indexed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000)
