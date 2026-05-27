from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class GeminiClient:
    api_key: str | None = None
    model: str = "gemini-3.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "GeminiClient":
        return cls(
            api_key=os.environ.get("GEMINI_API_KEY"),
            model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
            base_url=os.environ.get(
                "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
            ),
            timeout_seconds=int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "30")),
        )

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        body = json.dumps(
            {
                "systemInstruction": {
                    "parts": [{"text": system_prompt}],
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1800,
                },
            }
        ).encode("utf-8")

        model_id = self.model
        url = f"{self.base_url.rstrip('/')}/models/{model_id}:generateContent?key={self.api_key}"
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        last_exception: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if "error" in payload:
                    raise RuntimeError(f"Gemini API error: {payload['error'].get('message', payload['error'])}")
                candidates = payload.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini API returned no candidates")
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise RuntimeError("Gemini API returned no content parts")
                return "".join(part.get("text", "") for part in parts)
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503):
                    last_exception = exc
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue
                try:
                    error_body = exc.read().decode("utf-8")
                    error_json = json.loads(error_body)
                    error_msg = error_json.get("error", {}).get("message", error_body[:200])
                    raise RuntimeError(f"Gemini API HTTP {exc.code}: {error_msg}") from exc
                except Exception:
                    raise RuntimeError(f"Gemini API HTTP {exc.code}") from exc
            except Exception as exc:
                raise

        raise RuntimeError(
            f"Gemini API returned 429/503 after 3 retries. Last error: {last_exception}"
        ) from last_exception
