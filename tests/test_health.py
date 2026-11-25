import time

from fastapi.testclient import TestClient

from app.main import create_app
from tests.helpers import make_settings


def test_health_responde_200(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_ready_devuelve_503_durante_el_retardo():
    app = create_app(make_settings(ready_delay_seconds=60))
    with TestClient(app) as c:
        respuesta = c.get("/ready")
    assert respuesta.status_code == 503
    assert respuesta.json()["status"] == "starting"
    assert respuesta.json()["retry_in_seconds"] > 0


def test_ready_devuelve_200_sin_retardo(client):
    respuesta = client.get("/ready")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ready"}


def test_ready_pasa_a_200_cuando_vence_el_retardo():
    app = create_app(make_settings(ready_delay_seconds=30))
    with TestClient(app) as c:
        assert c.get("/ready").status_code == 503
        # Simula que el pod arrancó hace 31 s.
        app.state.started_at = time.monotonic() - 31
        assert c.get("/ready").status_code == 200
