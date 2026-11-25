# Registro de uso de IA

Base para la sección obligatoria **"Declaración de uso de IA"** del documento Word. Cada entrada: dónde, qué se pidió (esencia), qué devolvió, qué se corrigió y por qué.

> Herramienta: Claude Code (modelo Claude Sonnet 5.5) dentro de la app de escritorio de Claude.

| # | Fecha | Dónde | Qué se pidió (esencia) | Qué devolvió la IA | Qué se corrigió / validó y por qué |
|---|---|---|---|---|---|
| 1 | 2026-11-25 | Estructura completa del repo | Partir de `CLAUDE.md` (decisiones y reglas del proyecto) y generar la primera versión del código y la configuración | App FastAPI (`app/`), 33 pruebas, Dockerfile multietapa, manifiestos de `k8s/`, `Jenkinsfile` comentado, stack de monitoreo, scripts de instalación y documentación | **Validado:** las pruebas se ejecutaron localmente (33 pasan, 100 % de cobertura); `/version` y `/metrics` se probaron con la app corriendo; la sintaxis de YAML, JSON y shell se verificó. **Pendiente de validar en la nube:** Dockerfile (no hay Docker local), Jenkinsfile, Prometheus/Grafana y scripts de VM |
| 2 | 2026-11-25 | Pruebas / demo de Sonar | Preparar un fallo controlado del Quality Gate | Observación propia: borrar pruebas solo baja la cobertura a 82 % (las líneas de importación cuentan) | Se cambió la estrategia de la demo: `infra/demo-sonar-falla.sh` agrega un módulo grande sin pruebas (cobertura ≈ 30 %) |
| 3 | 2026-11-25 | Azure (fase 1) | Revisar la VM de LAB-03 y crear VM-TOOLS, NSG y autoapagado | Diagnóstico de solo lectura y luego comandos `az` ejecutados tras la confirmación de Diego | **Corregido:** B4ms no estaba disponible y se cambió a B4as_v2; la regla SSH abierta a `*` se restringió; `az vm auto-shutdown` falló por la política de regiones (grupo de recursos en centralus), así que se usó otra vía. **Detectado:** MicroK8s es v1.35.6, por lo que la versión de `kubectl` del script (v1.31.4) quedaba fuera de soporte y se actualizó; el script de VM-K8S revisaba la plantilla del certificado y no el certificado real, y se corrigió |
| 4 | 2026-11-25 | Autoapagado de las VMs | Resolver que el autoapagado nativo no funciona en mexicocentral | Diagnóstico de los tres errores de Azure y una alternativa: cron en VM-TOOLS con identidad administrada y `az vm deallocate` | **Validado:** la identidad lee el estado de ambas VMs y sus permisos efectivos incluyen `Microsoft.Compute/virtualMachines/*`. **No probado:** el apagado real a las 05:00 UTC; revisar `/var/log/medisur-autoapagado.log` al día siguiente |

<!-- Agregar una fila por cada uso relevante posterior (errores del pipeline, ajustes de PromQL, etc.). Anotar también lo que la IA hizo MAL y cómo se detectó. -->
