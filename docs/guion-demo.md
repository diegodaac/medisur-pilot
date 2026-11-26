# Guion de la demo en vivo

Los pasos **4, 8, 9 y 10** definen la calificación. Regla clave del enunciado: **si durante la demo alguien se conecta por SSH al clúster para arreglar algo, esa parte no cuenta.** Todos los comandos salen de la laptop: `git`, `gh`, `curl` y `kubectl` con un kubeconfig local.

## Preparación (30 min antes)

```bash
cd "<carpeta del proyecto>"
az vm start -g RG-LAB03-K8S -n vm-microk8s --no-wait && az vm start -g RG-LAB03-K8S -n vm-tools
./infra/mi-ip.sh                                  # permite la IP de la red donde se presenta
export KUBECONFIG=~/.kube/medisur.yaml            # kubectl directo al API de MicroK8s (sin SSH)
kubectl get pods -n medisur                       # 2/2 Running
curl -s http://158.23.21.125:30080/version        # anotar el SHA actual
URL=http://158.23.21.125:30080 ./infra/generar-trafico.sh 1800 &   # 30 min de tráfico para Grafana
```

- La rama `demo/sonar-falla` no debe existir (el script la crea): si quedó de un ensayo, `gh pr close <n> --delete-branch` y `git branch -D demo/sonar-falla`.
- Si se reinician las VMs, esperar a que Jenkins (`:8080`), SonarQube (`:9000`) y Grafana (`:3000`) carguen. Los contenedores tienen `restart: unless-stopped` y arrancan solos.
- Ventanas abiertas: terminal, Jenkins (*MediSur Pilot*), SonarQube, GitHub (repo y paquetes), Grafana (tablero *Aplicación*, últimos 15 min, refresco cada 10 s) y Discord.
- `~/.kube/medisur.yaml` tiene credenciales de administrador del clúster: vive solo en la laptop y nunca se sube al repositorio.
- Si la demo pasa de las 23:00, desactivar el autoapagado: `ssh -i ~/.ssh/id_rsa azureuser@158.23.177.202 'sudo chmod -x /usr/local/bin/medisur-autoapagado'`. Esto es SSH a VM-TOOLS para administrar herramientas, no al clúster.

## Desarrollo (unos 10 minutos)

| # | Acción (desde la laptop) | Qué decir / qué debe verse |
|---|---|---|
| 1 | `curl -s http://158.23.21.125:30080/version` | Anotar el SHA actual |
| 2 | `./infra/demo-sonar-falla.sh` y luego `git push -u origin demo/sonar-falla` y `gh pr create --fill` | Cambio en una rama y Pull Request |
| 3 | Mostrar Jenkins: el job **PR-N** aparece solo | Disparo por webhook; nadie toca Jenkins |
| 4 | **Fallo a propósito** | Se detiene en *Quality Gate* (cobertura ~30 %): Docker build, push y despliegue aparecen *skipped*. En GitHub, el PR queda **bloqueado**: no se puede fusionar |
| 5 | `git rm app/calculos_legacy.py && git commit -m "fix: elimina módulo sin pruebas" && git push`; cuando el check esté verde: `gh pr merge --squash --delete-branch` | El PR pasa a verde y se fusiona; arranca el build de `main` |
| 6 | GitHub → Packages | Imagen nueva con `<VERSION>-<sha>` y `<sha>`, sin `latest` |
| 7 | `kubectl get pods -n medisur -w` | Actualización gradual: el pod nuevo queda 0/1 unos 10 s (retardo de `/ready`) y luego se retira uno viejo; siempre hay 2 listos |
| 8 | `curl -s http://158.23.21.125:30080/version` | **SHA nuevo, sin SSH** |
| 9 | Con Grafana proyectado: `kubectl delete pod -n medisur <uno>` | El panel "Réplicas listas contra deseadas" baja a 1 y vuelve a 2 en segundos: el ReplicaSet crea otro pod; la readinessProbe impide que reciba tráfico hasta estar listo |
| 10 | `kubectl rollout undo deployment/medisur-api -n medisur` y luego `kubectl rollout status ...` y `curl .../version` | Vuelve el SHA anterior. `kubectl rollout history` muestra las revisiones con su build |

## Si algo sale mal

- **No arranca el build del PR:** en Jenkins, *MediSur Pilot → Scan Repository Now* (el webhook puede tardar unos segundos).
- **El Quality Gate se queda esperando:** revisar en SonarQube → Administration → Webhooks que el último envío sea 200.
- **No carga ninguna página:** cambió la IP de la red; correr `./infra/mi-ip.sh`.
- Respaldo: el video del ensayo completo (10 a 15 min).
