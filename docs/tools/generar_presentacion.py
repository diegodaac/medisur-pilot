#!/usr/bin/env python3
"""Genera la presentación de la defensa (PPTX 16:9) con el guion en las notas del orador.

Concepto visual: "la línea de entrega". El recorrido de un cambio se dibuja como una
línea de metro; la misma línea corre al pie de cada diapositiva y marca la sección actual.

Uso:  python3 docs/tools/generar_presentacion.py . entrega/MediSur_Presentacion.pptx
"""

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

REPO = Path(sys.argv[1])
SALIDA = Path(sys.argv[2])
CAP = REPO / "entrega" / "capturas"

PAPEL = RGBColor(0xEE, 0xF4, 0xF1)
TINTA = RGBColor(0x16, 0x26, 0x2B)
VERDE = RGBColor(0x2F, 0x7D, 0x6B)
BATA = RGBColor(0x1E, 0x4D, 0x44)
AMBAR = RGBColor(0xE3, 0xA1, 0x3A)
ROJO = RGBColor(0xC8, 0x41, 0x3A)
GRIS = RGBColor(0x5E, 0x6E, 0x73)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
VERDE_CLARO = RGBColor(0xA9, 0xD3, 0xC6)

TITULO = "Barlow Condensed"
TEXTO = "Barlow"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
VACIO = prs.slide_layouts[6]
W = 13.333

SECCIONES = ["Problema", "Arquitectura", "Herramientas", "Pipeline", "Demo", "Evidencia", "IA y costos", "Cierre"]


def fondo(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def texto(slide, x, y, w, h, contenido, tam=18, color=TINTA, fuente=TEXTO, negrita=False,
          alineacion=PP_ALIGN.LEFT, ancla=MSO_ANCHOR.TOP, interlineado=1.15):
    """contenido: str o lista de líneas; una línea puede ser (texto, {opciones})."""
    caja = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = caja.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = ancla
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    lineas = contenido if isinstance(contenido, list) else [contenido]
    for i, linea in enumerate(lineas):
        opts = {}
        if isinstance(linea, tuple):
            linea, opts = linea
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = opts.get("alineacion", alineacion)
        p.line_spacing = opts.get("interlineado", interlineado)
        p.space_after = Pt(opts.get("despues", 6))
        r = p.add_run()
        r.text = linea
        f = r.font
        f.name = opts.get("fuente", fuente)
        f.size = Pt(opts.get("tam", tam))
        f.bold = opts.get("negrita", negrita)
        f.color.rgb = opts.get("color", color)
    return caja


def linea(slide, x1, y1, x2, y2, color=VERDE, grosor=6):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(grosor)
    return c


def estacion(slide, x, y, d=0.26, relleno=PAPEL, borde=VERDE, grosor=4):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x - d / 2), Inches(y - d / 2), Inches(d), Inches(d))
    s.fill.solid()
    s.fill.fore_color.rgb = relleno
    s.line.color.rgb = borde
    s.line.width = Pt(grosor)
    return s


