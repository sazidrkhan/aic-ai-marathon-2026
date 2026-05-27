import unittest

from tests import _path  # noqa: F401

try:
    from fastapi.testclient import TestClient
    from main import app
except ModuleNotFoundError:  # pragma: no cover - lightweight local runtimes
    TestClient = None
    app = None


class FrontendAppTests(unittest.TestCase):
    @unittest.skipIf(TestClient is None, "FastAPI is not installed")
    def test_root_serves_demo_frontend(self):
        client = TestClient(app)

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("ReconMate", response.text)
        self.assertIn("/api/reconcile", response.text)


if __name__ == "__main__":
    unittest.main()
