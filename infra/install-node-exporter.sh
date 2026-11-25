#!/usr/bin/env bash
# Instala node_exporter como servicio systemd (puerto 9100, con collector de systemd).
# Se usa en AMBAS VMs. Ejecutar con sudo. Es una instalación de herramientas por
# SSH (permitido); los despliegues de la app NO se hacen por aquí.
set -euo pipefail

VERSION="1.8.2"
ARCH="linux-amd64"
URL="https://github.com/prometheus/node_exporter/releases/download/v${VERSION}/node_exporter-${VERSION}.${ARCH}.tar.gz"

[ "$(id -u)" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo ">> Descargando node_exporter ${VERSION}"
curl -fsSL "$URL" -o "$TMP/ne.tar.gz"
curl -fsSL "https://github.com/prometheus/node_exporter/releases/download/v${VERSION}/sha256sums.txt" -o "$TMP/sha256sums.txt"
( cd "$TMP" && grep "node_exporter-${VERSION}.${ARCH}.tar.gz" sha256sums.txt | sed 's#  .*#  ne.tar.gz#' | sha256sum -c - )

tar -xzf "$TMP/ne.tar.gz" -C "$TMP"
install -m 0755 "$TMP/node_exporter-${VERSION}.${ARCH}/node_exporter" /usr/local/bin/node_exporter

id node_exporter >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin node_exporter

cat > /etc/systemd/system/node_exporter.service <<'UNIT'
[Unit]
Description=Prometheus node_exporter
After=network-online.target
Wants=network-online.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter --collector.systemd --web.listen-address=:9100
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now node_exporter
sleep 1
# Sin `| head`: con pipefail, cortar la tubería hace que curl salga con código 23.
curl -fsS -o /dev/null http://localhost:9100/metrics
echo ">> node_exporter activo en :9100"
