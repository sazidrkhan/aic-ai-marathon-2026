"""Generate Chutes.AI provider configuration snippet.

Usage:
    PYTHONPATH=src python3 scripts/verify_chutes_config.py
"""
from __future__ import annotations

from reconmate.agent.handoff import build_chutes_provider_config


def main() -> None:
    print(
        build_chutes_provider_config(
            models=[
                "default",
                "default:latency",
                "default:throughput",
            ]
        )
    )


if __name__ == "__main__":
    main()
