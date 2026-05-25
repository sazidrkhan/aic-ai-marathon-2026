import os
import unittest

from tests import _path  # noqa: F401
from reconmate.agent.chutes_client import ChutesClient
from reconmate.agent.handoff import (
    build_backend_reconcile_response,
    build_hermes_provider_config,
    choose_demo_model_ids,
)


class ChutesHandoffTests(unittest.TestCase):
    def test_chutes_client_reads_safe_runtime_configuration_from_environment(self):
        original = dict(os.environ)
        try:
            os.environ["CHUTES_API_KEY"] = "cpk_test_key"
            os.environ["CHUTES_MODEL"] = "default:latency"
            os.environ["CHUTES_TIMEOUT_SECONDS"] = "17"

            client = ChutesClient.from_env()

            self.assertEqual(client.api_key, "cpk_test_key")
            self.assertEqual(client.model, "default:latency")
            self.assertEqual(client.timeout_seconds, 17)
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_hermes_provider_config_uses_key_env_instead_of_secret_value(self):
        config = build_hermes_provider_config(models=["default", "default:latency", "Qwen/Qwen3-32B-TEE"])

        self.assertIn("base_url: https://llm.chutes.ai/v1", config)
        self.assertIn("key_env: CHUTES_API_KEY", config)
        self.assertIn("default:latency: {}", config)
        self.assertNotIn("cpk_", config)

    def test_backend_reconcile_response_wraps_agent_documents_for_frontend(self):
        agent_result = {
            "report_source": "chutes_hermes",
            "model": "default:latency",
            "documents": {
                "reconciliation_report": {"generated": True, "content": "report"},
                "discrepancy_summary": {"generated": True, "content": "summary"},
            },
            "agent_trace": [{"step": 1, "tool": "chutes_generate_documents", "status": "success"}],
            "fallback_used": False,
            "llm_error": None,
        }

        response = build_backend_reconcile_response("recon_demo_001", agent_result)

        self.assertEqual(response["run_id"], "recon_demo_001")
        self.assertEqual(response["documents"]["reconciliation_report"]["source"], "chutes_hermes")
        self.assertEqual(response["documents"]["discrepancy_summary"]["source"], "chutes_hermes")
        self.assertEqual(response["model"], "default:latency")
        self.assertIs(response["fallback_used"], False)

    def test_choose_demo_model_ids_keeps_routing_aliases_and_tool_capable_models(self):
        payload = {
            "data": [
                {"id": "default", "supported_features": []},
                {"id": "default:latency", "supported_features": []},
                {"id": "model/no-tools", "supported_features": ["json_mode"]},
                {"id": "model/tools", "supported_features": ["tools", "json_mode"]},
            ]
        }

        model_ids = choose_demo_model_ids(payload, limit=3)

        self.assertEqual(model_ids, ["default", "default:latency", "model/tools"])


if __name__ == "__main__":
    unittest.main()
