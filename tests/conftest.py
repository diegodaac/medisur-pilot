import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.helpers import make_settings


@pytest.fixture
def client():
    with TestClient(create_app(make_settings())) as c:
        yield c
