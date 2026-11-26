# Capturas de evidencia

Las imágenes viven en `entrega/capturas/` (fuera de git, porque se entregan dentro del documento Word). El generador `docs/tools/generar_documento.js` inserta cada una en su lugar según el número con que empieza el nombre del archivo.

Las capturas de terminal (08, 09, 10, 16 y 02) muestran la salida real de los comandos ejecutados desde la laptop, sin SSH al clúster. Las demás son capturas de la ventana del navegador.

- [x] `02-azure-presupuesto.png` — Presupuesto `medisur-50usd` de 50 USD con avisos al 80 %, 100 % y pronóstico, y las dos VMs (Azure CLI).
- [x] `04-jenkins-pr4-rojo.png` — Build del PR #4 detenido en *Quality Gate*; Docker build, push y despliegue saltados.
- [x] `04b-github-pr4-bloqueado.png` — GitHub: "All checks have failed", con el check de Jenkins requerido.
- [x] `05-sonar-gate-fallido.png` — Historial de SonarQube: Quality Gate *Failed* y luego *Passed*.
- [x] `06-jenkins-main-verde.png` — Pipeline completo en verde en `main` (vista de etapas).
- [x] `07-ghcr-etiquetas.png` — Paquete en GHCR con las etiquetas `<VERSION>-<sha>` y `<sha>`, sin `latest`.
- [x] `08-pods-corriendo.png` — `kubectl get pods` y `get deployment`: 2 réplicas `1/1 Running`.
- [x] `09-curl-version.png` — `curl /version` y `/health`, e historial de revisiones del Deployment.
- [x] `10-rolling-update-pods-w.png` — `kubectl get pods -w` durante la actualización gradual.
- [x] `11-grafana-infra.png` — Tablero Infraestructura con datos reales de las dos VMs.
- [x] `12-grafana-app.png` — Tablero Aplicación con datos reales.
- [x] `13-grafana-caos.png` — Réplicas listas 2 → 1 → 2 durante el experimento de caos.
- [x] `13b-grafana-caos-reinicios.png` — Reinicios del contenedor durante el experimento de caos.
- [x] `14-prometheus-targets.png` — Prometheus › Targets: 13/13 destinos en UP.
- [x] `15-discord-alertas.png` — Notificaciones de Alertmanager en Discord.
- [x] `15b-grafana-alertas-disparadas.png` — Las cuatro alertas disparadas (Grafana Explore, `ALERTS{alertstate="firing"}`).
- [x] `16-rollout-undo.png` — `kubectl rollout undo` y `/version` con la versión anterior.
- [x] `17-jenkinsfile-github.png` — El `Jenkinsfile` versionado en el repositorio.
- [x] `17b-github-proteccion-main.png` — Protección de la rama `main`.

Pendiente fuera de las capturas: el enlace al **video de respaldo** (10 a 15 min) en los anexos del documento.
