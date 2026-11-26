# Guion de la presentación y del video

Duración objetivo: unos 20 minutos de exposición más 5 de preguntas, la estructura que sugiere el enunciado (problema y solución 2, arquitectura 3, herramientas 2, demo 10, IA y lecciones 2, costos 1).

El mismo texto está en las notas del orador de la presentación (Canva y PowerPoint). Las diapositivas 8 a 11 son el respaldo de la demo: si la demo en vivo funcionó, se pasan en unos 30 segundos cada una; en el video sirven para narrar la evidencia.

## 1. Portada

[0:00 – 0:30]
Buenas tardes. Soy Diego Alvarado y les presento el piloto de entrega continua que construí para MediSur.
La idea cabe en el título: que un cambio en el código llegue a producción sin que nadie entre al servidor.
La línea que ven abajo es el recorrido de cada cambio: push, pruebas, calidad, imagen, clúster y vigilancia. Esa misma línea va a acompañar toda la presentación al pie de cada diapositiva.

## 2. El problema: desplegar a mano no escala

[0:30 – 2:00]
MediSur, el caso del curso, despliega su software a mano. Eso tiene cuatro problemas: es lento, no se puede repetir igual, nadie sabe con certeza qué versión está en producción y no hay ninguna barrera que impida publicar código sin pruebas.
El objetivo del piloto es que cada cambio recorra solo un camino fijo: pruebas, análisis de calidad, construcción de la imagen y despliegue en Kubernetes, con monitoreo y alertas.
Importante: lo que se evalúa es la automatización. Por eso la aplicación es una API pequeña de inventario de insumos, y el trabajo fuerte está en el pipeline, el despliegue y la observabilidad.

## 3. Dos máquinas, dos responsabilidades

[2:00 – 5:00]
La arquitectura tiene dos máquinas virtuales en Azure, separadas como pide el enunciado.
VM-TOOLS construye, analiza y vigila: ahí corren Jenkins, SonarQube, Docker y todo el monitoreo. Prometheus está aquí, fuera del clúster.
VM-K8S solo ejecuta: MicroK8s con la aplicación en dos réplicas, más los exportadores de métricas.
En el diagrama, las flechas azules son la entrega continua: GitHub avisa a Jenkins por webhook, Jenkins analiza con SonarQube, construye la imagen, la publica en GitHub Container Registry y, solo en main, actualiza el clúster con kubectl.
Las flechas naranjas son la observabilidad: Prometheus lee métricas de las dos VMs, del clúster y de cada pod, y Alertmanager avisa a Discord.
Las dos VMs están en la misma red virtual; los firewalls solo abren los puertos necesarios y solo desde mi IP, más los rangos de webhooks de GitHub para Jenkins.

## 4. Una herramienta por trabajo

[5:00 – 7:00]
Elegí una herramienta por trabajo.
Para construir: Jenkins con un Multibranch Pipeline; el pipeline vive en el Jenkinsfile del repositorio, no configurado a clics.
Para analizar: SonarQube con un Quality Gate propio, y como extras de seguridad Hadolint para el Dockerfile, gitleaks para buscar secretos en todo el historial y Trivy para escanear la imagen.
Para publicar: GitHub y su registro de contenedores; cada imagen se etiqueta con la versión y el SHA del commit, nunca con latest.
Para ejecutar: MicroK8s con dos réplicas y actualización gradual.
Y para vigilar: Prometheus, Grafana y Alertmanager con notificaciones a Discord.

## 5. El recorrido de un cambio

[7:00 – 8:00]
Así recorre el pipeline un cambio. En cualquier rama o Pull Request: checkout con el SHA exacto, revisiones de seguridad en paralelo, las 33 pruebas con cobertura, análisis en SonarQube y la estación clave, el Quality Gate en ámbar: si la cobertura baja de 60 % o hay problemas de confiabilidad o seguridad, el build se detiene de verdad. Después se construye la imagen, Trivy la escanea y se publica en GHCR con la etiqueta del SHA.
Solo en main sigue el ramal de abajo: Jenkins actualiza el Deployment, espera el rollout con tiempo límite y hace una prueba de humo que compara el SHA de /version con el que acaba de construir. Si algo falla, el bloque post hace rollout undo automáticamente.
Y en GitHub, main está protegida: no se puede fusionar un PR sin el check de Jenkins en verde.

