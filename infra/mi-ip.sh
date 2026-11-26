#!/usr/bin/env bash
# Agrega la IP pública ACTUAL de Diego a las reglas de administración de los NSG,
# conservando siempre la IP de casa. Úsalo al cambiar de red (universidad, datos
# móviles) y el día de la demo antes de empezar.
#
#   ./infra/mi-ip.sh            # casa + IP actual
#   ./infra/mi-ip.sh --solo-casa  # vuelve a dejar solo la IP de casa (tras la entrega)
#
# Requiere `az login`. Modifica recursos de Azure: lo ejecuta Diego.
set -euo pipefail

RG="RG-LAB03-K8S"
CASA="189.219.112.220/32"

if [ "${1:-}" = "--solo-casa" ]; then
  PREFIJOS=("$CASA")
else
  ACTUAL="$(curl -fsS -m 10 https://api.ipify.org)/32"
  echo ">> IP actual: ${ACTUAL}"
  PREFIJOS=("$CASA")
  [ "$ACTUAL" != "$CASA" ] && PREFIJOS+=("$ACTUAL")
fi

# NSG y regla: solo puertos de administración (22, 8080, 9000, 3000, 9090, 16443, 30080).
for par in "vm-tools-nsg diego-admin" \
           "vm-microk8s-nsg SSH" \
           "vm-microk8s-nsg PermitirAPIKubernetes" \
           "vm-microk8s-nsg PermitirAppNodePort"; do
  read -r nsg regla <<<"$par"
  az network nsg rule update -g "$RG" --nsg-name "$nsg" -n "$regla" \
    --source-address-prefixes "${PREFIJOS[@]}" \
    --query "join(' ', [name, ':', join(', ', sourceAddressPrefixes)])" -o tsv 2>/dev/null
done
echo "Listo. Puede tardar unos segundos en aplicarse."
