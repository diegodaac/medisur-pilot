"""Métricas Prometheus de la aplicación.

- http_requests_total{method,endpoint,status}            Counter
- http_request_duration_seconds{method,endpoint}         Histogram
- app_info{version,commit} 1                             Gauge (versión desplegada en Grafana)

`endpoint` usa la plantilla de la ruta (p. ej. /api/items), nunca la URL
literal, para no disparar la cardinalidad.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter(
    "http_requests_total",
    "Total de peticiones HTTP atendidas.",
    ["method", "endpoint", "status"],
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duración de las peticiones HTTP en segundos.",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

APP_INFO = Gauge(
    "app_info",
    "Versión y commit de la aplicación en ejecución (siempre vale 1).",
    ["version", "commit"],
)

METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST


def set_app_info(version: str, commit: str) -> None:
    """Publica la versión desplegada; limpia series previas (útil en pruebas)."""
    APP_INFO.clear()
    APP_INFO.labels(version=version, commit=commit).set(1)


def observe_request(method: str, endpoint: str, status: int, seconds: float) -> None:
    REQUESTS.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    LATENCY.labels(method=method, endpoint=endpoint).observe(seconds)


def render_metrics() -> bytes:
    return generate_latest()
