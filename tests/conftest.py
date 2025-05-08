import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="function")
def client():
    """Provides a synchronous FastAPI TestClient.
    Lifespan events are handled by TestClient.
    """
    # TestClient itself manages the app's lifespan within its context.
    with TestClient(app) as c:
        yield c
