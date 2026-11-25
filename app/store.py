"""Almacenamiento en memoria de los items.

Limitación conocida (es un piloto): cada réplica del Deployment tiene su propio
estado, por lo que un GET puede no ver lo que otra réplica guardó con un POST.
Y al reiniciar el pod, los datos se pierden.
"""

import threading


class ItemStore:
    """Lista de items protegida con un candado para peticiones concurrentes."""

    def __init__(self) -> None:
        self._items: list[dict] = []
        self._siguiente_id = 1
        self._candado = threading.Lock()

    def add(self, name: str, description: str | None) -> dict:
        with self._candado:
            item = {"id": self._siguiente_id, "name": name, "description": description}
            self._siguiente_id += 1
            self._items.append(item)
            return dict(item)

    def list(self) -> list[dict]:
        with self._candado:
            return [dict(item) for item in self._items]

    def __len__(self) -> int:
        with self._candado:
            return len(self._items)
