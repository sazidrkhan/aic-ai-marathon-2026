from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class ChutesClient:
    api_key: str | None = None
    model: str = "default:latency"
    base_url: str = "https://llm.chutes.ai/v1"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "ChutesClient":
        return cls(
            api_key=os.environ.get("CHUTES_API_KEY"),
            model=os.environ.get("CHUTES_MODEL", "default:latency"),
            base_url=os.environ.get("CHUTES_BASE_URL", "https://llm.chutes.ai/v1"),
            timeout_seconds=int(os.environ.get("CHUTES_TIMEOUT_SECONDS", "30")),
        )

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("CHUTES_API_KEY is not configured")

        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1800,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
            },
            method="POST",
        )

        # Retry with basic exponential backoff for 429 rate limits
        last_exception: Exception | None = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                return payload["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    last_exception = exc
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue
                raise
            except Exception as exc:
                raise

        raise RuntimeError(
            f"Chutes API returned 429 Too Many Requests after 3 retries. "
            f"Last error: {last_exception}"
        ) from last_exception
