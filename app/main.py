"""API piloto de MediSur (FastAPI).

Endpoints:
  GET  /health      200 si el proceso vive (livenessProbe).
  GET  /ready       200 solo si puede atender tráfico; 503 durante
                    READY_DELAY_SECONDS tras el arranque (readinessProbe).
  GET  /version     {version, commit, build_date} inyectados al construir la imagen.
  GET  /metrics     Formato Prometheus.
  GET  /api/items   Lista los items (memoria local de la réplica).
  POST /api/items   Crea un item (validación Pydantic).
"""

import logging
import time
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, StringConstraints

from app.config import Settings, load_settings
from app.metrics import METRICS_CONTENT_TYPE, observe_request, render_metrics, set_app_info
from app.store import ItemStore

logger = logging.getLogger("medisur")

NombreItem = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ItemIn(BaseModel):
    """Cuerpo aceptado en POST /api/items."""

    name: NombreItem
    description: str | None = Field(default=None, max_length=500)


class ItemOut(ItemIn):
    """Item tal como se devuelve al cliente."""

    id: int


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fábrica de la aplicación; recibe Settings para poder probarla aislada."""
    settings = settings or load_settings()
    logging.basicConfig(level=settings.log_level)
    logger.setLevel(settings.log_level)

    app = FastAPI(title=settings.service_name, version=settings.version)
    app.state.settings = settings
    app.state.store = ItemStore()
    # Instante de arranque: /ready responde 503 hasta que pase READY_DELAY_SECONDS.
    app.state.started_at = time.monotonic()
    set_app_info(settings.version, settings.git_sha)

    @app.middleware("http")
    async def medir_peticiones(request: Request, call_next):
        # El propio scrape de Prometheus no se cuenta para no inflar las gráficas.
        if request.url.path == "/metrics":
            return await call_next(request)

        inicio = time.perf_counter()
        status = 500  # si call_next lanza una excepción, se contabiliza como 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            ruta = request.scope.get("route")
            endpoint = ruta.path if ruta is not None else "unmatched"
            observe_request(request.method, endpoint, status, time.perf_counter() - inicio)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/ready")
    def ready(request: Request):
        transcurrido = time.monotonic() - request.app.state.started_at
        faltante = settings.ready_delay_seconds - transcurrido
        if faltante > 0:
            return JSONResponse(
                status_code=503,
                content={"status": "starting", "retry_in_seconds": round(faltante, 1)},
            )
        return {"status": "ready"}

    @app.get("/version")
    def version() -> dict:
        return {
            "version": settings.version,
            "commit": settings.git_sha,
            "build_date": settings.build_date,
        }

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(content=render_metrics(), media_type=METRICS_CONTENT_TYPE)

    @app.get("/api/items", response_model=list[ItemOut])
    def list_items(request: Request) -> list[dict]:
        return request.app.state.store.list()

    @app.post("/api/items", response_model=ItemOut, status_code=201)
    def create_item(item: ItemIn, request: Request) -> dict:
        creado = request.app.state.store.add(item.name, item.description)
        logger.info("item creado id=%s", creado["id"])
        return creado

    return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    cfg = load_settings()
    # 0.0.0.0 es necesario dentro del contenedor para que el Service llegue al pod.
    uvicorn.run(app, host="0.0.0.0", port=cfg.port, log_level=cfg.log_level.lower())  # NOSONAR
