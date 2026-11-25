# Guion de la demo en vivo

Los pasos **4, 8, 9 y 10** definen la calificación. Tener abiertas: terminal con `kubectl`, Jenkins, SonarQube, GHCR, Grafana (proyectado) y GitHub.

| # | Acción | Qué decir / qué debe verse |
|---|---|---|
| 1 | `curl http://<IP-VM-K8S>:30080/version` | Anotar el SHA actual |
| 2 | Rama `demo/sonar-falla` (`./infra/demo-sonar-falla.sh`), push y PR | Cambio en rama + PR |
| 3 | Ver en Jenkins cómo arranca solo | Webhook de GitHub, sin intervención humana |
| 4 | **Fallo a propósito** | El build se detiene en *Quality Gate* (cobertura < 60 %): no se construye imagen, no se toca Kubernetes |
| 5 | Corregir (`git rm app/calculos_legacy.py`), push, merge del PR | Pipeline verde |
| 6 | Mostrar la imagen nueva en GHCR | Etiquetas `<VERSION>-<sha>` y `<sha>`, sin `latest` |
| 7 | `kubectl get pods -n medisur -w` | Actualización gradual: pods nuevos 0/1 durante el retardo de `/ready`, siempre ≥ 2 listos |
| 8 | `curl .../version` | **SHA nuevo, sin SSH** |
| 9 | Con Grafana proyectado: `kubectl delete pod -n medisur <pod>` | Ver la caída de réplicas y la recuperación automática (ReplicaSet) |
| 10 | `kubectl -n medisur rollout undo deployment/medisur-api` y `curl .../version` | Vuelve la versión anterior |

Notas:
- El paso 9 y 10 son comandos de **demostración** sobre el clúster; el despliegue de la versión nueva (paso 8) lo hizo Jenkins.
- Respaldo: grabar el ensayo completo en video de 10 a 15 minutos.