## 6. Seguridad del proceso

[8:00 – 9:00]
La seguridad del proceso descansa en seis cosas.
Ningún secreto vive en el repositorio: todo está en Jenkins Credentials o en archivos ignorados por git.
gitleaks revisa todo el historial en cada build; de hecho detuvo un build por un comentario que yo había escrito citando un patrón de credencial, y eso demuestra que la puerta funciona.
Trivy escanea la imagen antes de publicarla y encontró una vulnerabilidad real en starlette, que corregí actualizando FastAPI.
Descubrí que MicroK8s tenía RBAC desactivado, así que el ServiceAccount "de solo lectura" no lo era; lo activé y verifiqué que Prometheus recibe 403 al intentar escribir.
main solo acepta Pull Requests con el check en verde. Y el único token que se expuso, se rotó y se documentó, como pide el enunciado.

## 7. Demo en vivo

[9:00 – 19:00]  DEMO EN VIVO (10 minutos). Todo desde la laptop, sin SSH al clúster.
1. Terminal: curl -s http://158.23.21.125:30080/version  →  "Este es el SHA que está en producción."
2. ./infra/demo-sonar-falla.sh ; git push -u origin demo/sonar-falla ; gh pr create --fill  →  "Agrego un módulo sin pruebas: la cobertura baja a 30 %."
3. Jenkins: aparece el job PR solo  →  "Nadie toca Jenkins: lo dispara el webhook de GitHub."
4. Esperar la etapa Quality Gate en rojo  →  "SonarQube detiene el build. Docker, push y despliegue aparecen saltados: no hay imagen. En GitHub el PR queda bloqueado."
5. git rm app/calculos_legacy.py ; git commit -m "fix: elimina módulo sin pruebas" ; git push ; con el check verde: gh pr merge --squash --delete-branch  →  "Corrijo, el pipeline pasa a verde y fusiono."
6. GitHub › Packages  →  "Imagen nueva con la versión y el SHA, nunca latest."
7. kubectl get pods -n medisur -w  →  "Cada pod nuevo queda 0/1 unos segundos por el retardo de /ready y solo entonces se retira uno viejo: siempre hay dos listos."
8. curl /version  →  "El SHA cambió y nadie entró a ningún servidor."
9. Grafana (tablero Aplicación) en pantalla ; kubectl delete pod -n medisur <uno>  →  "Las réplicas listas bajan a 1 y vuelven a 2 en unos 20 segundos: el ReplicaSet crea otro pod y la readinessProbe le impide recibir tráfico hasta estar listo."
10. kubectl rollout undo deployment/medisur-api -n medisur ; curl /version  →  "Vuelve la versión anterior."
Si algo falla en vivo: usar las diapositivas siguientes como respaldo y el video.

## 8. El fallo a propósito

[Respaldo de la demo, paso 4 — 30 s si la demo en vivo funcionó]
Esta es la evidencia del fallo a propósito. A la izquierda, Jenkins: la etapa Quality Gate en rojo con el mensaje "Pipeline aborted due to quality gate failure", y todas las etapas siguientes saltadas. No se construyó imagen y no se tocó Kubernetes.
A la derecha, GitHub: el check de Jenkins es obligatorio y falló, así que el botón de fusionar está bloqueado. Un cambio malo no puede llegar a main ni por error.

## 9. Un merge cambia producción sin SSH

[Respaldo, pasos 5 a 8 — 30 s]
Cuando el PR se fusiona, el build de main recorre todas las estaciones: seguridad, pruebas, Quality Gate, imagen, Trivy, push, despliegue y prueba de humo.
A la derecha, la actualización gradual vista con kubectl: cada pod nuevo pasa unos 16 segundos en 0/1, por el retardo de /ready, y solo entonces se retira uno viejo. La estrategia es maxUnavailable 0 y maxSurge 1, así que nunca hay menos de dos pods atendiendo.

## 10. Autocuración y reversión

