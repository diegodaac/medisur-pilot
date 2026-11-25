#!/usr/bin/env bash
# Instala en VM-TOOLS el Azure CLI y el cron del apagado diario.
# Requisito previo (una vez, desde la laptop):
#   az vm identity assign -g RG-LAB03-K8S -n vm-tools
#   az role assignment create --assignee-object-id <principalId> --assignee-principal-type ServicePrincipal \
#     --role "Virtual Machine Contributor" --scope <id-del-grupo-de-recursos>
# Uso en VM-TOOLS:  sudo ./infra/install-autoapagado.sh
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }
DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v az >/dev/null; then
  echo ">> Instalando Azure CLI (repositorio oficial de Microsoft)"
  apt-get update -y
  apt-get install -y ca-certificates curl apt-transport-https lsb-release gnupg
  install -d -m 0755 /etc/apt/keyrings
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg
  chmod go+r /etc/apt/keyrings/microsoft.gpg
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/azure-cli.list
  apt-get update -y
  apt-get install -y azure-cli
fi

install -m 0755 "$DIR/autoapagado.sh" /usr/local/bin/medisur-autoapagado

# La VM está en UTC. 05:00 UTC = 23:00 en Monterrey (México ya no usa horario de verano).
cat > /etc/cron.d/medisur-autoapagado <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 5 * * * root /usr/local/bin/medisur-autoapagado
CRON
chmod 0644 /etc/cron.d/medisur-autoapagado

echo ">> Prueba de permisos (no apaga nada)"
/usr/local/bin/medisur-autoapagado probar || true
tail -n 5 /var/log/medisur-autoapagado.log
