from prometheus_client import REGISTRY


def _contador(metodo: str, endpoint: str, status: str) -> float:
    valor = REGISTRY.get_sample_value(
        "http_requests_total", {"method": metodo, "endpoint": endpoint, "status": status}
    )
    return valor or 0.0


def test_metrics_expone_formato_prometheus(client):
    respuesta = client.get("/metrics")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/plain")
    cuerpo = respuesta.text
    assert "http_requests_total" in cuerpo
    assert "http_request_duration_seconds" in cuerpo


def test_app_info_publica_version_y_commit(client):
    cuerpo = client.get("/metrics").text
    assert 'app_info{commit="abc1234",version="9.9.9"} 1.0' in cuerpo


def test_contador_aumenta_con_cada_peticion(client):
    antes = _contador("GET", "/health", "200")
    client.get("/health")
    client.get("/health")
    assert _contador("GET", "/health", "200") == antes + 2


def test_usa_la_plantilla_de_la_ruta_y_el_codigo_de_estado(client):
    antes = _contador("POST", "/api/items", "422")
    client.post("/api/items", json={"name": ""})
    assert _contador("POST", "/api/items", "422") == antes + 1


def test_rutas_inexistentes_se_agrupan_como_unmatched(client):
    antes = _contador("GET", "unmatched", "404")
    client.get("/no-existe-1")
    client.get("/no-existe-2")
    assert _contador("GET", "unmatched", "404") == antes + 2


def test_el_histograma_registra_la_duracion(client):
    cuenta_antes = REGISTRY.get_sample_value(
        "http_request_duration_seconds_count", {"method": "GET", "endpoint": "/version"}
    ) or 0.0
    client.get("/version")
    cuenta_despues = REGISTRY.get_sample_value(
        "http_request_duration_seconds_count", {"method": "GET", "endpoint": "/version"}
    )
    assert cuenta_despues == cuenta_antes + 1


def test_el_scrape_de_metrics_no_se_cuenta_a_si_mismo(client):
    antes = _contador("GET", "/metrics", "200")
    client.get("/metrics")
    assert _contador("GET", "/metrics", "200") == antes
