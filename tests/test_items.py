from fastapi.testclient import TestClient

from app.main import create_app
from tests.helpers import make_settings


def test_lista_vacia_al_inicio(client):
    respuesta = client.get("/api/items")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_crear_item_devuelve_201_y_lo_lista(client):
    creado = client.post("/api/items", json={"name": "Paracetamol", "description": "500 mg"})
    assert creado.status_code == 201
    assert creado.json() == {"id": 1, "name": "Paracetamol", "description": "500 mg"}

    listado = client.get("/api/items").json()
    assert listado == [creado.json()]


def test_los_ids_se_incrementan(client):
    primero = client.post("/api/items", json={"name": "A"}).json()
    segundo = client.post("/api/items", json={"name": "B"}).json()
    assert (primero["id"], segundo["id"]) == (1, 2)
    assert segundo["description"] is None


def test_nombre_vacio_es_rechazado(client):
    respuesta = client.post("/api/items", json={"name": ""})
    assert respuesta.status_code == 422


def test_nombre_solo_espacios_es_rechazado(client):
    respuesta = client.post("/api/items", json={"name": "   "})
    assert respuesta.status_code == 422


def test_falta_el_campo_name(client):
    respuesta = client.post("/api/items", json={"description": "sin nombre"})
    assert respuesta.status_code == 422


def test_descripcion_demasiado_larga_es_rechazada(client):
    respuesta = client.post("/api/items", json={"name": "X", "description": "a" * 501})
    assert respuesta.status_code == 422


def test_el_nombre_se_recorta(client):
    respuesta = client.post("/api/items", json={"name": "  Ibuprofeno  "})
    assert respuesta.json()["name"] == "Ibuprofeno"


def test_cada_replica_tiene_su_propio_estado():
    """Documenta la limitación del piloto: el estado no se comparte entre réplicas."""
    with TestClient(create_app(make_settings())) as a, TestClient(create_app(make_settings())) as b:
        a.post("/api/items", json={"name": "solo en A"})
        assert len(a.get("/api/items").json()) == 1
        assert b.get("/api/items").json() == []
