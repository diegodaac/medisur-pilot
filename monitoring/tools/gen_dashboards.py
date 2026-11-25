#!/usr/bin/env python3
"""Genera los tableros de Grafana como JSON (monitoring/grafana/dashboards/).

Los JSON se versionan; este script existe para poder regenerarlos y revisar las
consultas PromQL en un solo lugar. Uso:

    python3 monitoring/tools/gen_dashboards.py
"""

import json
from pathlib import Path

SALIDA = Path(__file__).resolve().parent.parent / "grafana" / "dashboards"
DS = {"type": "prometheus", "uid": "prometheus"}


def target(expr: str, leyenda: str, ref: str, instant: bool = False) -> dict:
    t = {"datasource": DS, "expr": expr, "legendFormat": leyenda, "refId": ref}
    if instant:
        t["instant"] = True
        t["range"] = False
    return t


def serie_tiempo(pid, titulo, x, y, w, h, targets, unidad="short", minimo=None, maximo=None):
    defaults = {"unit": unidad, "custom": {"lineWidth": 2, "fillOpacity": 10}}
    if minimo is not None:
        defaults["min"] = minimo
    if maximo is not None:
        defaults["max"] = maximo
    return {
        "id": pid,
        "type": "timeseries",
        "title": titulo,
        "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi"},
        },
        "targets": targets,
    }


def stat(pid, titulo, x, y, w, h, targets, unidad="short", texto="auto", mapeos=None, umbrales=None, color_fondo=False):
    defaults = {"unit": unidad}
    if mapeos:
        defaults["mappings"] = mapeos
    defaults["thresholds"] = umbrales or {
        "mode": "absolute",
        "steps": [{"color": "green", "value": None}],
    }
    return {
        "id": pid,
        "type": "stat",
        "title": titulo,
        "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": texto,
            "colorMode": "background" if color_fondo else "value",
            "graphMode": "none",
            "justifyMode": "center",
        },
        "targets": targets,
    }


def tablero(uid, titulo, paneles, etiquetas):
    return {
        "uid": uid,
        "title": titulo,
        "tags": etiquetas,
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "10s",
        "time": {"from": "now-30m", "to": "now"},
        "editable": True,
        "panels": paneles,
    }


# --------------------------------------------------------------------------
# Tablero 1: Infraestructura (las dos VMs lado a lado: una serie por VM)
# --------------------------------------------------------------------------
NIC = 'device!~"lo|docker.*|veth.*|br-.*|cali.*|vxlan.*|flannel.*"'
FS = 'mountpoint="/",fstype!~"tmpfs|overlay"'

