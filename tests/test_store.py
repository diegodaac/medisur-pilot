import threading

from app.store import ItemStore


def test_add_y_list():
    store = ItemStore()
    item = store.add("Gasas", None)
    assert item == {"id": 1, "name": "Gasas", "description": None}
    assert store.list() == [item]
    assert len(store) == 1


def test_list_devuelve_copias():
    store = ItemStore()
    store.add("Gasas", None)
    store.list()[0]["name"] = "modificado desde fuera"
    assert store.list()[0]["name"] == "Gasas"


def test_ids_unicos_con_hilos_concurrentes():
    store = ItemStore()

    def agregar():
        for _ in range(50):
            store.add("x", None)

    hilos = [threading.Thread(target=agregar) for _ in range(8)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    ids = [item["id"] for item in store.list()]
    assert len(ids) == 400
    assert len(set(ids)) == 400
