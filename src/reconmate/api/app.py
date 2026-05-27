from __future__ import annotations

import sys
import tempfile
from uuid import uuid4
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.documents import generate_agent_documents_with_chain
from reconmate.agent.gemini_client import GeminiClient
from reconmate.agent.handoff import build_backend_reconcile_response
from reconmate.agent.ocr_engine import ocr_extract_structured

REPO_ROOT = Path(__file__).resolve().parents[3]
MAX_OCR_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_OCR_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_OCR_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/pjpeg",
    "application/octet-stream",
}

if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))


@dataclass(frozen=True)
class AppClients:
    chutes: ChutesClient
    gemini: GeminiClient


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
    report_source: str | None = None
    summary: dict[str, Any]
    transactions: list[dict[str, Any]]
    documents: dict[str, Any]
    agent_trace: list[dict[str, Any]]
    model: str | None
    fallback_used: bool
    llm_error: str | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.clients = AppClients(
        chutes=ChutesClient.from_env(),
        gemini=GeminiClient.from_env(),
    )
    yield


app = FastAPI(
    title="ReconMate API",
    description="Global Treasury Reconciliation Agent for SMEs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=False,
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
    """Return service status and LLM runtime configuration."""
    clients: AppClients = app.state.clients
    return {
        "status": "ok",
        "chutes_model": clients.chutes.model,
        "chutes_base_url": clients.chutes.base_url,
        "chutes_api_key_configured": bool(clients.chutes.api_key),
        "gemini_model": clients.gemini.model,
        "gemini_api_key_configured": bool(clients.gemini.api_key),
    }


@app.get("/api/models")
def list_models() -> dict[str, Any]:
    """Return the currently configured LLM models."""
    clients: AppClients = app.state.clients
    return {
        "chutes": {
            "model": clients.chutes.model,
            "base_url": clients.chutes.base_url,
            "api_key_configured": bool(clients.chutes.api_key),
        },
        "gemini": {
            "model": clients.gemini.model,
            "api_key_configured": bool(clients.gemini.api_key),
        },
    }


@app.post("/api/reconcile", response_model=ReconcileResponse)
def reconcile(payload: ReconcilePayload) -> dict[str, Any]:
    """Run the reconciliation document-generation workflow with LLM fallback chain."""
    try:
        payload_dict = payload.model_dump()
        clients: AppClients = app.state.clients
        agent_result = generate_agent_documents_with_chain(
            payload_dict,
            chutes_client=clients.chutes,
            gemini_client=clients.gemini,
        )
        response = build_backend_reconcile_response(payload.run_id, agent_result)
        response["summary"] = _build_summary(payload_dict)
        response["transactions"] = payload_dict.get("matched_transactions", [])
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/ocr-extract")
async def ocr_extract(file: UploadFile = File(...)) -> dict[str, Any]:
    """Accept a payment-proof file and return OCR text plus parsed fields."""
    filename = Path(file.filename or "payment-proof").name
    suffix = Path(filename).suffix.lower()
    content_type = file.content_type or "application/octet-stream"

    if suffix not in ALLOWED_OCR_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported OCR file type. Upload PDF, PNG, JPG, or JPEG.",
        )
    if content_type not in ALLOWED_OCR_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported OCR content type. Upload PDF, PNG, JPG, or JPEG.",
        )

    temp_path: Path | None = None
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded OCR file is empty.")
        if len(contents) > MAX_OCR_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="OCR upload must be 10 MB or smaller.")

        temp_dir = Path(tempfile.gettempdir()) / "reconmate_ocr_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"{uuid4().hex}{suffix}"
        temp_path.write_bytes(contents)

        ocr_result = ocr_extract_structured(temp_path)
        return {
            "filename": filename,
            "content_type": content_type,
            "status": ocr_result.get("status"),
            "engine": ocr_result.get("engine"),
            "confidence": ocr_result.get("confidence"),
            "ocr_text": ocr_result.get("raw_text", ""),
            "lines": ocr_result.get("lines", []),
            "fields": {
                "sender_name": ocr_result.get("sender_name"),
                "amount": ocr_result.get("amount"),
                "currency": ocr_result.get("currency"),
                "reference": ocr_result.get("reference"),
                "date": ocr_result.get("date"),
            },
            "message": ocr_result.get("message"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
