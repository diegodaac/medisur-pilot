#!/usr/bin/env bash
# Prepara VM-K8S (Ubuntu 22.04 con MicroK8s de LAB-03): node_exporter,
# kube-state-metrics (NodePort 30808) y ServiceAccount de solo lectura para Prometheus.
# Ejecutar por SSH (instalación de herramientas) con:  sudo ./infra/setup-vm-k8s.sh <IP_PRIVADA_VM_K8S>
# Esto NO despliega la aplicación: eso lo hace únicamente Jenkins.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }
PRIVATE_IP="${1:?Uso: sudo $0 <IP_PRIVADA_VM_K8S>}"
DIR="$(cd "$(dirname "$0")" && pwd)"
KSM_VERSION="v2.14.0"
KUBECTL="microk8s kubectl"
CSR=/var/snap/microk8s/current/certs/csr.conf.template
CRT=/var/snap/microk8s/current/certs/server.crt

echo ">> Verificando MicroK8s"
microk8s status --wait-ready >/dev/null

echo ">> El certificado del API server debe incluir la IP privada ${PRIVATE_IP}"
# Se revisa el certificado REAL (MicroK8s agrega solo las IPs de sus interfaces).
if ! openssl x509 -in "$CRT" -noout -ext subjectAltName | grep -q "IP Address:${PRIVATE_IP}\b"; then
  NEXT=$(( $(grep -cE '^IP\.[0-9]+' "$CSR") + 1 ))
  echo "IP.${NEXT} = ${PRIVATE_IP}" >> "$CSR"
  echo "   agregada al template; regenerando certificado del servidor"
  microk8s refresh-certs --cert server.crt
  microk8s status --wait-ready >/dev/null
else
  echo "   ya estaba incluida"
fi

echo ">> node_exporter"
"$DIR/install-node-exporter.sh"

echo ">> kube-state-metrics ${KSM_VERSION}"
$KUBECTL apply -k "github.com/kubernetes/kube-state-metrics/examples/standard?ref=${KSM_VERSION}"
$KUBECTL apply -f "$DIR/kube-state-metrics-nodeport.yaml"

echo ">> ServiceAccount de solo lectura para Prometheus"
$KUBECTL apply -f "$DIR/prometheus-rbac.yaml"

cat <<EOF

Listo. Pasos manuales que quedan (los secretos NUNCA van al repo):
  1) Token del ServiceAccount (copiarlo a VM-TOOLS en monitoring/secrets/k8s-token):
       $KUBECTL -n kube-system get secret prometheus-reader-token -o jsonpath='{.data.token}' | base64 -d > k8s-token
  2) kubeconfig para Jenkins (se sube a Jenkins Credentials como Secret file, id: kubeconfig-k8s):
       microk8s config | sed "s#server: .*#server: https://${PRIVATE_IP}:16443#" > kubeconfig-jenkins
EOF
