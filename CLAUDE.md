# Proyecto: Trabajo final de Cómputo en la Nube (UANL FCFM)

Piloto de entrega continua sobre Kubernetes para el caso ficticio MediSur, S.A. de C.V.
Autor: Diego Alejandro Alvarado Castañón (trabajo individual). Entrega: HOY.
Enunciado completo: https://github.com/jorgealbertopineda78-del/cloud-compute/wiki/rabajo-final:-automatización-de-entrega-continua-sobre-Kubernetes

Idioma de trabajo: español formal. Se evalúa la AUTOMATIZACIÓN, no la aplicación: una API simple bien automatizada y monitoreada.

## Reglas que no se negocian (romper una cuesta la calificación)

- Dos VMs separadas en Azure: VM-TOOLS (construir, analizar, vigilar) y VM-K8S (ejecutar la app).
- Nunca usar la etiqueta `latest`. Etiquetas: `<VERSION>-<sha corto>` y `<sha corto>`.
- Ningún secreto en el repositorio ni en el historial (kubeconfig, tokens, PAT, contraseñas, webhooks de Discord). Si se filtra uno, rotarlo y documentarlo.
- El pipeline vive en el repositorio (`Jenkinsfile`), no configurado a clics.
- Mínimo `replicas: 2`, `livenessProbe` y `readinessProbe` declaradas.
- Cero despliegues manuales: todo despliegue pasa por Jenkins. El SSH solo se usa para INSTALAR herramientas, nunca para desplegar.
- Los tableros de Grafana deben tener datos reales.
- Prometheus NO va dentro del clúster: corre en VM-TOOLS.

## Reglas para Claude Code en este proyecto

- Antes de ejecutar comandos que creen o modifiquen recursos de Azure, mostrar el comando y esperar confirmación.
- Contraseñas, tokens, PAT de GitHub y webhooks los introduce Diego a mano (en Jenkins Credentials o en archivos ignorados por git). No escribirlos en archivos versionados ni repetirlos en el chat.
- Mantener `.gitignore` con: `kubeconfig*`, `*.env`, `.env*`, `alertmanager.yml`, `secrets/`, `coverage.xml`, `htmlcov/`, `__pycache__/`.
- Mantener un registro `docs/AI_LOG.md` con cada uso relevante de IA: dónde, qué se pidió (esencia), qué devolvió, qué se corrigió y por qué. Sirve para la sección obligatoria "Declaración de uso de IA" del documento Word.
- Guardar en `docs/evidencias/` una lista de las capturas pendientes que Diego debe tomar (pipeline rojo por Sonar, pipeline verde, imagen en GHCR, pods corriendo, tableros, alertas recibidas).
- Comentar el `Jenkinsfile` etapa por etapa: en la defensa pueden preguntar por cualquier línea.

## Decisiones de diseño ya tomadas

| Tema | Decisión | Motivo |
|---|---|---|
| Lenguaje | Python 3.12 + FastAPI + uvicorn + prometheus_client | Dominio previo; coverage.py genera XML para Sonar |
| Pruebas | pytest + pytest-cov, mínimo 5 pruebas reales | Requisito; cobertura ≥ 60 % |
| Repo y registro | GitHub + GHCR | Una sola plataforma, webhook nativo |
| Kubernetes | MicroK8s en VM-K8S (reutilizar la VM de LAB-03) | Continuidad con LAB-03; puerto 16443 del enunciado |
| CI/CD | Jenkins nativo (apt) en VM-TOOLS, Multibranch Pipeline | Construye ramas y PR; CD solo en `main` |
| Calidad | SonarQube Community en Docker, Quality Gate PROPIO | Ver nota sobre Community abajo |
| Monitoreo | Prometheus + Grafana + Alertmanager en Docker Compose (VM-TOOLS) | Configuración versionada como código |
| Alertas | Reglas de Prometheus → Alertmanager → Discord (o correo) | Reglas versionadas en el repo |
| Despliegue | `kubectl` directo desde Jenkins con kubeconfig en Jenkins Credentials | Lo que exige el núcleo |
| Extras (solo si sobra tiempo) | Hadolint, Trivy, gitleaks como etapas del pipeline | Baratos; suman seguridad |

## Infraestructura Azure

- Suscripción Azure for Students. Regiones permitidas: mexicocentral, canadacentral, westus2, westus, chilecentral.
- VM-K8S: la VM existente de LAB-03 (verificar tamaño B2ms, Ubuntu 22.04, MicroK8s funcionando).
- VM-TOOLS: crear nueva, B4ms (4 vCPU, 16 GB), Ubuntu Server 22.04 LTS, SSD estándar 64 GB, MISMA región y MISMA VNet que VM-K8S (si no es posible, usar peering de VNet).
- NSG VM-TOOLS: 22 solo IP de Diego; 8080 (Jenkins) solo IP de Diego + rangos `hooks` de `https://api.github.com/meta`; 9000, 3000, 9090 solo IP de Diego.
- NSG VM-K8S: 22 y 16443 solo IP de Diego; 80 abierto o IP de Diego; 9100 y 8080 solo desde la IP privada de VM-TOOLS.
- Costos obligatorios: alerta de presupuesto 50 USD, apagado automático diario en ambas VMs, detener siempre desde el portal (deallocate), retención de Prometheus 15 días, borrar grupos de recursos al terminar.

