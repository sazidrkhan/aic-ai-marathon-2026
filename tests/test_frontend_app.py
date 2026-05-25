import unittest

from fastapi.testclient import TestClient

from tests import _path  # noqa: F401
from main import app


class FrontendAppTests(unittest.TestCase):
    def test_root_serves_demo_frontend(self):
        client = TestClient(app)

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("ReconMate", response.text)
        self.assertIn("/api/reconcile", response.text)


if __name__ == "__main__":
    unittest.main()
