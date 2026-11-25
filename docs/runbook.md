# Runbook: de cero a demo

Orden alineado con las fases de `CLAUDE.md`. Todo lo que dice **(a mano)** lo hace Diego; ningún secreto se escribe en el repo ni en el chat.

## Fase 1 · Azure
1. Revisar y ejecutar, comando por comando, `infra/azure-commands.md` (VM-TOOLS, NSG, presupuesto, autoapagado).
2. Verificar SSH a ambas VMs. Anotar la **IP privada** de VM-K8S y de VM-TOOLS.

## Fase 2 · Repo en GitHub
1. `git init`, primer commit, crear el repo `medisur-pilot` en GitHub y subir `main` **(a mano)**.
2. Proteger `main` (Settings → Branches): exigir PR y el check de Jenkins.
3. Reemplazar en `Jenkinsfile`: `GHCR_OWNER` y `K8S_HOST`.
4. Verificar local (necesita Docker):
   ```bash
   docker build -t medisur-local --build-arg APP_VERSION=1.0.0 --build-arg GIT_SHA=$(git rev-parse --short=7 HEAD) --build-arg BUILD_DATE=$(date -u +%FT%TZ) .
   docker run --rm -p 8000:8000 -e READY_DELAY_SECONDS=0 medisur-local
   curl localhost:8000/version
   ```

## Fase 3 · VM-TOOLS
1. Copiar el repo a la VM (`git clone`) y ejecutar `sudo ./infra/setup-vm-tools.sh`.
2. SonarQube: `cd infra/sonarqube && cp env.example .env` **(editar contraseña a mano)** `&& docker compose up -d`. Entrar a `:9000`, cambiar la contraseña `admin`, generar un token **(a mano)**.
3. Quality Gate propio: `export SONAR_URL=http://localhost:9000; read -rs SONAR_TOKEN; export SONAR_TOKEN; ./infra/sonar-quality-gate.sh`.
4. Webhook de SonarQube (Administration → Configuration → Webhooks): `http://localhost:8080/sonarqube-webhook/`.
5. Jenkins (`:8080`): instalar plugins sugeridos más: *Pipeline*, *GitHub Branch Source*, *SonarQube Scanner*, *Prometheus metrics*, *Timestamper*, *Credentials Binding*.
6. Manage Jenkins → Tools: SonarQube Scanner con nombre **`sonar-scanner`** (instalación automática).
7. Manage Jenkins → System: servidor SonarQube con nombre **`sonarqube`**, URL `http://localhost:9000` y token como credencial *Secret text*.
8. Credentials **(a mano)**:
   | ID | Tipo | Contenido |
   |---|---|---|
   | `ghcr-pat` | Username with password | usuario de GitHub + PAT con `write:packages` |
   | `kubeconfig-k8s` | Secret file | kubeconfig de MicroK8s (Fase 5) |
   | `medisur-api-key` | Secret text | cualquier cadena aleatoria larga |
9. Crear un **Multibranch Pipeline** apuntando al repo (GitHub Branch Source, credencial de GitHub **(a mano)**).
10. Webhook en GitHub: `http://<IP-PUBLICA-VM-TOOLS>:8080/github-webhook/` (evento *push* y *pull_request*). Además, en la configuración del Multibranch, activar el disparo por *scan de webhook* de GitHub.
    **Sale de la fase cuando:** un push dispara el build solo.

## Fase 4 · CI hasta GHCR
- Con la rama `demo/sonar-falla` (`./infra/demo-sonar-falla.sh`) debe quedar **rojo** en *Quality Gate*.
- Con `main` o una rama normal debe quedar verde y verse la imagen en GHCR (hacer el paquete público o dejar que Jenkins cree el `imagePullSecret`).

## Fase 5 · VM-K8S y CD
1. `sudo ./infra/setup-vm-k8s.sh <IP_PRIVADA_VM_K8S>` (instala exporters, kube-state-metrics y el ServiceAccount de Prometheus).
2. Generar el kubeconfig para Jenkins (lo imprime el script) y subirlo a Jenkins como `kubeconfig-k8s` **(a mano)**.
3. Verificar desde VM-TOOLS: `KUBECONFIG=kubeconfig-jenkins kubectl get nodes` (si falla por certificado, revisar que la IP esté en el SAN).
4. Hacer merge a `main`: Jenkins crea namespace, ConfigMap, Secrets y Deployment. **Nunca** `kubectl apply` a mano.
   **Sale de la fase cuando:** un merge cambia `/version` sin SSH.

## Fase 6 · Monitoreo (en VM-TOOLS)
```bash
cd monitoring
cp env.example .env                           # editar K8S_PRIVATE_IP y contraseña de Grafana (a mano)
cp alertmanager.example.yml alertmanager.yml  # pegar el webhook de Discord (a mano)
mkdir -p secrets
# Copiar el token del ServiceAccount (lo imprime setup-vm-k8s.sh) a secrets/k8s-token (a mano)
chmod 644 secrets/k8s-token                   # el contenedor corre como usuario no root
docker compose up -d
```
- Prometheus `:9090` → *Status → Targets*: todo en **UP**.
- Grafana `:3000` → carpeta *MediSur*: dos tableros ya provisionados.
- Probar alertas sin tocar el despliegue: bajar temporalmente el umbral de `DiscoLleno` a 1 % (y `docker compose restart prometheus`), o detener `node_exporter` para disparar `DestinoCaido`. `PodReiniciandose` y `ReplicasNoDisponibles` se pueden provocar en la demo con `kubectl delete pod` repetido o una imagen rota por Jenkins.
  **Sale de la fase cuando:** borrar un pod se ve en Grafana.

## Regenerar los tableros
```bash
python3 monitoring/tools/gen_dashboards.py
```

## Cierre
- `az vm deallocate` en ambas VMs desde el portal/CLI.
- Al terminar el curso: borrar el grupo de recursos.
- Si algún secreto llegara a filtrarse: **rotarlo** y anotarlo en `docs/AI_LOG.md` / `docs/decisiones.md`.
