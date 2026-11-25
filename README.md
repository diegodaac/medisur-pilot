# MediSur Pilot

Piloto de entrega continua sobre Kubernetes para MediSur, S.A. de C.V. (trabajo final de Cómputo en la Nube, UANL FCFM). Se evalúa la **automatización**: una API sencilla, construida, analizada, publicada, desplegada y monitoreada sin pasos manuales.

```
GitHub ──webhook──▶ Jenkins (VM-TOOLS) ──▶ pytest ▶ SonarQube (Quality Gate) ▶ docker build ▶ GHCR
                                                                                     │ (solo main)
                                                         kubectl set image + rollout + prueba de humo
                                                                                     ▼
                                                                    MicroK8s (VM-K8S): medisur-api ×2

VM-TOOLS: Prometheus + Alertmanager ──▶ Discord · Grafana · SonarQube        (nada de esto corre en el clúster)
```

## Estructura

| Ruta | Contenido |
|---|---|
| `app/` | API FastAPI: `/health`, `/ready`, `/version`, `/metrics`, `/api/items` |
| `tests/` | 33 pruebas (pytest) |
| `Dockerfile` | Multietapa, usuario no root (UID 10001), metadatos de versión por `ARG` |
| `Jenkinsfile` | Pipeline declarativo, comentado etapa por etapa |
| `k8s/` | Namespace, ConfigMap, plantilla de Secret, Deployment (2 réplicas) y Service |
| `monitoring/` | Prometheus, Alertmanager, Grafana (tableros provisionados), blackbox |
| `infra/` | Scripts de instalación de herramientas, SonarQube, comandos de Azure |
| `docs/` | Runbook, guion de demo, decisiones, registro de IA, lista de capturas |

## Probar la aplicación localmente

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing
READY_DELAY_SECONDS=0 APP_VERSION=1.0.0 GIT_SHA=local01 python -m app.main
curl localhost:8000/version
```

## Versionado de imágenes

`<VERSION>-<sha corto>` y `<sha corto>` (por ejemplo `1.0.0-a1b2c3d` y `a1b2c3d`). **Nunca** `latest`. La versión sale del archivo `VERSION`.

## Reglas de seguridad

Ningún secreto en el repositorio: kubeconfig, tokens, PAT y webhooks viven en Jenkins Credentials o en archivos ignorados por git (ver `.gitignore`).

Guía completa de puesta en marcha: [`docs/runbook.md`](docs/runbook.md).
