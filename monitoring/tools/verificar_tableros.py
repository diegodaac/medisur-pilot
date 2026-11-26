#!/usr/bin/env python3
"""Ejecuta cada consulta PromQL de los tableros contra Prometheus y avisa si alguna
viene vacía (un tablero vacío no cuenta como monitoreo, según el enunciado).

Uso en VM-TOOLS:  python3 monitoring/tools/verificar_tableros.py [http://localhost:9090]
"""

import glob
import json
import os
import sys
import urllib.parse
import urllib.request

PROM = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9090"
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "grafana", "dashboards")
ETIQUETAS = ("vm", "pod", "endpoint", "service", "version", "commit", "job")
vacios = 0

for archivo in sorted(glob.glob(os.path.join(DIR, "*.json"))):
    tablero = json.load(open(archivo, encoding="utf-8"))
    print(f"== {tablero['title']}")
    for panel in tablero["panels"]:
        for target in panel["targets"]:
            url = f"{PROM}/api/v1/query?" + urllib.parse.urlencode({"query": target["expr"]})
            resultado = json.load(urllib.request.urlopen(url, timeout=10))["data"]["result"]
            partes = []
            for serie in resultado[:4]:
                nombre = "/".join(str(v) for k, v in serie["metric"].items() if k in ETIQUETAS) or target["legendFormat"]
                partes.append(f"{nombre}={round(float(serie['value'][1]), 3)}")
            estado = "OK   " if resultado else "VACÍO"
            vacios += 0 if resultado else 1
            print(f"  {estado} {panel['title'][:44]:<44} {', '.join(partes)[:90]}")

print(f"\nConsultas vacías: {vacios}")
sys.exit(1 if vacios else 0)