## Aplicación (directorio app/)

Endpoints obligatorios:
- `GET /health`: 200 si el proceso vive.
- `GET /ready`: 200 solo si puede atender tráfico; 503 durante `READY_DELAY_SECONDS` tras el arranque (hace visible la actualización gradual).
- `GET /version`: `{version, commit, build_date}` leídos de variables de entorno inyectadas al construir (`APP_VERSION`, `GIT_SHA`, `BUILD_DATE` vía `ARG` → `ENV` en el Dockerfile).
- `GET /metrics`: formato Prometheus. Mínimo: `http_requests_total{method,endpoint,status}` (Counter) y `http_request_duration_seconds{method,endpoint}` (Histogram). Además `app_info{version,commit} 1` (Gauge) para mostrar la versión desplegada en Grafana.
- `GET /api/items` y `POST /api/items`: almacenamiento en memoria con validación Pydantic (documentar que cada réplica tiene su propio estado; es un piloto).
- Toda configuración por variables de entorno (puerto, nivel de log, retardo de ready, nombre del servicio). Nada fijo en el código.

Dockerfile multietapa: etapa builder instala dependencias en un venv; etapa final `python:3.12-slim` sin herramientas de compilación, usuario sin privilegios (UID fijo, p. ej. 10001), `EXPOSE 8000`, `HEALTHCHECK` opcional.

Dependencias con versiones fijadas (`==`) en `requirements.txt` y `requirements-dev.txt`.

## Estructura del repositorio

```
medisur-pilot/
├── app/                 main.py, config.py, metrics.py, store.py
├── tests/               ≥5 pruebas reales
├── Dockerfile
├── .dockerignore
├── VERSION              1.0.0
├── requirements.txt
├── requirements-dev.txt
├── Jenkinsfile
├── sonar-project.properties
├── k8s/                 namespace.yaml, configmap.yaml, secret.template.yaml, deployment.yaml, service.yaml
├── monitoring/          docker-compose.yml, prometheus.yml, rules/alerts.yml,
│                        alertmanager.example.yml, grafana/provisioning/, grafana/dashboards/*.json
├── infra/               setup-vm-tools.sh, setup-vm-k8s.sh, comandos az documentados
└── docs/                AI_LOG.md, evidencias/, decisiones.md
```

## Pipeline (Jenkinsfile, declarativo)

CI con cada push (todas las ramas y PR):
1. Disparo por webhook de GitHub (sin intervención humana).
2. Checkout y registro del SHA corto (`git rev-parse --short HEAD`).
3. Instalación de dependencias fijadas en un venv.
4. Pruebas con `pytest --cov=app --cov-report=xml`. IMPORTANTE: NO usar `--cov-fail-under`; la cobertura la debe bloquear Sonar (demo, paso 4).
5. Análisis con SonarScanner (código + `coverage.xml`), dentro de `withSonarQubeEnv`.
6. `timeout(time: 5, unit: 'MINUTES') { waitForQualityGate abortPipeline: true }`. Requiere webhook de SonarQube → `http://localhost:8080/sonarqube-webhook/`.
7. `docker build` con `--build-arg GIT_SHA=... APP_VERSION=... BUILD_DATE=...`.
8. `docker push` a `ghcr.io/<usuario>/medisur-pilot` con etiquetas `<VERSION>-<sha>` y `<sha>`. Login con credencial de Jenkins (PAT con `write:packages`).

CD solo en `main` (`when { branch 'main' }`):
9. `kubectl set image deployment/medisur-api api=<imagen:etiqueta>` usando kubeconfig de Jenkins Credentials (tipo Secret file).
10. `kubectl rollout status deployment/medisur-api --timeout=120s`.
11. Prueba de humo: `curl -f` a `/health` y `/version`, verificando que el SHA de `/version` coincide.
12. `post { failure { kubectl rollout undo ... } }`: reversión automática y pipeline en rojo.

Si cualquier etapa de CI falla, nada llega a Kubernetes.

Si la imagen en GHCR es privada, Jenkins crea el `imagePullSecret` desde sus credenciales; alternativa aceptable: hacer público el paquete (la imagen no contiene secretos).

## SonarQube

- Correr en Docker en VM-TOOLS. Requiere en el host: `sysctl -w vm.max_map_count=524288` (persistir en `/etc/sysctl.d/`).
- Community Edition analiza una sola rama y el "Sonar way" evalúa sobre todo el código nuevo. Crear Quality Gate propio con condiciones sobre el código TOTAL: cobertura < 60 % falla, confiabilidad peor que A falla, seguridad peor que A falla. Asignarlo al proyecto.
- Preparar una rama de demo con un bug crítico o con pruebas eliminadas para bajar la cobertura.