def rect(slide, x, y, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    return s


def linea_de_seccion(slide, actual, oscuro=False):
    """La línea de metro al pie: una estación por sección de la charla."""
    y = 7.02
    x0, x1 = 0.75, W - 0.75
    color_base = VERDE_CLARO if oscuro else RGBColor(0xC9, 0xDB, 0xD4)
    linea(slide, x0, y, x1, y, color_base, 4)
    paso = (x1 - x0) / (len(SECCIONES) - 1)
    idx = SECCIONES.index(actual)
    linea(slide, x0, y, x0 + paso * idx, y, VERDE_CLARO if oscuro else VERDE, 4)
    for i, nombre in enumerate(SECCIONES):
        x = x0 + paso * i
        hecho = i <= idx
        estacion(slide, x, y, 0.16 if i != idx else 0.24,
                 relleno=(VERDE if not oscuro else VERDE_CLARO) if i == idx else (PAPEL if not oscuro else BATA),
                 borde=(VERDE if not oscuro else VERDE_CLARO) if hecho else color_base, grosor=2.5)
        if i == idx:
            texto(slide, x - 1.0, y - 0.46, 2.0, 0.3, nombre, tam=12, negrita=True,
                  color=VERDE_CLARO if oscuro else VERDE, fuente=TITULO, alineacion=PP_ALIGN.CENTER)


def titulo(slide, t, sub=None, color=TINTA):
    texto(slide, 0.75, 0.55, 11.8, 0.9, t, tam=40, negrita=True, fuente=TITULO, color=color, interlineado=1.0)
    if sub:
        texto(slide, 0.75, 1.38, 11.8, 0.5, sub, tam=18, color=GRIS if color == TINTA else VERDE_CLARO)


def imagen(slide, nombre, x, y, w=None, h=None, borde=True):
    ruta = CAP / nombre if not Path(nombre).is_absolute() else Path(nombre)
    if not ruta.exists():
        rect(slide, x, y, w or 4, h or 2.3, RGBColor(0xDD, 0xE7, 0xE3))
        texto(slide, x, y + (h or 2.3) / 2 - 0.2, w or 4, 0.4, f"[falta {ruta.name}]", tam=12, color=GRIS,
              alineacion=PP_ALIGN.CENTER)
        return None
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    pic = slide.shapes.add_picture(str(ruta), Inches(x), Inches(y), **kw)
    if borde:
        pic.line.color.rgb = RGBColor(0xC9, 0xDB, 0xD4)
        pic.line.width = Pt(1)
    return pic


def pie(slide, x, y, w, t):
    texto(slide, x, y, w, 0.4, t, tam=12, color=GRIS)


def notas(slide, guion):
    slide.notes_slide.notes_text_frame.text = guion.strip()


diapositivas = []


def nueva(color=PAPEL):
    s = prs.slides.add_slide(VACIO)
    fondo(s, color)
    diapositivas.append(s)
    return s


# ---------------------------------------------------------------- 1. Portada
s = nueva(BATA)
texto(s, 0.75, 0.7, 9, 0.4, "Cómputo en la Nube · Trabajo final", tam=16, color=VERDE_CLARO)
texto(s, 0.75, 1.25, 11.5, 2.2, "Del commit a producción,\nsin tocar el servidor", tam=66, negrita=True,
      fuente=TITULO, color=BLANCO, interlineado=0.95)
texto(s, 0.75, 3.45, 11, 0.5, "Piloto de entrega continua sobre Kubernetes para MediSur, S.A. de C.V.", tam=22,
      color=VERDE_CLARO)
# La línea de entrega, en grande
estaciones = ["push", "pruebas", "calidad", "imagen", "clúster", "vigilancia"]
x0, x1, y = 0.95, 12.4, 5.05
linea(s, x0, y, x1, y, VERDE_CLARO, 10)
for i, e in enumerate(estaciones):
    x = x0 + (x1 - x0) / (len(estaciones) - 1) * i
    estacion(s, x, y, 0.42, relleno=BATA, borde=BLANCO, grosor=5)
    texto(s, x - 0.9, y + 0.32, 1.8, 0.4, e, tam=18, color=BLANCO, fuente=TITULO, negrita=True,
          alineacion=PP_ALIGN.CENTER)
texto(s, 0.75, 6.45, 12, 0.6, [
    ("Diego Alejandro Alvarado Castañón   |   Prof. Jorge Alberto Islas Pineda   |   UANL FCFM   |   25 de noviembre de 2026",
     {"tam": 14, "color": VERDE_CLARO}),
])
notas(s, """
[0:00 – 0:30]
Buenas tardes. Soy Diego Alvarado y les presento el piloto de entrega continua que construí para MediSur.
La idea cabe en el título: que un cambio en el código llegue a producción sin que nadie entre al servidor.
La línea que ven abajo es el recorrido de cada cambio: push, pruebas, calidad, imagen, clúster y vigilancia. Esa misma línea va a acompañar toda la presentación al pie de cada diapositiva.
""")

# ---------------------------------------------------------------- 2. Problema y objetivo
s = nueva()
titulo(s, "El problema: desplegar a mano no escala")
col = [
    ("Hoy, en MediSur", {"tam": 22, "negrita": True, "fuente": TITULO, "color": ROJO, "despues": 10}),
    ("Cada versión se compila, copia y reinicia a mano: es lento y cada vez sale distinto.", {}),
    ("No hay registro de qué versión corre en producción.", {}),
    ("Nada impide publicar código sin pruebas o con defectos graves.", {}),
    ("Los problemas se descubren cuando ya afectan a los usuarios.", {}),
]
texto(s, 0.75, 2.05, 5.6, 4.2, col, tam=19)
rect(s, 6.85, 2.1, 0.06, 3.9, VERDE)
obj = [
    ("El objetivo del piloto", {"tam": 22, "negrita": True, "fuente": TITULO, "color": VERDE, "despues": 10}),
    ("Que cada cambio pase solo por pruebas, análisis de calidad, imagen y despliegue en Kubernetes, y que el sistema sea observable.", {}),
    ("Lo que se evalúa es la automatización, no la aplicación: por eso la API es sencilla y el esfuerzo está en el proceso.", {"color": GRIS}),
]
texto(s, 7.2, 2.05, 5.4, 4.2, obj, tam=19)
linea_de_seccion(s, "Problema")
notas(s, """
[0:30 – 2:00]
MediSur, el caso del curso, despliega su software a mano. Eso tiene cuatro problemas: es lento, no se puede repetir igual, nadie sabe con certeza qué versión está en producción y no hay ninguna barrera que impida publicar código sin pruebas.
El objetivo del piloto es que cada cambio recorra solo un camino fijo: pruebas, análisis de calidad, construcción de la imagen y despliegue en Kubernetes, con monitoreo y alertas.
Importante: lo que se evalúa es la automatización. Por eso la aplicación es una API pequeña de inventario de insumos, y el trabajo fuerte está en el pipeline, el despliegue y la observabilidad.
""")

# ---------------------------------------------------------------- 3. Arquitectura
s = nueva()
titulo(s, "Dos máquinas, dos responsabilidades",
       "VM-TOOLS construye, analiza y vigila. VM-K8S solo ejecuta la aplicación.")
imagen(s, REPO / "docs" / "arquitectura.png", 0.75, 2.0, h=4.45, borde=False)
texto(s, 8.0, 2.15, 4.6, 4.4, [
    ("VM-TOOLS", {"tam": 20, "negrita": True, "fuente": TITULO, "color": VERDE}),
    ("B4as_v2 · 4 vCPU · 16 GB", {"tam": 14, "color": GRIS}),
    ("Jenkins, SonarQube, Docker, Prometheus, Grafana y Alertmanager.", {"despues": 16}),
    ("VM-K8S", {"tam": 20, "negrita": True, "fuente": TITULO, "color": VERDE}),
    ("B2as_v2 · 2 vCPU · 8 GB", {"tam": 14, "color": GRIS}),
    ("MicroK8s 1.35 con RBAC, la API (2 réplicas), kube-state-metrics y node_exporter.", {"despues": 16}),
    ("Misma VNet en mexicocentral; los firewalls solo abren lo necesario y desde mi IP.", {"color": GRIS, "tam": 15}),
], tam=16)
linea_de_seccion(s, "Arquitectura")
notas(s, """
[2:00 – 5:00]
La arquitectura tiene dos máquinas virtuales en Azure, separadas como pide el enunciado.
VM-TOOLS construye, analiza y vigila: ahí corren Jenkins, SonarQube, Docker y todo el monitoreo. Prometheus está aquí, fuera del clúster.
VM-K8S solo ejecuta: MicroK8s con la aplicación en dos réplicas, más los exportadores de métricas.
En el diagrama, las flechas azules son la entrega continua: GitHub avisa a Jenkins por webhook, Jenkins analiza con SonarQube, construye la imagen, la publica en GitHub Container Registry y, solo en main, actualiza el clúster con kubectl.
Las flechas naranjas son la observabilidad: Prometheus lee métricas de las dos VMs, del clúster y de cada pod, y Alertmanager avisa a Discord.
Las dos VMs están en la misma red virtual; los firewalls solo abren los puertos necesarios y solo desde mi IP, más los rangos de webhooks de GitHub para Jenkins.
""")

# ---------------------------------------------------------------- 4. Herramientas
s = nueva()
titulo(s, "Una herramienta por trabajo", "Cada una con su versión exacta en el inventario del documento.")
grupos = [
    ("Construir", ["Jenkins 2.580.3", "Docker 29", "Jenkinsfile en el repo"]),
    ("Analizar", ["SonarQube 10.7", "Hadolint", "gitleaks", "Trivy"]),
    ("Publicar", ["GitHub", "GHCR", "Etiqueta <versión>-<sha>"]),
    ("Ejecutar", ["MicroK8s 1.35", "2 réplicas", "RollingUpdate"]),
    ("Vigilar", ["Prometheus", "Grafana", "Alertmanager → Discord"]),
]
ancho = (W - 1.5 - 0.4 * 4) / 5
for i, (g, items) in enumerate(grupos):
    x = 0.75 + i * (ancho + 0.4)
    rect(s, x, 2.3, ancho, 0.07, VERDE)
    texto(s, x, 2.5, ancho, 0.5, g, tam=24, negrita=True, fuente=TITULO, color=VERDE)
    texto(s, x, 3.15, ancho, 3.2, [(it, {"despues": 10}) for it in items], tam=18)
linea_de_seccion(s, "Herramientas")
notas(s, """
[5:00 – 7:00]
Elegí una herramienta por trabajo.
Para construir: Jenkins con un Multibranch Pipeline; el pipeline vive en el Jenkinsfile del repositorio, no configurado a clics.
Para analizar: SonarQube con un Quality Gate propio, y como extras de seguridad Hadolint para el Dockerfile, gitleaks para buscar secretos en todo el historial y Trivy para escanear la imagen.
Para publicar: GitHub y su registro de contenedores; cada imagen se etiqueta con la versión y el SHA del commit, nunca con latest.
Para ejecutar: MicroK8s con dos réplicas y actualización gradual.
Y para vigilar: Prometheus, Grafana y Alertmanager con notificaciones a Discord.
""")

# ---------------------------------------------------------------- 5. Pipeline
s = nueva()
titulo(s, "El recorrido de un cambio", "Si una estación falla, el tren se detiene: nada llega a Kubernetes.")
paradas = [
    ("Checkout", "SHA y versión", VERDE),
    ("Seguridad", "Hadolint + gitleaks", VERDE),
    ("Pruebas", "33 pruebas, cobertura", VERDE),
    ("SonarQube", "análisis", VERDE),
    ("Quality Gate", "cobertura ≥ 60 %, A en\nconfiabilidad y seguridad", AMBAR),
    ("Imagen", "build + Trivy", VERDE),
    ("GHCR", "push con SHA", VERDE),
]
x0, x1, y = 0.95, 12.4, 3.25
linea(s, x0, y, x1, y, VERDE, 9)
paso = (x1 - x0) / (len(paradas) - 1)
for i, (n, d, c) in enumerate(paradas):
    x = x0 + paso * i
    estacion(s, x, y, 0.42 if c == AMBAR else 0.34, relleno=AMBAR if c == AMBAR else PAPEL, borde=c if c == AMBAR else VERDE, grosor=5)
    texto(s, x - 0.95, y - 0.85, 1.9, 0.4, n, tam=18, negrita=True, fuente=TITULO, color=TINTA, alineacion=PP_ALIGN.CENTER)
    texto(s, x - 0.95, y + 0.32, 1.9, 0.8, d, tam=13, color=GRIS, alineacion=PP_ALIGN.CENTER)
# Ramal de CD: solo main
xr = x0 + paso * 6
linea(s, xr, y, xr, 5.0, BATA, 9)
linea(s, xr, 5.0, 4.0, 5.0, BATA, 9)
for i, (n, d) in enumerate([("Deploy", "set image + rollout"), ("Humo", "/health y SHA en /version"), ("Rollback", "si falla: rollout undo")]):
    x = xr - 2.75 * (i + 1) + 0.25 if i else xr - 2.5
    x = [xr - 2.3, xr - 5.0, 4.0][i]
    estacion(s, x, 5.0, 0.34, relleno=PAPEL, borde=BATA if i < 2 else ROJO, grosor=5)
    texto(s, x - 1.1, 5.25, 2.2, 0.4, n, tam=18, negrita=True, fuente=TITULO, color=TINTA, alineacion=PP_ALIGN.CENTER)
    texto(s, x - 1.1, 5.62, 2.2, 0.5, d, tam=13, color=GRIS, alineacion=PP_ALIGN.CENTER)
texto(s, xr + 0.25, 4.35, 1.6, 0.6, "solo en main", tam=14, negrita=True, color=BATA)
texto(s, 0.75, 4.55, 2.6, 1.4, [("Todas las ramas y PR", {"negrita": True, "color": VERDE}),
                               ("CI completa; el check de Jenkins es obligatorio para fusionar a main.", {"color": GRIS, "tam": 14})], tam=15)
linea_de_seccion(s, "Pipeline")
notas(s, """
[7:00 – 8:00]
Así recorre el pipeline un cambio. En cualquier rama o Pull Request: checkout con el SHA exacto, revisiones de seguridad en paralelo, las 33 pruebas con cobertura, análisis en SonarQube y la estación clave, el Quality Gate en ámbar: si la cobertura baja de 60 % o hay problemas de confiabilidad o seguridad, el build se detiene de verdad. Después se construye la imagen, Trivy la escanea y se publica en GHCR con la etiqueta del SHA.
Solo en main sigue el ramal de abajo: Jenkins actualiza el Deployment, espera el rollout con tiempo límite y hace una prueba de humo que compara el SHA de /version con el que acaba de construir. Si algo falla, el bloque post hace rollout undo automáticamente.
Y en GitHub, main está protegida: no se puede fusionar un PR sin el check de Jenkins en verde.
""")

# ---------------------------------------------------------------- 6. Seguridad
s = nueva()
titulo(s, "Seguridad del proceso", "Ningún secreto en el repositorio; permisos mínimos donde se pudo comprobar.")
items = [
    ("Secretos fuera del repo", "Tokens, PAT, kubeconfig y webhook viven en Jenkins Credentials o en archivos ignorados por git."),
    ("gitleaks en cada build", "Revisa todo el historial. Detuvo un build por un comentario mío que citaba un patrón de credencial."),
    ("Trivy antes de publicar", "Encontró un CVE real en starlette; se actualizó FastAPI antes de desplegar."),
    ("RBAC activado", "MicroK8s lo tenía apagado. Ahora el ServiceAccount de Prometheus recibe 403 si intenta escribir."),
    ("main protegida", "Solo por Pull Request y con el check de Jenkins en verde."),
    ("Un token expuesto, rotado", "Se pegó por error en un chat: se revocó y quedó documentado."),
]
for i, (t, d) in enumerate(items):
    colx = 0.75 + (i % 2) * 6.1
    fila = 2.15 + (i // 2) * 1.5
    rect(s, colx, fila + 0.08, 0.07, 1.05, AMBAR if i in (1, 3) else VERDE)
    texto(s, colx + 0.25, fila, 5.6, 1.4, [(t, {"tam": 20, "negrita": True, "fuente": TITULO, "despues": 4}),
                                          (d, {"tam": 15, "color": GRIS})], tam=15)
linea_de_seccion(s, "Pipeline")
notas(s, """
[8:00 – 9:00]
La seguridad del proceso descansa en seis cosas.
Ningún secreto vive en el repositorio: todo está en Jenkins Credentials o en archivos ignorados por git.
gitleaks revisa todo el historial en cada build; de hecho detuvo un build por un comentario que yo había escrito citando un patrón de credencial, y eso demuestra que la puerta funciona.
Trivy escanea la imagen antes de publicarla y encontró una vulnerabilidad real en starlette, que corregí actualizando FastAPI.
Descubrí que MicroK8s tenía RBAC desactivado, así que el ServiceAccount "de solo lectura" no lo era; lo activé y verifiqué que Prometheus recibe 403 al intentar escribir.
main solo acepta Pull Requests con el check en verde. Y el único token que se expuso, se rotó y se documentó, como pide el enunciado.
""")

# ---------------------------------------------------------------- 7. Demo
s = nueva(BATA)
texto(s, 0.75, 0.55, 11, 0.9, "Demo en vivo", tam=44, negrita=True, fuente=TITULO, color=BLANCO)
texto(s, 0.75, 1.35, 11, 0.5, "Todo desde la laptop. Nadie se conecta por SSH al clúster.", tam=18, color=VERDE_CLARO)
pasos = [
    ("curl /version", "anotar el SHA actual"),
    ("Cambio en rama + PR", "demo-sonar-falla.sh"),
    ("Jenkins arranca solo", "webhook de GitHub"),
    ("Fallo a propósito", "el Quality Gate detiene el build"),
    ("Corregir y fusionar", "pipeline en verde"),
    ("Imagen nueva en GHCR", "etiqueta con el SHA"),
    ("kubectl get pods -w", "actualización gradual"),
    ("curl /version", "SHA nuevo, sin SSH"),
    ("kubectl delete pod", "con Grafana en pantalla"),
    ("kubectl rollout undo", "vuelve la versión anterior"),
]
clave = {4, 8, 9, 10}
for i, (p, d) in enumerate(pasos, start=1):
    colx = 0.75 + ((i - 1) // 5) * 6.1
    fila = 2.2 + ((i - 1) % 5) * 0.88
    estacion(s, colx + 0.25, fila + 0.27, 0.46, relleno=AMBAR if i in clave else BATA, borde=AMBAR if i in clave else VERDE_CLARO, grosor=3)
    texto(s, colx, fila + 0.07, 0.5, 0.4, str(i), tam=16, negrita=True, fuente=TITULO,
          color=TINTA if i in clave else BLANCO, alineacion=PP_ALIGN.CENTER)
    texto(s, colx + 0.7, fila, 5.2, 0.8, [(p, {"tam": 20, "negrita": True, "fuente": TITULO, "color": BLANCO, "despues": 0}),
                                         (d, {"tam": 14, "color": VERDE_CLARO})], tam=14)
texto(s, 0.75, 6.45, 6, 0.35, "En ámbar: los pasos que definen la calificación.", tam=14, color=AMBAR)
linea_de_seccion(s, "Demo", oscuro=True)
notas(s, """
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
""")

# ---------------------------------------------------------------- 8. Evidencia: fallo
s = nueva()
titulo(s, "El fallo a propósito: la imagen nunca se construye", "PR #4 con un módulo sin pruebas: cobertura de 30.2 %.")
imagen(s, "04-jenkins-pr4-rojo.png", 0.75, 2.0, w=6.0)
imagen(s, "04b-github-pr4-bloqueado.png", 6.95, 2.0, w=5.65)
pie(s, 0.75, 5.5, 6.0, "Jenkins: ❌ en Quality Gate; Docker build, push y despliegue saltados.")
pie(s, 6.95, 5.3, 5.65, "GitHub: el check requerido falló; el PR no se puede fusionar.")
linea_de_seccion(s, "Evidencia")
notas(s, """
[Respaldo de la demo, paso 4 — 30 s si la demo en vivo funcionó]
Esta es la evidencia del fallo a propósito. A la izquierda, Jenkins: la etapa Quality Gate en rojo con el mensaje "Pipeline aborted due to quality gate failure", y todas las etapas siguientes saltadas. No se construyó imagen y no se tocó Kubernetes.
A la derecha, GitHub: el check de Jenkins es obligatorio y falló, así que el botón de fusionar está bloqueado. Un cambio malo no puede llegar a main ni por error.
""")

# ---------------------------------------------------------------- 9. Evidencia: verde
s = nueva()
titulo(s, "Un merge cambia producción sin SSH", "El build de main corre todas las estaciones y despliega solo.")
imagen(s, "06-jenkins-main-verde.png", 0.75, 2.0, w=6.6)
imagen(s, "10-rolling-update-pods-w.png", 7.6, 2.0, h=3.9)
pie(s, 0.75, 5.85, 6.6, "Jenkins: las 13 etapas en verde, de Checkout a Prueba de humo.")
pie(s, 7.6, 5.95, 5.0, "kubectl get pods -w: siempre dos pods listos.")
linea_de_seccion(s, "Evidencia")
notas(s, """
[Respaldo, pasos 5 a 8 — 30 s]
Cuando el PR se fusiona, el build de main recorre todas las estaciones: seguridad, pruebas, Quality Gate, imagen, Trivy, push, despliegue y prueba de humo.
A la derecha, la actualización gradual vista con kubectl: cada pod nuevo pasa unos 16 segundos en 0/1, por el retardo de /ready, y solo entonces se retira uno viejo. La estrategia es maxUnavailable 0 y maxSurge 1, así que nunca hay menos de dos pods atendiendo.
""")

# ---------------------------------------------------------------- 10. Autocuración
s = nueva()
titulo(s, "Autocuración y reversión", "Kubernetes repone lo que se cae; la versión anterior está a un comando.")
imagen(s, "13-grafana-caos.png", 0.75, 2.0, w=6.6)
texto(s, 7.75, 2.1, 4.85, 4.2, [
    ("22 s", {"tam": 54, "negrita": True, "fuente": TITULO, "color": VERDE, "despues": 0, "interlineado": 0.9}),
    ("para volver a 2/2 tras kubectl delete pod; el servicio respondió 200 todo el tiempo.", {"tam": 16, "color": GRIS, "despues": 16}),
    ("7 reinicios", {"tam": 30, "negrita": True, "fuente": TITULO, "color": TINTA, "despues": 0}),
    ("en el experimento de caos: el pod se recuperó sin intervención.", {"tam": 16, "color": GRIS, "despues": 16}),
    ("rollout undo", {"tam": 30, "negrita": True, "fuente": TITULO, "color": TINTA, "despues": 0}),
    ("devuelve la versión anterior y /version lo confirma.", {"tam": 16, "color": GRIS}),
], tam=16)
pie(s, 0.75, 5.85, 6.6, "Grafana: réplicas listas 2 → 1 → 2 durante el experimento de caos.")
linea_de_seccion(s, "Evidencia")
notas(s, """
[Respaldo, pasos 9 y 10 — 45 s]
Esta gráfica es el tablero de Grafana durante un experimento de caos: detuve el proceso de un pod cada vez que intentaba arrancar. Las réplicas listas bajaron de 2 a 1, el otro pod siguió atendiendo y, al terminar, Kubernetes recuperó el pod solo, después de siete reinicios.
Con un kubectl delete pod normal, el Deployment vuelve a 2/2 en unos 22 segundos y el servicio nunca deja de responder.
Y la reversión es un comando: kubectl rollout undo devuelve la versión anterior, y /version lo confirma.
""")

# ---------------------------------------------------------------- 11. Monitoreo
s = nueva()
titulo(s, "Monitoreo con datos reales", "Dos tableros, 13 destinos en UP y tres alertas probadas en Discord.")
imagen(s, "12-grafana-app.png", 0.75, 2.0, w=6.1)
imagen(s, "15b-grafana-alertas-disparadas.png", 7.05, 2.0, w=5.55)
pie(s, 0.75, 5.55, 6.1, "Tablero Aplicación: versión desplegada, réplicas, 5xx, peticiones por segundo y latencia p95.")
pie(s, 7.05, 5.3, 5.55, "Las cuatro alertas disparadas en la prueba controlada.")
linea_de_seccion(s, "Evidencia")
notas(s, """
[19:00 – 20:00 aprox.]
Dos tableros con datos reales. El de infraestructura muestra las dos VMs lado a lado: CPU, memoria, disco, red, estado de los servicios y tiempo encendido. El de aplicación, a la izquierda, muestra la versión desplegada, réplicas listas contra deseadas, tasa de errores 5xx, peticiones por segundo, latencia p95 y CPU y memoria por pod.
Las tres alertas obligatorias se probaron con fallas controladas, sin tocar el despliegue: llené el disco al 85 % para DiscoLleno, y el experimento de caos provocó PodReiniciandose y ReplicasNoDisponibles. Todas llegaron a Discord, con su aviso de resolución.
Un detalle de diseño: las métricas se leen pod por pod a través del API server, no por el Service; con dos réplicas, leerlas por el Service mezclaría los contadores.
""")

# ---------------------------------------------------------------- 12. IA
s = nueva()
titulo(s, "Uso de inteligencia artificial", "Claude Code como asistente de ingeniería. Ninguna salida se aceptó sin verificarla.")
texto(s, 0.75, 2.15, 5.6, 4.2, [
    ("Para qué se usó", {"tam": 22, "negrita": True, "fuente": TITULO, "color": VERDE, "despues": 10}),
    ("Generar el andamiaje: app, pruebas, Dockerfile, manifiestos, Jenkinsfile y monitoreo.", {}),
    ("Ejecutar y diagnosticar la instalación en las VMs.", {}),
    ("Cada cambio en Azure se confirmó antes; los secretos los escribí yo, nunca la IA.", {"color": GRIS}),
], tam=18)
rect(s, 6.85, 2.2, 0.06, 3.8, AMBAR)
texto(s, 7.2, 2.15, 5.4, 4.3, [
    ("Lo que la IA hizo mal y se corrigió", {"tam": 22, "negrita": True, "fuente": TITULO, "color": TINTA, "despues": 10}),
    ("Versiones viejas: la llave de Jenkins había caducado, Jenkins 2.580 exige Java 21 y kube-state-metrics debía coincidir con Kubernetes 1.35.", {}),
    ("Supuso que el ServiceAccount era de solo lectura; al verificarlo, RBAC estaba apagado.", {}),
    ("Escribió un comentario que disparó gitleaks: la puerta lo detuvo.", {}),
], tam=17)
linea_de_seccion(s, "IA y costos")
notas(s, """
[20:00 – 21:30]
Usé Claude Code como asistente de ingeniería y está declarado con detalle en el documento.
Me ayudó a generar el andamiaje y a ejecutar y diagnosticar la instalación. Dos reglas no se rompieron: cada cambio en Azure lo confirmé antes de ejecutarse, y las contraseñas y tokens los escribí yo directamente en la VM o en Jenkins.
Lo más valioso fueron sus errores, porque cada uno se detectó al ejecutar y medir: versiones que en 2026 ya no eran válidas, el supuesto de que el ServiceAccount era de solo lectura cuando RBAC estaba apagado, y un comentario suyo que gitleaks detectó como posible credencial.
Puedo explicar cada línea del Jenkinsfile y de los manifiestos, porque cada pieza se probó y se corrigió durante la instalación.
""")

# ---------------------------------------------------------------- 13. Costos
s = nueva()
titulo(s, "Control de costos")
texto(s, 0.75, 1.75, 5.5, 3.0, [
    ("5.15 USD", {"tam": 80, "negrita": True, "fuente": TITULO, "color": VERDE, "despues": 0, "interlineado": 0.9}),
    ("consumidos del crédito de 100 USD de Azure for Students al 25 de noviembre (el cómputo de las VMs se refleja con retraso).", {"tam": 17, "color": GRIS}),
], tam=17)
texto(s, 7.0, 1.95, 5.6, 4.5, [
    ("Presupuesto de 50 USD con avisos al 80 %, 100 % y por pronóstico.", {"despues": 12}),
    ("Apagado diario a las 23:00 con deallocate. El nativo de Azure no existe en mexicocentral: lo hace un cron con identidad administrada.", {"despues": 12}),
    ("Prometheus con retención de 15 días; tamaños B y discos StandardSSD.", {"despues": 12}),
    ("Al terminar el curso se borra el grupo de recursos.", {}),
], tam=18)
linea_de_seccion(s, "IA y costos")
notas(s, """
[21:30 – 22:00]
En costos: llevo 5.15 dólares consumidos del crédito de 100; el cómputo de las VMs aparece en Azure con hasta un día de retraso.
Hay un presupuesto de 50 dólares con avisos al 80 y al 100 por ciento y por pronóstico. Las VMs se apagan cada noche a las 23:00 con deallocate; como el autoapagado nativo de Azure no existe en mexicocentral, lo implementé con un cron en VM-TOOLS que usa una identidad administrada con permisos solo sobre el grupo de recursos. Al terminar el curso borro todo el grupo.
""")

# ---------------------------------------------------------------- 14. Cierre
s = nueva(BATA)
texto(s, 0.75, 0.7, 11, 0.9, "Lo que me llevo", tam=44, negrita=True, fuente=TITULO, color=BLANCO)
lecciones = [
    "Verificar contra el sistema real, no contra la memoria: varias versiones conocidas ya no servían.",
    "Un requisito de seguridad solo cuenta si se comprueba.",
    "Las puertas automáticas atrapan errores humanos y de la IA.",
]
texto(s, 0.75, 1.8, 11.5, 2.6, [(l, {"despues": 14}) for l in lecciones], tam=24, color=BLANCO)
texto(s, 0.75, 4.55, 11.5, 1.0, "Preguntas", tam=60, negrita=True, fuente=TITULO, color=VERDE_CLARO)
texto(s, 0.75, 5.75, 11.5, 0.5, "github.com/diegodaac/medisur-pilot", tam=18, color=BLANCO)
linea_de_seccion(s, "Cierre", oscuro=True)
notas(s, """
[22:00 – 22:30, luego 5 minutos de preguntas]
Me llevo tres lecciones. Primero, verificar contra el sistema real y no contra la memoria: varias versiones que "todos conocen" ya no servían en 2026. Segundo, un requisito de seguridad solo cuenta si se comprueba; el RBAC apagado lo demostró. Y tercero, las puertas automáticas atrapan errores, tanto humanos como de la IA.
El código, el Jenkinsfile, los manifiestos y la configuración del monitoreo están en el repositorio. Muchas gracias; quedo atento a sus preguntas.
""")

prs.save(SALIDA)
print(f"escrita {SALIDA} con {len(prs.slides)} diapositivas")
