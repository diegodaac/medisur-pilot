import pytest

from app.config import load_settings

VARIABLES = [
    "PORT",
    "LOG_LEVEL",
    "READY_DELAY_SECONDS",
    "SERVICE_NAME",
    "APP_VERSION",
    "GIT_SHA",
    "BUILD_DATE",
]


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


def test_valores_por_defecto():
    cfg = load_settings()
    assert cfg.port == 8000
    assert cfg.log_level == "INFO"
    assert cfg.ready_delay_seconds == 10.0
    assert cfg.service_name == "medisur-api"
    assert (cfg.version, cfg.git_sha, cfg.build_date) == ("dev", "unknown", "unknown")


def test_lee_las_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("READY_DELAY_SECONDS", "2.5")
    monkeypatch.setenv("SERVICE_NAME", "otra-api")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("GIT_SHA", "deadbee")
    monkeypatch.setenv("BUILD_DATE", "2026-02-02T10:00:00Z")
    cfg = load_settings()
    assert cfg.port == 9000
    assert cfg.log_level == "DEBUG"
    assert cfg.ready_delay_seconds == 2.5
    assert cfg.service_name == "otra-api"
    assert cfg.version == "1.2.3"
    assert cfg.git_sha == "deadbee"
    assert cfg.build_date == "2026-02-02T10:00:00Z"


@pytest.mark.parametrize(
    ("nombre", "valor"),
    [
        ("PORT", "abc"),
        ("PORT", "0"),
        ("PORT", "70000"),
        ("READY_DELAY_SECONDS", "rápido"),
        ("READY_DELAY_SECONDS", "-1"),
        ("LOG_LEVEL", "verboso"),
    ],
)
def test_valores_invalidos_lanzan_error(monkeypatch, nombre, valor):
    monkeypatch.setenv(nombre, valor)
    with pytest.raises(ValueError):
        load_settings()
