#!/usr/bin/env bash
# Apagado diario (deallocate) de las dos VMs. Lo ejecuta cron en VM-TOOLS.
#
# Por qué existe: el autoapagado nativo de Azure (Microsoft.DevTestLab/schedules)
# no está disponible para VMs en mexicocentral (ver docs/decisiones.md).
#
# Autenticación: identidad administrada de vm-tools con rol "Virtual Machine
# Contributor" limitado al grupo de recursos. No hay contraseñas ni tokens guardados.
set -uo pipefail

RG="RG-LAB03-K8S"
VMS_ORDEN=("vm-microk8s" "vm-tools")   # vm-tools al final: se apaga a sí misma
LOG="/var/log/medisur-autoapagado.log"
MODO="${1:-apagar}"                     # "probar" solo verifica permisos, no apaga nada

exec >> "$LOG" 2>&1
echo "=== $(date -u +%FT%TZ) inicio (modo: $MODO)"

if ! az login --identity --output none; then
  echo "ERROR: no se pudo autenticar con la identidad administrada"
  exit 1
fi

for vm in "${VMS_ORDEN[@]}"; do
  if [ "$MODO" = "probar" ]; then
    estado=$(az vm get-instance-view -g "$RG" -n "$vm" --query "instanceView.statuses[1].displayStatus" -o tsv)
    echo "prueba: $vm -> $estado"
  else
    # --no-wait: Azure acepta la solicitud de inmediato; así vm-tools alcanza a pedir su propio apagado.
    az vm deallocate -g "$RG" -n "$vm" --no-wait && echo "deallocate solicitado: $vm"
  fi
done

echo "=== $(date -u +%FT%TZ) fin"
