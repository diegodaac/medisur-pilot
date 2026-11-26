#!/usr/bin/env bash
# Genera tráfico realista contra la API para que los tableros de Grafana muestren
# peticiones por segundo, latencia y una pequeña tasa de errores 4xx.
# Útil antes de tomar capturas y durante la demo (paso 9: delete pod).
#
#   ./infra/generar-trafico.sh                      # 5 minutos contra la IP privada de VM-K8S
#   ./infra/generar-trafico.sh 600                  # 10 minutos
#   URL=http://158.23.21.125:30080 ./infra/generar-trafico.sh   # desde la laptop
set -uo pipefail

DURACION="${1:-300}"
URL="${URL:-http://172.16.0.4:30080}"
FIN=$(( $(date +%s) + DURACION ))
n=0

echo ">> Tráfico contra ${URL} durante ${DURACION} s (Ctrl+C para detener)"
while [ "$(date +%s)" -lt "$FIN" ]; do
  curl -s -o /dev/null "$URL/api/items"
  curl -s -o /dev/null "$URL/version"
  curl -s -o /dev/null -X POST -H "Content-Type: application/json" \
       -d "{\"name\":\"insumo-$n\",\"description\":\"lote de prueba\"}" "$URL/api/items"
  # Cada 10 vueltas, una petición inválida (422) para que la gráfica no sea plana.
  [ $(( n % 10 )) -eq 0 ] && curl -s -o /dev/null -X POST -H "Content-Type: application/json" -d '{"name":""}' "$URL/api/items"
  n=$(( n + 1 ))
  sleep 0.3
done
echo ">> Fin: ${n} vueltas"
