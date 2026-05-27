"""OCR integration for ReconMate payment-proof intake.

The OCR dependencies are intentionally optional so the API can start quickly
for normal reconciliation demos. Install ``requirements-ocr.txt`` to enable
PaddleOCR image extraction and scanned-PDF page OCR.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

_PADDLE_OCR_INSTALLED = False
try:
    from paddleocr import PaddleOCR  # type: ignore[import]

    _PADDLE_OCR_INSTALLED = True
except Exception:  # pragma: no cover - optional dependency
    PaddleOCR = None  # type: ignore[assignment]


_ocr_engine: Any = None


def _get_ocr() -> Any:
    """Return a lazy-initialized PaddleOCR instance."""
    global _ocr_engine
    if _ocr_engine is None:
        if not _PADDLE_OCR_INSTALLED:
            raise RuntimeError("Install paddleocr to enable real OCR extraction.")
        errors: list[str] = []
        for kwargs in (
            {"use_angle_cls": True, "lang": "en", "show_log": False},
            {"use_angle_cls": True, "lang": "en"},
            {"lang": "en"},
            {},
        ):
            try:
                _ocr_engine = PaddleOCR(**kwargs)
                break
            except Exception as exc:
                label = ", ".join(f"{key}={value!r}" for key, value in kwargs.items()) or "no args"
                errors.append(f"{label}: {exc}")
        if _ocr_engine is None:
            raise RuntimeError(
                "PaddleOCR is installed but could not be initialized. "
                f"Last error: {errors[-1] if errors else 'unknown error'}"
            )
    return _ocr_engine


def _missing_dependency_response(message: str) -> dict[str, Any]:
    return {
        "raw_text": "",
        "lines": [],
        "status": "unavailable",
        "engine": None,
        "confidence": None,
        "message": message,
    }


def _text_response(
    lines: list[str],
    confidences: list[float],
    *,
    engine: str,
    page_count: int | None = None,
) -> dict[str, Any]:
    confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
    return {
        "raw_text": "\n".join(lines),
        "lines": lines,
        "confidences": confidences,
        "status": "success",
        "engine": engine,
        "confidence": confidence,
        "page_count": page_count,
    }


def _flatten_paddle_result(result: Any) -> tuple[list[str], list[float]]:
    """Normalize PaddleOCR output across common 2.x and 3.x result shapes."""
    lines: list[str] = []
    confidences: list[float] = []

    def visit(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, dict):
            text_values = node.get("rec_texts") or node.get("texts")
            score_values = node.get("rec_scores") or node.get("scores")
            if isinstance(text_values, list):
                for index, text in enumerate(text_values):
                    if text:
                        lines.append(str(text))
                        if isinstance(score_values, list) and index < len(score_values):
                            try:
                                confidences.append(float(score_values[index]))
                            except (TypeError, ValueError):
                                pass
                return
            text = node.get("text")
            if text:
                lines.append(str(text))
                try:
                    confidences.append(float(node.get("score")))
                except (TypeError, ValueError):
                    pass
            return
        if not isinstance(node, (list, tuple)):
            return
        if len(node) >= 2 and isinstance(node[1], (list, tuple)) and node[1]:
            text = node[1][0]
            if isinstance(text, str):
                lines.append(text)
                if len(node[1]) > 1:
                    try:
                        confidences.append(float(node[1][1]))
                    except (TypeError, ValueError):
                        pass
                return
        for child in node:
            visit(child)

    visit(result)
    return lines, confidences


def _ocr_image(image_path: Path) -> dict[str, Any]:
    if not _PADDLE_OCR_INSTALLED:
        return _missing_dependency_response(
            "Install paddleocr to enable real text extraction from images."
        )

    ocr = _get_ocr()
    try:
        result = ocr.ocr(str(image_path), cls=True)
    except TypeError:
        result = ocr.ocr(str(image_path))
    lines, confidences = _flatten_paddle_result(result)
    return _text_response(lines, confidences, engine="paddleocr")


def _extract_text_pdf(pdf_path: Path) -> dict[str, Any] | None:
    """Extract selectable text from a PDF before falling back to OCR."""
    try:
        from pypdf import PdfReader  # type: ignore[import]
    except Exception:
        return None

    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    lines = [line.strip() for text in pages for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    return _text_response(lines, [], engine="pypdf", page_count=len(reader.pages))


def _ocr_pdf_pages(pdf_path: Path) -> dict[str, Any]:
    """Render scanned PDF pages with PyMuPDF and OCR each page image."""
    if not _PADDLE_OCR_INSTALLED:
        return _missing_dependency_response(
            "Install paddleocr and pymupdf to OCR scanned PDF payment proofs."
        )
    try:
        import fitz  # type: ignore[import]
    except Exception:
        return _missing_dependency_response(
            "Install pymupdf to render scanned PDF pages for OCR."
        )

    all_lines: list[str] = []
    all_confidences: list[float] = []
    with tempfile.TemporaryDirectory(prefix="reconmate_pdf_ocr_") as tmp_dir:
        document = fitz.open(str(pdf_path))
        page_count = document.page_count
        for page_index in range(page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image_path = Path(tmp_dir) / f"page_{page_index + 1}.png"
            pixmap.save(str(image_path))
            result = _ocr_image(image_path)
            all_lines.extend(result["lines"])
            all_confidences.extend(result.get("confidences", []))

    return _text_response(
        all_lines,
        all_confidences,
        engine="paddleocr",
        page_count=page_count,
    )


def ocr_extract_text(file_path: str | Path) -> dict[str, Any]:
    """Extract raw text from a payment-proof image or PDF."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.suffix.lower() == ".pdf":
        text_result = _extract_text_pdf(path)
        if text_result:
            return text_result
        return _ocr_pdf_pages(path)

    return _ocr_image(path)


