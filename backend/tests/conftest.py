import os
import sys

import pytest
from fastapi.testclient import TestClient

# This points to: /.../crypto-streaming-dashboard/backend
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app  # noqa: E402  (import after sys.path setup)


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Shared FastAPI TestClient for API tests."""
    return TestClient(app)
