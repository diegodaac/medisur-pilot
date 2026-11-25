"""Utilidades compartidas por las pruebas."""

from app.config import Settings


def make_settings(**cambios) -> Settings:
    """Settings de prueba; por defecto /ready responde 200 de inmediato."""
    base = {
        "port": 8000,
        "log_level": "INFO",
        "ready_delay_seconds": 0.0,
        "service_name": "medisur-api-test",
        "version": "9.9.9",
        "git_sha": "abc1234",
        "build_date": "2026-01-01T00:00:00Z",
    }
    base.update(cambios)
    return Settings(**base)
