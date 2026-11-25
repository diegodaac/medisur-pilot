# Capturas pendientes (las toma Diego)

Guardar cada imagen en esta carpeta con el nombre sugerido. Marcar al terminar.

- [ ] `01-vms-azure.png` — Portal de Azure con VM-TOOLS y VM-K8S encendidas, misma región y VNet.
- [ ] `02-presupuesto-autoapagado.png` — Alerta de presupuesto 50 USD y apagado automático configurado.
- [ ] `03-webhook-github.png` — Webhook de GitHub con entrega exitosa (✓) hacia Jenkins.
- [ ] `04-pipeline-rojo-sonar.png` — Build **rojo** en la etapa *Quality Gate* (cobertura < 60 %), y que no hay etapas de Docker/CD después.
- [ ] `05-sonar-gate-fallido.png` — Pantalla de SonarQube con el Quality Gate "MediSur" en *Failed*.
- [ ] `06-pipeline-verde.png` — Build **verde** completo (CI + CD) en la rama `main`.
- [ ] `07-ghcr-etiquetas.png` — Paquete en GHCR mostrando las etiquetas `<VERSION>-<sha>` y `<sha>` (sin `latest`).
- [ ] `08-pods-corriendo.png` — `kubectl get pods -n medisur` con 2 réplicas `1/1 Running`.
- [ ] `09-curl-version.png` — `curl http://<IP-VM-K8S>:30080/version` con el SHA nuevo.
- [ ] `10-rolling-update.png` — `kubectl get pods -w` durante la actualización gradual.
- [ ] `11-grafana-infra.png` — Tablero *Infraestructura* con datos reales de las dos VMs.
- [ ] `12-grafana-app.png` — Tablero *Aplicación* con datos reales (versión, réplicas, p95, etc.).
- [ ] `13-grafana-pod-eliminado.png` — Tablero *Aplicación* mostrando la caída y recuperación tras `kubectl delete pod`.
- [ ] `14-prometheus-targets.png` — Prometheus > Status > Targets con todos los destinos en *UP*.
- [ ] `15-alertas-discord.png` — Las tres alertas (disco, reinicios, réplicas) recibidas en Discord.
- [ ] `16-rollback.png` — `kubectl rollout undo` y `/version` con la versión anterior.
- [ ] `17-jenkinsfile-en-repo.png` — El `Jenkinsfile` en GitHub (el pipeline vive en el repo, no configurado a clics).
