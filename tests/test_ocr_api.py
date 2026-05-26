import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import _path  # noqa: F401
from reconmate.agent import ocr_engine

try:
    from fastapi.testclient import TestClient
    from main import app
except ModuleNotFoundError:  # pragma: no cover - lightweight local runtimes
    TestClient = None
    app = None


class OcrEngineTests(unittest.TestCase):
    def test_structured_parser_extracts_payment_fields_from_text_pdf_result(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            with patch.object(
                ocr_engine,
                "ocr_extract_text",
                return_value={
                    "raw_text": "\n".join(
                        [
                            "Sender: ABC Trading Ltd",
                            "Amount: USD 1,250.50",
                            "Reference: INV-9001",
                            "Date: 2026-05-26",
                        ]
                    ),
                    "lines": [],
                    "status": "success",
                    "engine": "pypdf",
                    "confidence": None,
                },
            ):
                result = ocr_engine.ocr_extract_structured(Path(tmp.name))

        self.assertEqual(result["sender_name"], "ABC Trading Ltd")
        self.assertEqual(result["amount"], "1250.50")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["reference"], "INV-9001")
        self.assertEqual(result["date"], "2026-05-26")


class OcrApiTests(unittest.TestCase):
    @unittest.skipIf(TestClient is None, "FastAPI is not installed")
    def test_ocr_endpoint_rejects_unsupported_file_type(self):
        client = TestClient(app)

        response = client.post(
            "/api/ocr-extract",
            files={"file": ("proof.txt", b"hello", "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported OCR file type", response.json()["detail"])

    @unittest.skipIf(TestClient is None, "FastAPI is not installed")
    def test_ocr_endpoint_returns_engine_output(self):
        client = TestClient(app)

        with patch(
            "reconmate.api.app.ocr_extract_structured",
            return_value={
                "raw_text": "Amount: MYR 88.00",
                "lines": ["Amount: MYR 88.00"],
                "sender_name": None,
                "amount": "88.00",
                "currency": "MYR",
                "reference": None,
                "date": None,
                "status": "success",
                "engine": "paddleocr",
                "confidence": 0.91,
                "message": None,
            },
        ):
            response = client.post(
                "/api/ocr-extract",
                files={"file": ("proof.png", b"fake image bytes", "image/png")},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["engine"], "paddleocr")
        self.assertEqual(payload["ocr_text"], "Amount: MYR 88.00")
        self.assertEqual(payload["fields"]["amount"], "88.00")
        self.assertEqual(payload["fields"]["currency"], "MYR")


if __name__ == "__main__":
    unittest.main()
