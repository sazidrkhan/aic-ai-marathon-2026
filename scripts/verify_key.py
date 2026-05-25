"""Verify that your Chutes API key is accepted by the service.

HTTP 429 = Rate limited (key is valid, just throttled)
HTTP 401/403 = Key is invalid or revoked
HTTP 200 = Success (rare on rate-limited keys)

Usage:
    python scripts/verify_key.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
    print("=" * 60)
    print("Chutes API Key Verification")
    print("=" * 60)

    api_key = os.environ.get("CHUTES_API_KEY")
    if not api_key:
        print("\n[ERROR] CHUTES_API_KEY is not set.")
        print('Set it first with: $env:CHUTES_API_KEY="your-key-here"')
        return 1

    print(f"\nTesting key: {api_key[:10]}...{api_key[-4:]}")

    body = json.dumps({
        "model": "default:latency",
        "messages": [
            {"role": "user", "content": "Say hello"}
        ],
        "temperature": 0.2,
        "max_tokens": 10
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://llm.chutes.ai/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("\n[SUCCESS] Key is valid and working.")
            print(f"Response: {data['choices'][0]['message']['content']}")
            return 0
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("\n[RATE LIMITED] HTTP 429")
            print("   Your key IS valid, but Chutes is throttling requests.")
            print("   This is normal for free-tier keys during hackathon.")
            print("\n   For demo day: the server still works perfectly using")
            print("   template fallback mode with the same output structure.")
            return 0  # Not a failure - key works
        elif e.code in (401, 403):
            print(f"\n[KEY REJECTED] HTTP {e.code}")
            print("   Your API key is invalid or revoked.")
            return 1
        else:
            print(f"\n[HTTP ERROR] {e.code}: {e.reason}")
            return 1
    except Exception as e:
        print(f"\n[NETWORK ERROR] {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
