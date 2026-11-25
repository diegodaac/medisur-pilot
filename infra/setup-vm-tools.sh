#!/usr/bin/env bash
# Prepara VM-TOOLS (Ubuntu 22.04): Docker, Java, Jenkins nativo, kubectl, jq,
# parámetro del kernel para SonarQube y node_exporter.
# Ejecutar por SSH (instalación de herramientas) con:  sudo ./infra/setup-vm-tools.sh
# Idempotente: se puede repetir sin romper nada.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }
DIR="$(cd "$(dirname "$0")" && pwd)"
KUBECTL_VERSION="v1.35.6"   # misma versión que MicroK8s en VM-K8S (política de desfase ±1)

echo ">> Paquetes base, Java 17, Docker y jq"
apt-get update -y
apt-get install -y ca-certificates curl gnupg git jq fontconfig openjdk-17-jre docker.io docker-compose-v2
systemctl enable --now docker

echo ">> Repositorio e instalación de Jenkins (LTS, nativo)"
install -d -m 0755 /usr/share/keyrings
# Llave de firma vigente del repositorio (la de 2023 ya no firma; huella ...7198F4B714ABFC68).
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key -o /usr/share/keyrings/jenkins-keyring.asc
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  > /etc/apt/sources.list.d/jenkins.list
apt-get update -y
apt-get install -y jenkins
# Jenkins ejecuta `docker build/run` desde el pipeline.
usermod -aG docker jenkins
systemctl enable --now jenkins
systemctl restart jenkins

echo ">> kubectl ${KUBECTL_VERSION}"
curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" -o /usr/local/bin/kubectl
chmod 0755 /usr/local/bin/kubectl

echo ">> vm.max_map_count para SonarQube (persistente)"
echo "vm.max_map_count=524288" > /etc/sysctl.d/99-sonarqube.conf
echo "fs.file-max=131072" >> /etc/sysctl.d/99-sonarqube.conf
sysctl --system >/dev/null

echo ">> node_exporter"
"$DIR/install-node-exporter.sh"

echo
echo "Listo. La contraseña inicial de Jenkins NO se imprime aquí (para que no quede en logs)."
echo "Léela a mano con:  sudo cat /var/lib/jenkins/secrets/initialAdminPassword"
echo "Siguiente paso: docs/runbook.md (SonarQube, Jenkins, monitoreo)."
