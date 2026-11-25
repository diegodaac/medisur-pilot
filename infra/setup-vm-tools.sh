#!/usr/bin/env bash
# Prepara VM-TOOLS (Ubuntu 22.04): Docker, Java, Jenkins nativo, kubectl, jq,
# parámetro del kernel para SonarQube y node_exporter.
# Ejecutar por SSH (instalación de herramientas) con:  sudo ./infra/setup-vm-tools.sh
# Idempotente: se puede repetir sin romper nada.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }
DIR="$(cd "$(dirname "$0")" && pwd)"
KUBECTL_VERSION="v1.31.4"

echo ">> Paquetes base, Java 17, Docker y jq"
apt-get update -y
apt-get install -y ca-certificates curl gnupg git jq fontconfig openjdk-17-jre docker.io docker-compose-v2
systemctl enable --now docker

echo ">> Repositorio e instalación de Jenkins (LTS, nativo)"
install -d -m 0755 /usr/share/keyrings
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key -o /usr/share/keyrings/jenkins-keyring.asc
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
echo "Listo. Contraseña inicial de Jenkins:"
cat /var/lib/jenkins/secrets/initialAdminPassword || true
echo "Siguiente paso: docs/runbook.md (SonarQube, Jenkins, monitoreo)."