def ocr_extract_structured(file_path: str | Path) -> dict[str, Any]:
    """Extract structured payment-proof fields with OCR and regex heuristics."""
    ocr_result = ocr_extract_text(file_path)
    raw_text = ocr_result["raw_text"]

    if ocr_result.get("status") != "success":
        return {
            "raw_text": raw_text,
            "lines": ocr_result.get("lines", []),
            "sender_name": None,
            "amount": None,
            "currency": None,
            "reference": None,
            "date": None,
            "status": ocr_result.get("status"),
            "engine": ocr_result.get("engine"),
            "confidence": ocr_result.get("confidence"),
            "message": ocr_result.get("message"),
        }

    sender_match = re.search(
        r"\b(?:From|Sender|Payee|Paid by|Customer)\b[\s:,-]*(\S.{0,60})",
        raw_text,
        re.IGNORECASE,
    )
    amount_match = re.search(
        r"(?:\b(?:Amount|Total|Paid)\b)?[\s:,-]*(MYR|USD|SGD|EUR|GBP|RM)?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        raw_text,
        re.IGNORECASE,
    )
    date_match = re.search(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        raw_text,
    )
    ref_match = re.search(
        r"\b(?:Transaction ID|Receipt No\.?|Reference|Invoice|Ref)\b[\s:#,-]*(\S+)",
        raw_text,
        re.IGNORECASE,
    )

    currency = amount_match.group(1).upper() if amount_match and amount_match.group(1) else None
    if currency == "RM":
        currency = "MYR"

    return {
        "raw_text": raw_text,
        "lines": ocr_result.get("lines", []),
        "sender_name": sender_match.group(1).strip() if sender_match else None,
        "amount": amount_match.group(2).replace(",", "") if amount_match else None,
        "currency": currency,
        "reference": ref_match.group(1).strip() if ref_match else None,
        "date": date_match.group(1).strip() if date_match else None,
        "engine": ocr_result.get("engine"),
        "confidence": ocr_result.get("confidence"),
        "status": "success",
    }


def ocr_extract_json(file_path: str | Path) -> str:
    """Return structured OCR output as formatted JSON for CLI/debug usage."""
    return json.dumps(ocr_extract_structured(file_path), indent=2, ensure_ascii=False)
