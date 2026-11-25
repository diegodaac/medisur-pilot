from fastapi.testclient import TestClient

from app.main import create_app
from tests.helpers import make_settings


def test_version_devuelve_los_valores_inyectados(client):
    respuesta = client.get("/version")
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "version": "9.9.9",
        "commit": "abc1234",
        "build_date": "2026-01-01T00:00:00Z",
    }


def test_version_refleja_otro_commit():
    app = create_app(make_settings(git_sha="ffff000", version="2.0.0"))
    with TestClient(app) as c:
        cuerpo = c.get("/version").json()
    assert cuerpo["commit"] == "ffff000"
    assert cuerpo["version"] == "2.0.0"
