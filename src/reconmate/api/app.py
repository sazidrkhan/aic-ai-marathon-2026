from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.documents import generate_agent_documents
from reconmate.agent.handoff import build_backend_reconcile_response

REPO_ROOT = Path(__file__).resolve().parents[3]

if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


class ReconcilePayload(BaseModel):
    """Inbound reconciliation payload from the frontend or API clients."""

    run_id: str
    company_name: str
    base_currency: str
    matched_transactions: list[dict[str, Any]] = Field(default_factory=list)
    possible_matches: list[dict[str, Any]] = Field(default_factory=list)
    unmatched_payment_proofs: list[dict[str, Any]] = Field(default_factory=list)
    unmatched_bank_rows: list[dict[str, Any]] = Field(default_factory=list)
    fx_rates_used: list[dict[str, Any]] = Field(default_factory=list)
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)


class ReconcileResponse(BaseModel):
    """Outbound reconciliation response returned to the frontend."""

    run_id: str
    summary: dict[str, Any]
    transactions: list[dict[str, Any]]
    documents: dict[str, Any]
    agent_trace: list[dict[str, Any]]
    model: str | None
    fallback_used: bool
    llm_error: str | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chutes_client = ChutesClient.from_env()
    yield


app = FastAPI(
    title="ReconMate API",
    description="Global Treasury Reconciliation Agent for SMEs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_summary(payload: dict[str, Any]) -> dict[str, int]:
    return {
        "matched_count": len(payload.get("matched_transactions", [])),
        "possible_match_count": len(payload.get("possible_matches", [])),
        "unmatched_payment_proof_count": len(payload.get("unmatched_payment_proofs", [])),
        "unmatched_bank_row_count": len(payload.get("unmatched_bank_rows", [])),
    }


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    """Serve the demo frontend from the same origin as the API."""
    index_path = REPO_ROOT / "frontend" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path, media_type="text/html")


@app.get("/health")
def health() -> dict[str, Any]:
    """Return service status and Chutes runtime configuration."""
    client: ChutesClient = app.state.chutes_client
    return {
        "status": "ok",
        "chutes_model": client.model,
        "chutes_base_url": client.base_url,
        "api_key_configured": bool(client.api_key),
    }


@app.get("/api/models")
def list_models() -> dict[str, Any]:
    """Return the currently configured Chutes model."""
    client: ChutesClient = app.state.chutes_client
    return {
        "model": client.model,
        "base_url": client.base_url,
        "api_key_configured": bool(client.api_key),
    }


@app.post("/api/reconcile", response_model=ReconcileResponse)
def reconcile(payload: ReconcilePayload) -> dict[str, Any]:
    """Run the reconciliation document-generation workflow."""
    try:
        payload_dict = payload.model_dump()
        agent_result = generate_agent_documents(
            payload_dict,
            llm_client=app.state.chutes_client,
        )
        response = build_backend_reconcile_response(payload.run_id, agent_result)
        response["summary"] = _build_summary(payload_dict)
        response["transactions"] = payload_dict.get("matched_transactions", [])
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/ocr-extract")
async def ocr_extract(file: UploadFile = File(...)) -> dict[str, Any]:
    """Accept a payment-proof file and return demo OCR output."""
    temp_path = REPO_ROOT / "tmp" / file.filename
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        contents = await file.read()
        temp_path.write_bytes(contents)
        return {
            "filename": file.filename,
            "ocr_text": f"[Stubbed OCR output for {file.filename}]",
            "status": "stubbed",
            "message": "OCR upload accepted. Install PaddleOCR to enable real extraction.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
