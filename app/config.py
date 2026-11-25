"""Configuración de la aplicación.

Toda la configuración llega por variables de entorno (nada fijo en el código).
En Kubernetes, las variables vienen del ConfigMap `medisur-api-config` y del
Secret `medisur-api-secret`; la versión/commit/fecha se inyectan al construir
la imagen (ARG -> ENV en el Dockerfile).
"""

import os
from dataclasses import dataclass

_NIVELES_LOG = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class Settings:
    """Valores de configuración ya validados."""

    port: int
    log_level: str
    ready_delay_seconds: float
    service_name: str
    version: str
    git_sha: str
    build_date: str


def _leer_float_no_negativo(nombre: str, por_defecto: str) -> float:
    crudo = os.environ.get(nombre, por_defecto)
    try:
        valor = float(crudo)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser numérico, se recibió {crudo!r}") from exc
    if valor < 0:
        raise ValueError(f"{nombre} no puede ser negativo, se recibió {valor}")
    return valor


def _leer_puerto(nombre: str, por_defecto: str) -> int:
    crudo = os.environ.get(nombre, por_defecto)
    try:
        puerto = int(crudo)
    except ValueError as exc:
        raise ValueError(f"{nombre} debe ser un entero, se recibió {crudo!r}") from exc
    if not 1 <= puerto <= 65535:
        raise ValueError(f"{nombre} fuera de rango (1-65535): {puerto}")
    return puerto


def load_settings() -> Settings:
    """Lee las variables de entorno en el momento de la llamada."""
    nivel = os.environ.get("LOG_LEVEL", "INFO").upper()
    if nivel not in _NIVELES_LOG:
        raise ValueError(f"LOG_LEVEL inválido: {nivel!r}")

    return Settings(
        port=_leer_puerto("PORT", "8000"),
        log_level=nivel,
        ready_delay_seconds=_leer_float_no_negativo("READY_DELAY_SECONDS", "10"),
        service_name=os.environ.get("SERVICE_NAME", "medisur-api"),
        version=os.environ.get("APP_VERSION", "dev"),
        git_sha=os.environ.get("GIT_SHA", "unknown"),
        build_date=os.environ.get("BUILD_DATE", "unknown"),
    )
