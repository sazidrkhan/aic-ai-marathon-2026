"""Minimal PaddleOCR integration for ReconMate.

This module provides a thin wrapper around PaddleOCR for extracting
structured text from payment-proof images.  It is designed to run on
demand (lazy-loaded) so the heavy PaddleO/PaddleOCR imports do not
slow down FastAPI startup.

Usage
-----
    from reconmate.agent.ocr_engine import ocr_extract_text, ocr_extract_structured

    # Extract raw text
    text = ocr_extract_text("payment_proofs/invoice_001.png")

    # Extract structured fields (best-effort)
    data = ocr_extract_structured("payment_proofs/invoice_001.png")
    # {
    #   "raw_text": "...",
    #   "sender_name": "...",
    #   "amount": "...",
    #   "currency": "...",
    #   "reference": "...",
    #   "date": "...",
    # }

Note
----
For hackathon demos, if PaddleOCR is not installed the functions
return a clear stub response so the rest of the pipeline still works.

"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Lazy PaddleOCR import
# ---------------------------------------------------------------------------

_PADDLE_OCR_INSTALLED = False
try:
    from paddleocr import PaddleOCR  # type: ignore[import]

    _PADDLE_OCR_INSTALLED = True
except Exception:  # pragma: no cover
    pass


_ocr_engine: Any = None


def _get_ocr() -> Any:
    """Return a lazy-initialised PaddleOCR instance."""
    global _ocr_engine
    if _ocr_engine is None:
        if not _PADDLE_OCR_INSTALLED:
            raise RuntimeError(
                "PaddleOCR is not installed. Install it with:\n"
                "  pip install paddleocr"
            )
        # English + multilingual support; show_log=False keeps startup quiet
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr_engine


# ---------------------------------------------------------------------------
# Core OCR functions
# ---------------------------------------------------------------------------

def ocr_extract_text(image_path: str | Path) -> dict[str, Any]:
    """
    Run OCR on an image and return raw extracted text.

    Returns
    -------
    dict
        ``{"raw_text": str, "lines": list[str], "status": "success"}``
        If PaddleOCR is unavailable, returns a stub with ``"status": "stubbed"``.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(str(image_path))

    if not _PADDLE_OCR_INSTALLED:
        return {
            "raw_text": "[PaddleOCR not installed – stubbed for demo]",
            "lines": [],
            "status": "stubbed",
            "message": "Install paddleocr to enable real text extraction.",
        }

    ocr = _get_ocr()
    result = ocr.ocr(str(image_path), cls=True)
    lines: list[str] = []
    if result and result[0]:
        for line in result[0]:
            if line:
                text = line[1][0] if line[1] else ""
                lines.append(text)

    raw_text = "\n".join(lines)
    return {
        "raw_text": raw_text,
        "lines": lines,
        "status": "success",
    }


def ocr_extract_structured(image_path: str | Path) -> dict[str, Any]:
    """
    Extract structured payment-proof fields using OCR + simple regex heuristics.

    This is **best-effort**; accuracy depends on image quality and layout.
    For the hackathon demo the pipeline can fall back to pre-structured JSON if
    OCR confidence is low.
    """
    ocr_result = ocr_extract_text(image_path)
    raw_text = ocr_result["raw_text"]

    # If OCR is stubbed, return the stubbed response straight away
    if ocr_result.get("status") == "stubbed":
        return {
            "raw_text": raw_text,
            "sender_name": None,
            "amount": None,
            "currency": None,
            "reference": None,
            "date": None,
            "status": "stubbed",
            "message": ocr_result.get("message"),
        }

    # ------------------------------------------------------------------
    # Very naive heuristics; real version would use an LLM extraction step
    # ------------------------------------------------------------------
    sender_match = re.search(r"(?:From|Sender|Payee)[\s:]*(\S.{0,50})", raw_text, re.IGNORECASE)
    amount_match = re.search(r"([A-Z]{3})\s?([0-9,]+\.?\d*)", raw_text)
    date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", raw_text)
    ref_match = re.search(r"(?:Ref|Invoice|Reference)[\s:#]*(\S+)", raw_text, re.IGNORECASE)

    return {
        "raw_text": raw_text,
        "sender_name": sender_match.group(1).strip() if sender_match else None,
        "amount": amount_match.group(2).strip() if amount_match else None,
        "currency": amount_match.group(1).strip() if amount_match else None,
        "reference": ref_match.group(1).strip() if ref_match else None,
        "date": date_match.group(1).strip() if date_match else None,
        "status": "success",
    }
