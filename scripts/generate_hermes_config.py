from __future__ import annotations

from reconmate.agent.handoff import build_hermes_provider_config


def main() -> None:
    print(
        build_hermes_provider_config(
            models=[
                "default",
                "default:latency",
                "default:throughput",
            ]
        )
    )


if __name__ == "__main__":
    main()
