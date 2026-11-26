# Historial reescrito (2026-11-25)

El 25 de noviembre de 2026 se reescribió el historial de `main` para quitar de los mensajes de commit la línea `Co-Authored-By` del asistente de IA. **El contenido de los archivos no cambió** (el diff entre el historial anterior y el nuevo es vacío); solo cambiaron los mensajes y, por lo tanto, los SHA.

El uso de IA sigue declarado en detalle en [`docs/AI_LOG.md`](AI_LOG.md) y en la sección 7 del documento Word.

Algunas capturas, etiquetas de imagen en GHCR, builds de Jenkins y revisiones del Deployment muestran los SHA anteriores. Esta tabla permite rastrearlos:

| SHA anterior | SHA actual | Commit |
|---|---|---|
| `ed5f6b1` | `f120d23` | feat: base del piloto MediSur (app, pipeline, k8s y monitoreo) |
| `447591e` | `7cd2f40` | infra: fase 1 de Azure y autoapagado con identidad administrada |
| `5fccf9f` | `2354829` | ci: fija GHCR_OWNER a diegodaac |
| `51faf38` | `ef9d13b` | fix(infra): instalación de VM-TOOLS (#1) |
| `f2ad68e` | `c83f69f` | fix(sonar): gate idempotente y webhook por IP privada (#2) |
| `9149ea9` | `68857d9` | infra: preparación de VM-K8S, kube-state-metrics y RBAC (#3) |
| `3b5f159` | `fe1e58b` | feat(ci): extras de seguridad Hadolint, gitleaks y Trivy (#5) |
| `985a0a3` | `823ed2f` | monitoring: stack verificado y alertas probadas (#6) |
| `88bcc56` | `ba18fbc` | docs: generador del documento con capturas (#7) |
| `b2ab05b` | `fff9ab9` | infra: presupuesto de 50 USD con avisos (#8) |
| `e1bdff3` | `9bd0737` | docs: nombre del profesor en la portada (#9) |

Ajustes hechos junto con la reescritura:
- `.gitleaksignore` identifica los falsos positivos por SHA de commit; se actualizó a los SHA nuevos para que gitleaks siga en verde.
- Los Pull Requests ya fusionados en GitHub conservan sus commits originales; la reescritura afecta solo a `main`.
- Respaldo completo del historial anterior: `git bundle` guardado fuera del repositorio.
