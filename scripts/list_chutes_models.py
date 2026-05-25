from __future__ import annotations

import json
import urllib.request

from reconmate.agent.handoff import choose_demo_model_ids


def main() -> None:
    with urllib.request.urlopen("https://llm.chutes.ai/v1/models", timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    for model_id in choose_demo_model_ids(payload):
        print(model_id)


if __name__ == "__main__":
    main()
