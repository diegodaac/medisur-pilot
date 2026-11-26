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
| IPs permitidas en los NSG | Casa de Diego + red de la universidad (UANL), mediante `infra/mi-ip.sh`, que agrega la IP actual sin quitar la de casa | La demo se hace desde la universidad. Esa IP la comparte el campus, así que tras la entrega se ejecuta `./infra/mi-ip.sh --solo-casa`. Las pantallas de inicio de sesión quedan visibles para la red del campus, pero siguen exigiendo contraseña, y SSH exige la llave privada |
| Versión de kube-state-metrics | **v2.19.1** | La matriz de compatibilidad oficial asocia v2.19 con Kubernetes 1.35 (la versión del clúster). La v2.14 que proponía el primer borrador era para 1.32 |
| kubeconfig de Jenkins | `microk8s config` con `server: https://172.16.0.4:16443`, guardado solo en Jenkins Credentials (`kubeconfig-k8s`, Secret file) | El certificado del API server ya incluía la IP privada, así que la verificación TLS funciona sin `insecure-skip-tls-verify`. Probado desde VM-TOOLS con `kubectl get nodes` |
| Token de Prometheus | Secret `prometheus-reader-token` (tipo `service-account-token`), copiado a `monitoring/secrets/k8s-token` en VM-TOOLS con permisos 640 y grupo 65534 | El contenedor de Prometheus corre como `nobody` (65534); el directorio está ignorado por git. El token no pasó por pantalla: se copió de VM a VM por una tubería SSH |
| RBAC de MicroK8s | Se **activó** (`microk8s enable rbac` → `--authorization-mode=RBAC,Node`). El clúster de LAB-03 lo tenía desactivado (`AlwaysAllow`) | Detectado con `kubectl auth can-i`: sin RBAC, el ServiceAccount "de solo lectura" de Prometheus podía crear deployments. **Verificado después de activarlo:** Prometheus lee pods, nodos y cAdvisor (HTTP 200), pero recibe 403 al crear un deployment y no puede leer Secrets. El kubeconfig de Jenkins (usuario admin de MicroK8s) conserva acceso total. kube-state-metrics funciona sin errores de permisos y todos los pods del sistema siguen en Running |
| Extras de seguridad | **Incluidos** como etapas del pipeline: Hadolint y gitleaks en paralelo tras el checkout; Trivy antes del push (bloquea CRITICAL con parche, reporta HIGH). Imágenes con versión fijada, sin instalar nada en la VM | Rúbrica: "hasta tres herramientas bien integradas". Trivy detectó CVE-2025-62727 en starlette (se actualizó FastAPI); gitleaks tuvo falsos positivos revisados y registrados en `.gitleaksignore` |
| Check obligatorio en `main` | GitHub exige `continuous-integration/jenkins/pr-head` en verde y la rama actualizada para fusionar un PR | Un PR con el Quality Gate en rojo (como el PR de demo) queda bloqueado y no puede llegar a `main` ni por error |

## Incidentes de secretos (rotación)

| Fecha | Secreto | Qué pasó | Acción |
|---|---|---|---|
| 2026-11-25 | Token de usuario de SonarQube `jenkins` | Se pegó por error en el chat con el asistente de IA (nunca llegó al repositorio) | Revocado en SonarQube (My Account → Security) y reemplazado por uno nuevo, que solo se introduce en la terminal (`read -rs`) y en Jenkins Credentials |

## Limitaciones conocidas (para mencionar en el documento)

- SonarQube fijado en **10.7.0 Community**, que ya no tiene soporte ("no longer active"). Se mantuvo a propósito para la entrega: las versiones Community Build más recientes cambian el modo de calificación (MQR) y los nombres de las métricas, lo que pondría en riesgo el Quality Gate. En producción se actualizaría.

- El estado de `/api/items` es en memoria y **por réplica** (cada pod tiene el suyo) y se pierde al reiniciar.
- SonarQube Community analiza una sola rama: cada análisis sobrescribe el anterior; el Quality Gate propio evalúa el código total.
- `tls_config.insecure_skip_verify` en Prometheus hacia el API server de MicroK8s (certificado autofirmado) porque el tráfico es por IP privada dentro de la VNet.
