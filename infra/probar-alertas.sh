#!/usr/bin/env bash
# Prueba de las tres alertas obligatorias con fallas controladas (no toca el despliegue).
# Se ejecuta desde la laptop; usa SSH solo para inyectar la falla, nunca para desplegar.
#
#   1) DiscoLleno            -> reserva un archivo temporal en VM-TOOLS hasta pasar del 80 %
#   2) PodReiniciandose      -> detiene el proceso de un pod cada vez que arranca (> 3 reinicios en 10 min)
#   3) ReplicasNoDisponibles -> ese pod nunca llega a estar listo durante más de 5 min
#
# Al terminar, borra el archivo y deja que el pod se recupere solo (ReplicaSet + kubelet).
set -uo pipefail

TOOLS="azureuser@158.23.177.202"; K8S="azureuser@158.23.21.125"
KEY_TOOLS="$HOME/.ssh/id_rsa";    KEY_K8S="$HOME/.ssh/vm-microk8s_key.pem"
RELLENO=/var/tmp/medisur-relleno-disco
CAOS_SEG="${CAOS_SEG:-450}"   # 7.5 min: 5 min de "for" + evaluación + margen

alertas() {  # alertas en estado firing según Prometheus
  ssh -o BatchMode=yes -i "$KEY_TOOLS" "$TOOLS" \
    'curl -s localhost:9090/api/v1/alerts | jq -r ".data.alerts[] | select(.state==\"firing\") | .labels.alertname" | sort -u | tr "\n" " "'
}

echo ">> [$(date +%T)] 1) Llenando disco de VM-TOOLS"
ssh -o BatchMode=yes -i "$KEY_TOOLS" "$TOOLS" "
  usado=\$(df --output=pcent / | tail -1 | tr -dc 0-9); total=\$(df --output=size -B1G / | tail -1 | tr -dc 0-9)
  gb=\$(( total * (85 - usado) / 100 )); sudo fallocate -l \${gb}G $RELLENO && df -h / | tail -1"

echo ">> [$(date +%T)] 2-3) Experimento de caos en un pod durante ${CAOS_SEG}s"
ssh -o BatchMode=yes -i "$KEY_K8S" "$K8S" "nohup bash -c '
  K=\"sudo microk8s kubectl -n medisur\"
  POD=\$(\$K get pods -l app=medisur-api -o jsonpath=\"{.items[0].metadata.name}\")
  echo \"pod objetivo: \$POD\"; FIN=\$(( \$(date +%s) + $CAOS_SEG ))
  while [ \$(date +%s) -lt \$FIN ]; do
    if [ \"\$(\$K get pod \$POD -o jsonpath={.status.containerStatuses[0].state.running.startedAt})\" != \"\" ]; then
      \$K exec \$POD -- python -c \"import os,signal; os.kill(1, signal.SIGTERM)\" >/dev/null 2>&1 && echo \"\$(date +%T) proceso detenido\"
    fi
    sleep 1
  done
  echo \"fin del caos; reinicios: \$(\$K get pod \$POD -o jsonpath={.status.containerStatuses[0].restartCount})\"
' > /tmp/caos.log 2>&1 &"

borrado=no
for i in $(seq 1 80); do        # hasta ~13 min
  sleep 10
  f=$(alertas)
  echo "   [$(date +%T)] firing: ${f:-ninguna}"
  if [ "$borrado" = no ] && echo "$f" | grep -q DiscoLleno; then
    sleep 20   # deja que Alertmanager notifique
    ssh -o BatchMode=yes -i "$KEY_TOOLS" "$TOOLS" "sudo rm -f $RELLENO && df -h / | tail -1"
    echo ">> [$(date +%T)] archivo de relleno borrado"; borrado=yes
  fi
  if echo "$f" | grep -q PodReiniciandose && echo "$f" | grep -q ReplicasNoDisponibles && [ "$borrado" = yes ]; then
    echo ">> [$(date +%T)] Las tres alertas dispararon."; break
  fi
done
[ "$borrado" = no ] && ssh -o BatchMode=yes -i "$KEY_TOOLS" "$TOOLS" "sudo rm -f $RELLENO"
ssh -o BatchMode=yes -i "$KEY_K8S" "$K8S" 'tail -3 /tmp/caos.log'
ssh -o BatchMode=yes -i "$KEY_TOOLS" "$TOOLS" 'curl -s localhost:9093/metrics | grep -E "^alertmanager_notifications(_failed)?_total\{integration=\"discord\"" | grep -v " 0$"'