[Respaldo, pasos 9 y 10 — 45 s]
Esta gráfica es el tablero de Grafana durante un experimento de caos: detuve el proceso de un pod cada vez que intentaba arrancar. Las réplicas listas bajaron de 2 a 1, el otro pod siguió atendiendo y, al terminar, Kubernetes recuperó el pod solo, después de siete reinicios.
Con un kubectl delete pod normal, el Deployment vuelve a 2/2 en unos 22 segundos y el servicio nunca deja de responder.
Y la reversión es un comando: kubectl rollout undo devuelve la versión anterior, y /version lo confirma.

## 11. Monitoreo con datos reales

[19:00 – 20:00 aprox.]
Dos tableros con datos reales. El de infraestructura muestra las dos VMs lado a lado: CPU, memoria, disco, red, estado de los servicios y tiempo encendido. El de aplicación, a la izquierda, muestra la versión desplegada, réplicas listas contra deseadas, tasa de errores 5xx, peticiones por segundo, latencia p95 y CPU y memoria por pod.
Las tres alertas obligatorias se probaron con fallas controladas, sin tocar el despliegue: llené el disco al 85 % para DiscoLleno, y el experimento de caos provocó PodReiniciandose y ReplicasNoDisponibles. Todas llegaron a Discord, con su aviso de resolución.
Un detalle de diseño: las métricas se leen pod por pod a través del API server, no por el Service; con dos réplicas, leerlas por el Service mezclaría los contadores.

## 12. Uso de inteligencia artificial

[20:00 – 21:30]
Usé Claude Code como asistente de ingeniería y está declarado con detalle en el documento.
Me ayudó a generar el andamiaje y a ejecutar y diagnosticar la instalación. Dos reglas no se rompieron: cada cambio en Azure lo confirmé antes de ejecutarse, y las contraseñas y tokens los escribí yo directamente en la VM o en Jenkins.
Lo más valioso fueron sus errores, porque cada uno se detectó al ejecutar y medir: versiones que en 2026 ya no eran válidas, el supuesto de que el ServiceAccount era de solo lectura cuando RBAC estaba apagado, y un comentario suyo que gitleaks detectó como posible credencial.
Puedo explicar cada línea del Jenkinsfile y de los manifiestos, porque cada pieza se probó y se corrigió durante la instalación.

## 13. Control de costos

[21:30 – 22:00]
En costos: llevo 5.15 dólares consumidos del crédito de 100; el cómputo de las VMs aparece en Azure con hasta un día de retraso.
Hay un presupuesto de 50 dólares con avisos al 80 y al 100 por ciento y por pronóstico. Las VMs se apagan cada noche a las 23:00 con deallocate; como el autoapagado nativo de Azure no existe en mexicocentral, lo implementé con un cron en VM-TOOLS que usa una identidad administrada con permisos solo sobre el grupo de recursos. Al terminar el curso borro todo el grupo.

## 14. Lo que me llevo y preguntas

[22:00 – 22:30, luego 5 minutos de preguntas]
Me llevo tres lecciones. Primero, verificar contra el sistema real y no contra la memoria: varias versiones que "todos conocen" ya no servían en 2026. Segundo, un requisito de seguridad solo cuenta si se comprueba; el RBAC apagado lo demostró. Y tercero, las puertas automáticas atrapan errores, tanto humanos como de la IA.
El código, el Jenkinsfile, los manifiestos y la configuración del monitoreo están en el repositorio. Muchas gracias; quedo atento a sus preguntas.

## Para grabar el video de respaldo

- Graba pantalla completa con QuickTime (Archivo › Nueva grabación de pantalla) o el grabador de Canva; incluye audio del micrófono.
- Antes: enciende las VMs, corre `./infra/mi-ip.sh` y `export KUBECONFIG=~/.kube/medisur.yaml`, y deja tráfico con `URL=http://158.23.21.125:30080 ./infra/generar-trafico.sh 1800 &` para que Grafana tenga datos.
- Ten abiertas: la presentación, la terminal, Jenkins, GitHub, SonarQube y Grafana (tablero Aplicación, últimos 15 minutos).
- La rama `demo/sonar-falla` no debe existir antes de empezar (ver `docs/guion-demo.md`).
- Duración: 10 a 15 minutos. Si el tiempo aprieta, recorta las diapositivas 2 a 6 y conserva completa la demo.
