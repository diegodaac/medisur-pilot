# Decisiones de diseño

Las decisiones base están en `CLAUDE.md`. Aquí se anotan las **desviaciones o detalles** que surgieron al implementar, con su motivo, para poder defenderlas.

| Tema | Decisión | Motivo |
|---|---|---|
| Pruebas dentro de contenedor | La etapa de pruebas corre en `python:3.12-slim` con el workspace montado en la misma ruta | VM-TOOLS (Ubuntu 22.04) trae Python 3.10; así se prueba con la misma versión que producción y el `coverage.xml` conserva rutas que Sonar resuelve |
| Aplicar manifiesto + `set image` | El pipeline aplica `k8s/deployment.yaml` (con `__IMAGE__` sustituido) y luego ejecuta `kubectl set image` | La primera vez el Deployment no existe; re-aplicar el manifiesto con la imagen real evita que la plantilla "pise" la imagen vigente. El `set image` queda explícito como pide el enunciado |
| Servicio expuesto | `NodePort 30080` en lugar de puerto 80 con Ingress | Menos piezas (no hace falta el addon `ingress`); el NodePort basta para la prueba de humo y el `curl /version`. El NSG de VM-K8S abre 30080 en vez de 80 |
| kube-state-metrics | NodePort **30808** en lugar de 8080 | El rango válido de NodePort es 30000-32767; el Service original es headless, así que se añade `kube-state-metrics-np` |
| Estado de servicios en Grafana | `blackbox_exporter` (probe HTTP) + `node_systemd_unit_state` para Jenkins | SonarQube, Prometheus y Grafana corren en Docker, así que el collector de systemd no los ve |
| Métricas y `/ready` | El panel de 5xx excluye `endpoint="/ready"` | `/ready` responde 503 a propósito durante el retardo de arranque; sin el filtro cada despliegue parecería un incidente |
| `/metrics` | No se cuenta a sí mismo en `http_requests_total` | Evita inflar las peticiones por segundo con el scrape de Prometheus |
| Prometheus y la IP de K8s | `prometheus.tpl.yml` con marcador `K8S_PRIVATE_IP`, renderizado al arrancar el contenedor desde `monitoring/.env` | Un solo archivo versionado, sin editar a mano ni ensuciar el árbol de git en la VM |
| Secreto de la app | `APP_API_KEY` en el Secret `medisur-api-secret`, creado por Jenkins desde la credencial `medisur-api-key` | Demuestra el flujo de secretos (ConfigMap + Secret) sin versionar nada. La app no lo usa; es un piloto |
| Tamaño de VM-TOOLS | `Standard_B4as_v2` (4 vCPU AMD, 16 GB) en lugar de B4ms | B4ms no está disponible para la suscripción en mexicocentral (restricción `Location`). B4as_v2 tiene los mismos recursos y es de la misma familia que VM-K8S. Con ella se usan los 6 vCPU de cuota regional |
| VM-K8S | `Standard_B2as_v2` (2 vCPU, 8 GB), Ubuntu **24.04**, MicroK8s v1.35.6 | Es la VM reutilizada de LAB-03; sus recursos equivalen a B2ms. `kubectl` en VM-TOOLS se fija a v1.35.6 |
| Autoapagado | Cron diario en VM-TOOLS (05:00 UTC = 23:00 Monterrey) que ejecuta `az vm deallocate` sobre `vm-microk8s` y luego `vm-tools`, autenticado con la **identidad administrada** de `vm-tools` (rol *Virtual Machine Contributor* solo sobre el grupo de recursos). Scripts: `infra/autoapagado.sh` e `infra/install-autoapagado.sh`. Limitación: si VM-TOOLS ya está apagada, no apaga VM-K8S | `Microsoft.DevTestLab/schedules` debe crearse en la región de la VM (`InvalidScheduleLocation`) y ese tipo de recurso no existe en `mexicocentral` (`LocationNotAvailableForResourceType`). `az vm auto-shutdown` además fallaba porque el grupo de recursos está en `centralus`, región no permitida |
| NSG de VM-K8S | La regla `SSH` estaba abierta a `*` desde LAB-03; se restringió a la IP de Diego | Cumplir la regla del NSG |
| Extras (Hadolint, Trivy, gitleaks) | No incluidos en el `Jenkinsfile` | Se agregan al final solo si sobra tiempo (fase 7) |

## Limitaciones conocidas (para mencionar en el documento)

- El estado de `/api/items` es en memoria y **por réplica** (cada pod tiene el suyo) y se pierde al reiniciar.
- SonarQube Community analiza una sola rama: cada análisis sobrescribe el anterior; el Quality Gate propio evalúa el código total.
- `tls_config.insecure_skip_verify` en Prometheus hacia el API server de MicroK8s (certificado autofirmado) porque el tráfico es por IP privada dentro de la VNet.