MAPEO_UPDOWN = [
    {"type": "value", "options": {"1": {"text": "ACTIVO", "color": "green"}, "0": {"text": "CAÍDO", "color": "red"}}}
]
UMBRAL_UPDOWN = {"mode": "absolute", "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]}

infra = tablero(
    "medisur-infra",
    "MediSur · Infraestructura",
    [
        serie_tiempo(
            1, "CPU en uso (%)", 0, 0, 12, 8,
            [target('100 - avg by (vm) (rate(node_cpu_seconds_total{mode="idle",job=~"node-.*"}[2m])) * 100', "{{vm}}", "A")],
            unidad="percent", minimo=0, maximo=100,
        ),
        serie_tiempo(
            2, "Memoria disponible (%)", 12, 0, 12, 8,
            [target('node_memory_MemAvailable_bytes{job=~"node-.*"} / node_memory_MemTotal_bytes{job=~"node-.*"} * 100', "{{vm}}", "A")],
            unidad="percent", minimo=0, maximo=100,
        ),
        serie_tiempo(
            3, "Disco usado en / (%)", 0, 8, 12, 8,
            [target(f'100 - (node_filesystem_avail_bytes{{job=~"node-.*",{FS}}} / node_filesystem_size_bytes{{job=~"node-.*",{FS}}} * 100)', "{{vm}}", "A")],
            unidad="percent", minimo=0, maximo=100,
        ),
        serie_tiempo(
            4, "Red (bytes/s): recibido y enviado", 12, 8, 12, 8,
            [
                target(f'sum by (vm) (rate(node_network_receive_bytes_total{{job=~"node-.*",{NIC}}}[2m]))', "{{vm}} ↓ recibido", "A"),
                target(f'sum by (vm) (rate(node_network_transmit_bytes_total{{job=~"node-.*",{NIC}}}[2m]))', "{{vm}} ↑ enviado", "B"),
            ],
            unidad="Bps",
        ),
        stat(
            5, "Estado de servicios", 0, 16, 16, 6,
            [target("probe_success{job=\"blackbox-servicios\"}", "{{service}}", "A", instant=True)],
            texto="value_and_name", mapeos=MAPEO_UPDOWN, umbrales=UMBRAL_UPDOWN, color_fondo=True,
        ),
        stat(
            6, "Tiempo encendido", 16, 16, 8, 6,
            [target('node_time_seconds{job=~"node-.*"} - node_boot_time_seconds{job=~"node-.*"}', "{{vm}}", "A", instant=True)],
            unidad="s", texto="value_and_name",
        ),
        serie_tiempo(
            7, "Servicio jenkins.service (systemd, VM-TOOLS)", 0, 22, 12, 6,
            [target('node_systemd_unit_state{job="node-tools",name="jenkins.service",state="active"}', "jenkins.service activo", "A")],
            minimo=0, maximo=1,
        ),
        serie_tiempo(
            8, "Destinos de Prometheus (up)", 12, 22, 12, 6,
            [target("up", "{{job}} · {{instance}}", "A")],
            minimo=0, maximo=1,
        ),
    ],
    ["medisur", "infraestructura"],
)

# --------------------------------------------------------------------------
# Tablero 2: Aplicación
# --------------------------------------------------------------------------
APP = 'job="medisur-pods"'
SIN_READY = 'endpoint!="/ready"'  # /ready devuelve 503 a propósito durante el retardo de arranque
POD_CONT = 'namespace="medisur",container!="",container!="POD"'

app = tablero(
    "medisur-app",
    "MediSur · Aplicación",
    [
        stat(
            1, "Versión desplegada", 0, 0, 8, 4,
            [target(f"max by (version, commit) (app_info{{{APP}}})", "{{version}} · {{commit}}", "A", instant=True)],
            texto="name",
        ),
        stat(
            2, "Réplicas listas / deseadas", 8, 0, 8, 4,
            [
                target('kube_deployment_status_replicas_available{namespace="medisur",deployment="medisur-api"}', "listas", "A", instant=True),
                target('kube_deployment_spec_replicas{namespace="medisur",deployment="medisur-api"}', "deseadas", "B", instant=True),
            ],
            texto="value_and_name",
        ),
        stat(
            3, "Tasa de errores 5xx (5 min)", 16, 0, 8, 4,
            [target(
                f'sum(rate(http_requests_total{{{APP},status=~"5..",{SIN_READY}}}[5m])) / sum(rate(http_requests_total{{{APP},{SIN_READY}}}[5m])) * 100 or vector(0)',
                "5xx", "A", instant=True,
            )],
            unidad="percent",
            umbrales={"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 1}, {"color": "red", "value": 5}]},
            color_fondo=True,
        ),
        serie_tiempo(
            4, "Peticiones por segundo", 0, 4, 12, 8,
            [target(f"sum by (endpoint) (rate(http_requests_total{{{APP}}}[1m]))", "{{endpoint}}", "A")],
            unidad="reqps",
        ),
        serie_tiempo(
            5, "Latencia p95", 12, 4, 12, 8,
            [target(f"histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{{{APP}}}[5m])))", "p95", "A")],
            unidad="s",
        ),
        serie_tiempo(
            6, "CPU por pod (cores)", 0, 12, 12, 8,
            [target(f'sum by (pod) (rate(container_cpu_usage_seconds_total{{{POD_CONT}}}[2m]))', "{{pod}}", "A")],
            unidad="short",
        ),
        serie_tiempo(
            7, "Memoria por pod", 12, 12, 12, 8,
            [target(f'sum by (pod) (container_memory_working_set_bytes{{{POD_CONT}}})', "{{pod}}", "A")],
            unidad="bytes",
        ),
        serie_tiempo(
            8, "Réplicas listas contra deseadas", 0, 20, 12, 8,
            [
                target('kube_deployment_status_replicas_available{namespace="medisur",deployment="medisur-api"}', "listas", "A"),
                target('kube_deployment_spec_replicas{namespace="medisur",deployment="medisur-api"}', "deseadas", "B"),
            ],
            minimo=0,
        ),
        serie_tiempo(
            9, "Reinicios de contenedor (acumulados)", 12, 20, 12, 8,
            [target('sum by (pod) (kube_pod_container_status_restarts_total{namespace="medisur"})', "{{pod}}", "A")],
            minimo=0,
        ),
    ],
    ["medisur", "aplicacion"],
)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, doc in (("infraestructura.json", infra), ("aplicacion.json", app)):
        (SALIDA / nombre).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("escrito", SALIDA / nombre)


if __name__ == "__main__":
    main()
