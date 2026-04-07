import importlib
import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


REQUIRED_AUDIT_ENV = {
    "AZURE_OPENAI_API_KEY": "test-key",
    "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
    "AZURE_OPENAI_API_VERSION": "2024-02-01",
    "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-4o",
    "AZURE_SEARCH_ENDPOINT": "https://example.search.windows.net",
    "AZURE_SEARCH_API_KEY": "search-key",
    "AZURE_SEARCH_INDEX_NAME": "child-safety-rules",
    "AZURE_VI_ACCOUNT_ID": "account-id",
    "AZURE_VI_LOCATION": "westeurope",
    "AZURE_SUBSCRIPTION_ID": "subscription-id",
    "AZURE_RESOURCE_GROUP": "resource-group",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "",
}


class APIRouteTests(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, REQUIRED_AUDIT_ENV, clear=False)
        self.dotenv_patcher = patch("dotenv.load_dotenv", return_value=True)
        self.env_patcher.start()
        self.dotenv_patcher.start()

        sys.modules.pop("backend.src.api.server", None)
        self.server = importlib.import_module("backend.src.api.server")

        self.client_context = TestClient(self.server.app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        self.dotenv_patcher.stop()
        self.env_patcher.stop()

    def test_health_endpoint_returns_expected_payload(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "healthy", "service": "Child Safety Guardian AI"},
        )

    def test_audit_endpoint_returns_graph_output(self):
        fake_result = {
            "video_id": "vid_test1234",
            "final_status": "PASS",
            "final_report": "Mocked report",
            "compliance_results": [],
            "retrieved_policies": [],
        }

        with patch.object(self.server.compliance_graph, "invoke", return_value=fake_result):
            response = self.client.post(
                "/audit",
                json={"video_url": "https://www.youtube.com/watch?v=test"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["video_id"], "vid_test1234")
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["final_report"], "Mocked report")
        self.assertEqual(payload["compliance_results"], [])
        self.assertEqual(payload["retrieved_policies"], [])
        self.assertIn("session_id", payload)
