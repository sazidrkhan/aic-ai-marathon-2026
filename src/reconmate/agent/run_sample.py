from __future__ import annotations

import argparse
import json
from pathlib import Path

from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.documents import generate_agent_documents


class DisabledClient:
    model = "disabled"

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("LLM disabled for local fallback demonstration")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ReconMate agent documents from a sample payload.")
    parser.add_argument("payload", type=Path, help="Path to reconciliation payload JSON")
    parser.add_argument(
        "--use-chutes",
        action="store_true",
        help="Call Chutes using CHUTES_API_KEY. Without this flag, template fallback is demonstrated.",
    )
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    client = ChutesClient.from_env() if args.use_chutes else DisabledClient()
    result = generate_agent_documents(payload, llm_client=client)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