## Kubernetes (manifiestos en k8s/)

- Namespace `medisur`.
- Deployment `medisur-api`: `replicas: 2`, estrategia RollingUpdate (`maxUnavailable: 0`, `maxSurge: 1`), liveness en `/health`, readiness en `/ready`, `requests` y `limits` de CPU y memoria, `securityContext` no root, variables desde ConfigMap y Secret.
- Service NodePort o ClusterIP + Ingress de MicroK8s (puerto 80) para que la prueba de humo y `curl /version` funcionen desde fuera.
- Secret: versionar solo `secret.template.yaml` con marcadores; Jenkins lo genera con `kubectl create secret generic ... --dry-run=client -o yaml | kubectl apply -f -`.
- Desde Jenkins, kubeconfig generado con `microk8s config` apuntando a la IP PRIVADA de VM-K8S. Verificar que el certificado del API server incluya esa IP (en LAB-03 posiblemente ya se editó `csr.conf.template`).
- Crear un ServiceAccount de solo lectura para Prometheus con su token (nunca versionado).

## Monitoreo

Exporters:
- node_exporter en ambas VMs (puerto 9100, servicio systemd, con `--collector.systemd` para el estado de servicios).
- kube-state-metrics en VM-K8S, expuesto por NodePort en 8080.

Prometheus (VM-TOOLS), `--storage.tsdb.retention.time=15d`. Jobs de scrape:
- `node-tools` y `node-k8s` (9100 por IP privada).
- `kube-state-metrics` (IP privada de VM-K8S:8080).
- `medisur-pods`: pods de la app a través del proxy del API server (`https://<ip-privada>:16443/api/v1/namespaces/medisur/pods/<pod>:8000/proxy/metrics`) con `kubernetes_sd_configs` (role: pod), token de ServiceAccount y relabeling. No hacer scrape a través del Service: con 2 réplicas los contadores saldrían incoherentes.
- `cadvisor`: CPU y memoria por pod vía `/api/v1/nodes/<node>/proxy/metrics/cadvisor`.
- Jenkins (plugin Prometheus, `/prometheus`), Prometheus mismo y Grafana.

Tablero 1, Infraestructura (dos VMs lado a lado): CPU, memoria disponible, disco, red, estado de servicios (Jenkins, SonarQube, Prometheus, Grafana) y tiempo encendido (`node_time_seconds - node_boot_time_seconds`).

Tablero 2, Aplicación: réplicas listas contra deseadas, reinicios de contenedor, peticiones por segundo, tasa de 5xx, latencia p95, CPU y memoria por pod, versión desplegada (`app_info`).

Tableros provisionados como JSON en `monitoring/grafana/dashboards/`.

Alertas mínimas (`monitoring/rules/alerts.yml`):
- Disco > 80 % en cualquier VM.
- `increase(kube_pod_container_status_restarts_total{namespace="medisur"}[10m]) > 3`.
- `kube_deployment_status_replicas_available < kube_deployment_spec_replicas` durante 5m.
Alertmanager envía a Discord (`discord_configs`); el webhook va en `alertmanager.yml` NO versionado (solo `alertmanager.example.yml`).

## Plan de hoy, con criterio de salida por fase

1. Azure: verificar VM de LAB-03, crear VM-TOOLS, NSG, presupuesto, autoapagado. Sale cuando hay SSH a ambas.
2. App + pruebas + Dockerfile + repo en GitHub con `main` protegida. Sale cuando `docker run` local devuelve `/version` con SHA.
3. VM-TOOLS: Docker, Jenkins, SonarQube, credenciales, webhook. Sale cuando un push dispara el build solo.
4. Pipeline CI completo hasta GHCR. Sale cuando hay un build rojo por Sonar y uno verde con imagen en GHCR.
5. CD a MicroK8s con prueba de humo y reversión automática. Sale cuando un merge cambia `/version` sin SSH.
6. Monitoreo: exporters, Prometheus, dos tableros, tres alertas llegando a Discord. Sale cuando borrar un pod se ve en Grafana.
7. Extras si sobra tiempo (Hadolint, Trivy, gitleaks).
8. Ensayo completo de la demo y grabación del video de respaldo (10 a 15 min).

Demo en vivo (los pasos 4, 8, 9 y 10 definen la calificación):
1. `curl /version` y anotar SHA. 2. Cambio en rama + PR. 3. Jenkins arranca solo. 4. Fallo a propósito: Sonar detiene el build, no hay imagen. 5. Corrección, merge, pipeline verde. 6. Imagen nueva en GHCR. 7. `kubectl get pods -w`. 8. `curl /version`: SHA nuevo, sin SSH. 9. Con Grafana proyectado, `kubectl delete pod` y explicar la recuperación. 10. `kubectl rollout undo` y `/version` muestra la versión anterior.
