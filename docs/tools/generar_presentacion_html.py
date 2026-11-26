#!/usr/bin/env python3
"""Versión HTML de la presentación (misma estructura que generar_presentacion.py), pensada
para imprimirse a PDF con Chrome headless y subirse a Canva. El guion se toma de las notas
del PPTX generado, para que haya una sola fuente.

Uso:
  python3 docs/tools/generar_presentacion.py . entrega/MediSur_Presentacion.pptx
  python3 docs/tools/generar_presentacion_html.py . entrega/MediSur_Presentacion.pptx entrega/presentacion.html
"""

import html
import sys
from pathlib import Path

from pptx import Presentation

REPO = Path(sys.argv[1]).resolve()
PPTX = Path(sys.argv[2]).resolve()
SALIDA = Path(sys.argv[3]).resolve()
CAP = REPO / "entrega" / "capturas"

notas = [s.notes_slide.notes_text_frame.text if s.has_notes_slide else "" for s in Presentation(PPTX).slides]
SECCIONES = ["Problema", "Arquitectura", "Herramientas", "Pipeline", "Demo", "Evidencia", "IA y costos", "Cierre"]
e = html.escape


def img(nombre):
    ruta = CAP / nombre if not nombre.startswith("/") else Path(nombre)
    return ruta.as_uri()


def metro(actual, oscuro=False):
    idx = SECCIONES.index(actual)
    n = len(SECCIONES)
    puntos = []
    for i, nombre in enumerate(SECCIONES):
        izq = 60 + (1160 * i / (n - 1))
        clase = "actual" if i == idx else ("hecha" if i < idx else "")
        etiqueta = f'<span class="nombre">{e(nombre)}</span>' if i == idx else ""
        puntos.append(f'<i class="est {clase}" style="left:{izq:.1f}px">{etiqueta}</i>')
    avance = 1160 * idx / (n - 1)
    return (f'<div class="metro{" oscuro" if oscuro else ""}"><b class="via"></b>'
            f'<b class="avance" style="width:{avance:.1f}px"></b>{"".join(puntos)}</div>')


slides = []


def slide(cuerpo, clase="", seccion=None, oscuro=False):
    pie = metro(seccion, oscuro) if seccion else ""
    slides.append(f'<section class="slide {clase}" data-document-role="page">{cuerpo}{pie}</section>')


# 1. Portada
estaciones = "".join(
    f'<div class="p-est" style="left:{60 + 1060 * i / 5:.1f}px"><i></i><span>{n}</span></div>'
    for i, n in enumerate(["push", "pruebas", "calidad", "imagen", "clúster", "vigilancia"]))
slide(f"""
<p class="sobre">Cómputo en la Nube · Trabajo final</p>
<h1 class="portada">Del commit a producción,<br>sin tocar el servidor</h1>
<p class="lema">Piloto de entrega continua sobre Kubernetes para MediSur, S.A. de C.V.</p>
<div class="p-linea"><b></b>{estaciones}</div>
<p class="creditos">Diego Alejandro Alvarado Castañón&emsp;|&emsp;Prof. Jorge Alberto Islas Pineda&emsp;|&emsp;UANL FCFM&emsp;|&emsp;25 de noviembre de 2026</p>
""", "bata")

# 2. Problema
slide("""
<h2>El problema: desplegar a mano no escala</h2>
<div class="dos">
  <div><h3 class="rojo">Hoy, en MediSur</h3>
    <p>Cada versión se compila, copia y reinicia a mano: es lento y cada vez sale distinto.</p>
    <p>No hay registro de qué versión corre en producción.</p>
    <p>Nada impide publicar código sin pruebas o con defectos graves.</p>
    <p>Los problemas se descubren cuando ya afectan a los usuarios.</p></div>
  <div class="regla"><h3>El objetivo del piloto</h3>
    <p>Que cada cambio pase solo por pruebas, análisis de calidad, imagen y despliegue en Kubernetes, y que el sistema sea observable.</p>
    <p class="gris">Lo que se evalúa es la automatización, no la aplicación: por eso la API es sencilla y el esfuerzo está en el proceso.</p></div>
</div>""", seccion="Problema")

# 3. Arquitectura
slide(f"""
<h2>Dos máquinas, dos responsabilidades</h2>
<p class="sub">VM-TOOLS construye, analiza y vigila. VM-K8S solo ejecuta la aplicación.</p>
<div class="arq">
  <img src="{(REPO / 'docs' / 'arquitectura.png').as_uri()}" alt="Diagrama de arquitectura">
  <div class="arq-txt">
    <h3>VM-TOOLS</h3><p class="dato">B4as_v2 · 4 vCPU · 16 GB</p>
    <p>Jenkins, SonarQube, Docker, Prometheus, Grafana y Alertmanager.</p>
    <h3>VM-K8S</h3><p class="dato">B2as_v2 · 2 vCPU · 8 GB</p>
    <p>MicroK8s 1.35 con RBAC, la API (2 réplicas), kube-state-metrics y node_exporter.</p>
    <p class="gris chico">Misma VNet en mexicocentral; los firewalls solo abren lo necesario y desde mi IP.</p>
  </div>
</div>""", seccion="Arquitectura")

# 4. Herramientas
grupos = [("Construir", ["Jenkins 2.580.3", "Docker 29", "Jenkinsfile en el repo"]),
          ("Analizar", ["SonarQube 10.7", "Hadolint", "gitleaks", "Trivy"]),
          ("Publicar", ["GitHub", "GHCR", "Etiqueta &lt;versión&gt;-&lt;sha&gt;"]),
          ("Ejecutar", ["MicroK8s 1.35", "2 réplicas", "RollingUpdate"]),
          ("Vigilar", ["Prometheus", "Grafana", "Alertmanager → Discord"])]
cols = "".join(f'<div class="col"><h3>{g}</h3>{"".join(f"<p>{i}</p>" for i in items)}</div>' for g, items in grupos)
slide(f"""
<h2>Una herramienta por trabajo</h2>
<p class="sub">Cada una con su versión exacta en el inventario del documento.</p>
<div class="cinco">{cols}</div>""", seccion="Herramientas")

# 5. Pipeline
paradas = [("Checkout", "SHA y versión", ""), ("Seguridad", "Hadolint + gitleaks", ""),
           ("Pruebas", "33 pruebas, cobertura", ""), ("SonarQube", "análisis", ""),
           ("Quality Gate", "cobertura ≥ 60 %, A en confiabilidad y seguridad", "gate"),
           ("Imagen", "build + Trivy", ""), ("GHCR", "push con SHA", "")]
pp = "".join(f'<div class="parada {c}" style="left:{60 + 940 * i / 6:.1f}px"><b>{n}</b><i></i><span>{d}</span></div>'
             for i, (n, d, c) in enumerate(paradas))
slide(f"""
<h2>El recorrido de un cambio</h2>
<p class="sub">Si una estación falla, el tren se detiene: nada llega a Kubernetes.</p>
<div class="ruta">
  <b class="via-ci"></b>{pp}
  <b class="ramal-v"></b><b class="ramal-h"></b>
  <span class="solo-main">solo en main</span>
  <div class="parada cd" style="left:790px"><i></i><b>Deploy</b><span>set image + rollout</span></div>
  <div class="parada cd" style="left:560px"><i></i><b>Humo</b><span>/health y SHA en /version</span></div>
  <div class="parada cd rb" style="left:330px"><i></i><b>Rollback</b><span>si falla: rollout undo</span></div>
  <div class="nota-ci"><b>Todas las ramas y PR</b><span>CI completa; el check de Jenkins es obligatorio para fusionar a main.</span></div>
</div>""", seccion="Pipeline")

# 6. Seguridad
items = [("Secretos fuera del repo", "Tokens, PAT, kubeconfig y webhook viven en Jenkins Credentials o en archivos ignorados por git.", ""),
         ("gitleaks en cada build", "Revisa todo el historial. Detuvo un build por un comentario mío que citaba un patrón de credencial.", "ambar"),
         ("Trivy antes de publicar", "Encontró un CVE real en starlette; se actualizó FastAPI antes de desplegar.", ""),
         ("RBAC activado", "MicroK8s lo tenía apagado. Ahora el ServiceAccount de Prometheus recibe 403 si intenta escribir.", "ambar"),
         ("main protegida", "Solo por Pull Request y con el check de Jenkins en verde.", ""),
         ("Un token expuesto, rotado", "Se pegó por error en un chat: se revocó y quedó documentado.", "")]
seg = "".join(f'<div class="item {c}"><h4>{t}</h4><p>{d}</p></div>' for t, d, c in items)
slide(f"""
<h2>Seguridad del proceso</h2>
<p class="sub">Ningún secreto en el repositorio; permisos mínimos donde se pudo comprobar.</p>
<div class="seis">{seg}</div>""", seccion="Pipeline")

# 7. Demo
pasos = [("curl /version", "anotar el SHA actual"), ("Cambio en rama + PR", "demo-sonar-falla.sh"),
         ("Jenkins arranca solo", "webhook de GitHub"), ("Fallo a propósito", "el Quality Gate detiene el build"),
         ("Corregir y fusionar", "pipeline en verde"), ("Imagen nueva en GHCR", "etiqueta con el SHA"),
         ("kubectl get pods -w", "actualización gradual"), ("curl /version", "SHA nuevo, sin SSH"),
         ("kubectl delete pod", "con Grafana en pantalla"), ("kubectl rollout undo", "vuelve la versión anterior")]
clave = {4, 8, 9, 10}
dp = "".join(f'<li class="{"clave" if i in clave else ""}"><i>{i}</i><b>{p}</b><span>{d}</span></li>'
             for i, (p, d) in enumerate(pasos, start=1))
slide(f"""
<h2 class="blanco">Demo en vivo</h2>
<p class="sub claro">Todo desde la laptop. Nadie se conecta por SSH al clúster.</p>
<ol class="pasos">{dp}</ol>
<p class="leyenda">En ámbar: los pasos que definen la calificación.</p>""", "bata", seccion="Demo", oscuro=True)

# 8-11. Evidencia
slide(f"""
<h2>El fallo a propósito: la imagen nunca se construye</h2>
<p class="sub">PR #4 con un módulo sin pruebas: cobertura de 30.2 %.</p>
<div class="caps"><figure><img src="{img('04-jenkins-pr4-rojo.png')}" alt=""><figcaption>Jenkins: ❌ en Quality Gate; Docker build, push y despliegue saltados.</figcaption></figure>
<figure><img src="{img('04b-github-pr4-bloqueado.png')}" alt=""><figcaption>GitHub: el check requerido falló; el PR no se puede fusionar.</figcaption></figure></div>""",
      seccion="Evidencia")
slide(f"""
<h2>Un merge cambia producción sin SSH</h2>
<p class="sub">El build de main corre todas las estaciones y despliega solo.</p>
<div class="caps"><figure class="ancha"><img src="{img('06-jenkins-main-verde.png')}" alt=""><figcaption>Jenkins: las 13 etapas en verde, de Checkout a Prueba de humo.</figcaption></figure>
<figure class="angosta"><img src="{img('10-rolling-update-pods-w.png')}" alt=""><figcaption>kubectl get pods -w: siempre dos pods listos.</figcaption></figure></div>""",
      seccion="Evidencia")
slide(f"""
<h2>Autocuración y reversión</h2>
<p class="sub">Kubernetes repone lo que se cae; la versión anterior está a un comando.</p>
<div class="caps"><figure class="ancha"><img src="{img('13-grafana-caos.png')}" alt=""><figcaption>Grafana: réplicas listas 2 → 1 → 2 durante el experimento de caos.</figcaption></figure>
<div class="cifras"><p><b class="grande">22 s</b>para volver a 2/2 tras kubectl delete pod; el servicio respondió 200 todo el tiempo.</p>
<p><b>7 reinicios</b>en el experimento de caos: el pod se recuperó sin intervención.</p>
<p><b>rollout undo</b>devuelve la versión anterior y /version lo confirma.</p></div></div>""",
      seccion="Evidencia")
slide(f"""
<h2>Monitoreo con datos reales</h2>
<p class="sub">Dos tableros, 13 destinos en UP y tres alertas probadas en Discord.</p>
<div class="caps"><figure><img src="{img('12-grafana-app.png')}" alt=""><figcaption>Tablero Aplicación: versión, réplicas, 5xx, peticiones por segundo y latencia p95.</figcaption></figure>
<figure><img src="{img('15b-grafana-alertas-disparadas.png')}" alt=""><figcaption>Las cuatro alertas disparadas en la prueba controlada.</figcaption></figure></div>""",
      seccion="Evidencia")

# 12. IA
slide("""
<h2>Uso de inteligencia artificial</h2>
<p class="sub">Claude Code como asistente de ingeniería. Ninguna salida se aceptó sin verificarla.</p>
<div class="dos">
  <div><h3>Para qué se usó</h3>
    <p>Generar el andamiaje: app, pruebas, Dockerfile, manifiestos, Jenkinsfile y monitoreo.</p>
    <p>Ejecutar y diagnosticar la instalación en las VMs.</p>
    <p class="gris">Cada cambio en Azure se confirmó antes; los secretos los escribí yo, nunca la IA.</p></div>
  <div class="regla ambar"><h3 class="tinta">Lo que la IA hizo mal y se corrigió</h3>
    <p>Versiones viejas: la llave de Jenkins había caducado, Jenkins 2.580 exige Java 21 y kube-state-metrics debía coincidir con Kubernetes 1.35.</p>
    <p>Supuso que el ServiceAccount era de solo lectura; al verificarlo, RBAC estaba apagado.</p>
    <p>Escribió un comentario que disparó gitleaks: la puerta lo detuvo.</p></div>
</div>""", seccion="IA y costos")

# 13. Costos
slide("""
<h2>Control de costos</h2>
<div class="dos costos">
  <div><p class="cifra">5.15 USD</p>
    <p class="gris">consumidos del crédito de 100 USD de Azure for Students al 25 de noviembre (el cómputo de las VMs se refleja con retraso).</p></div>
  <div><p>Presupuesto de 50 USD con avisos al 80 %, 100 % y por pronóstico.</p>
    <p>Apagado diario a las 23:00 con deallocate. El nativo de Azure no existe en mexicocentral: lo hace un cron con identidad administrada.</p>
    <p>Prometheus con retención de 15 días; tamaños B y discos StandardSSD.</p>
    <p>Al terminar el curso se borra el grupo de recursos.</p></div>
</div>""", seccion="IA y costos")

# 14. Cierre
slide("""
<h2 class="blanco">Lo que me llevo</h2>
<div class="lecciones">
  <p>Verificar contra el sistema real, no contra la memoria: varias versiones conocidas ya no servían.</p>
  <p>Un requisito de seguridad solo cuenta si se comprueba.</p>
  <p>Las puertas automáticas atrapan errores humanos y de la IA.</p>
</div>
<p class="preguntas">Preguntas</p>
<p class="repo">github.com/diegodaac/medisur-pilot</p>""", "bata", seccion="Cierre", oscuro=True)

assert len(slides) == len(notas), (len(slides), len(notas))
slides = [s.replace('data-document-role="page">', f'data-document-role="page" data-speaker-notes="{e(n)}">', 1)
          for s, n in zip(slides, notas)]

CSS = """
@page { size: 1280px 720px; margin: 0 }
:root { --papel:#EEF4F1; --tinta:#16262B; --verde:#2F7D6B; --bata:#1E4D44; --ambar:#E3A13A; --rojo:#C8413A;
        --gris:#5E6E73; --claro:#A9D3C6; --via:#C9DBD4 }
* { box-sizing: border-box; margin: 0; padding: 0 }
html, body { background: var(--papel) }
body { font-family: "Barlow", sans-serif; color: var(--tinta); -webkit-print-color-adjust: exact; print-color-adjust: exact }
.slide { width: 1280px; height: 720px; position: relative; overflow: hidden; background: var(--papel);
         padding: 52px 72px 0; page-break-after: always; break-after: page }
.slide.bata { background: var(--bata); color: #fff }
h1, h2, h3, h4 { font-family: "Barlow Condensed", sans-serif; font-weight: 700; line-height: 1 }
h2 { font-size: 46px; letter-spacing: -0.2px }
h3 { font-size: 26px; color: var(--verde); margin-bottom: 14px }
h3.rojo { color: var(--rojo) } h3.tinta { color: var(--tinta) }
.sub { font-size: 20px; color: var(--gris); margin-top: 8px }
.sub.claro, .claro { color: var(--claro) } .blanco { color: #fff }
p { font-size: 20px; line-height: 1.38; margin-bottom: 12px; max-width: 62ch }
.gris { color: var(--gris) } .chico { font-size: 16px }
/* metro al pie */
.metro { position: absolute; left: 0; right: 0; bottom: 34px; height: 24px }
.metro .via, .metro .avance { position: absolute; left: 60px; top: 10px; height: 4px; background: var(--via); width: 1160px }
.metro .avance { background: var(--verde) }
.metro .est { position: absolute; top: 5px; width: 14px; height: 14px; margin-left: -7px; border-radius: 50%;
              background: var(--papel); border: 3px solid var(--via) }
.metro .est.hecha { border-color: var(--verde) }
.metro .est.actual { width: 22px; height: 22px; margin-left: -11px; top: 1px; background: var(--verde); border-color: var(--verde) }
.metro .nombre { position: absolute; bottom: 26px; left: 50%; transform: translateX(-50%); white-space: nowrap;
                 font: 700 15px "Barlow Condensed"; color: var(--verde) }
.metro.oscuro .via { background: #2f6a5f } .metro.oscuro .avance { background: var(--claro) }
.metro.oscuro .est { background: var(--bata); border-color: #2f6a5f } .metro.oscuro .est.hecha { border-color: var(--claro) }
.metro.oscuro .est.actual { background: var(--claro); border-color: var(--claro) } .metro.oscuro .nombre { color: var(--claro) }
/* portada */
.sobre { color: var(--claro); font-size: 19px; margin-top: 18px }
h1.portada { font-size: 86px; line-height: 0.95; margin-top: 18px; color: #fff; letter-spacing: -0.5px }
.lema { color: var(--claro); font-size: 26px; margin-top: 22px; max-width: none }
.p-linea { position: absolute; left: 60px; right: 60px; top: 470px; height: 80px }
.p-linea > b { position: absolute; left: 0; right: 0; top: 18px; height: 12px; background: var(--claro); border-radius: 6px }
.p-est { position: absolute; top: 0; width: 0 }
.p-est i { position: absolute; left: -24px; top: 0; width: 48px; height: 48px; border-radius: 50%; background: var(--bata); border: 6px solid #fff }
.p-est span { position: absolute; left: -90px; width: 180px; top: 58px; text-align: center; font: 700 24px "Barlow Condensed" }
.creditos { position: absolute; left: 72px; bottom: 30px; font-size: 16px; color: var(--claro); max-width: none }
/* dos columnas */
.dos { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; margin-top: 44px }
.regla { border-left: 6px solid var(--verde); padding-left: 32px } .regla.ambar { border-color: var(--ambar) }
/* arquitectura */
.arq { display: grid; grid-template-columns: 720px 1fr; gap: 40px; margin-top: 24px; align-items: start }
.arq img { width: 720px; height: auto; display: block }
.arq-txt h3 { margin: 0 0 2px } .dato { font-size: 16px; color: var(--gris); margin-bottom: 6px } .arq-txt p { font-size: 18px }
/* herramientas */
.cinco { display: grid; grid-template-columns: repeat(5, 1fr); gap: 36px; margin-top: 56px }
.col { border-top: 7px solid var(--verde); padding-top: 18px } .col h3 { font-size: 30px } .col p { font-size: 20px; margin-bottom: 10px }
/* pipeline */
.ruta { position: relative; height: 420px; margin-top: 30px }
.via-ci { position: absolute; left: 60px; top: 116px; width: 1052px; height: 12px; background: var(--verde); border-radius: 6px }
.parada { position: absolute; top: 60px; width: 0 }
.parada b { position: absolute; left: -95px; width: 190px; text-align: center; top: 0; font: 700 22px "Barlow Condensed" }
.parada i { position: absolute; left: -19px; top: 43px; width: 38px; height: 38px; border-radius: 50%; background: var(--papel); border: 6px solid var(--verde) }
.parada span { position: absolute; left: -95px; width: 190px; text-align: center; top: 92px; font-size: 15px; color: var(--gris); line-height: 1.25 }
.parada.gate i { width: 48px; height: 48px; left: -24px; top: 38px; background: var(--ambar); border-color: var(--ambar) }
.ramal-v { position: absolute; left: 1100px; top: 122px; width: 12px; height: 162px; background: var(--bata) }
.ramal-h { position: absolute; left: 330px; top: 272px; width: 782px; height: 12px; background: var(--bata); border-radius: 6px }
.solo-main { position: absolute; left: 990px; top: 196px; font: 700 18px "Barlow"; color: var(--bata) }
.parada.cd { top: 236px } .parada.cd i { top: 23px; border-color: var(--bata) } .parada.cd b { top: 74px } .parada.cd span { top: 104px }
.parada.rb i { border-color: var(--rojo) }
.nota-ci { position: absolute; left: 0; top: 300px; width: 215px } .nota-ci b { display: block; color: var(--verde); font-size: 18px }
.nota-ci span { font-size: 15px; color: var(--gris); line-height: 1.3 }
/* seguridad */
.seis { display: grid; grid-template-columns: 1fr 1fr; gap: 26px 64px; margin-top: 40px }
.item { border-left: 6px solid var(--verde); padding-left: 22px } .item.ambar { border-color: var(--ambar) }
.item h4 { font-size: 24px; margin-bottom: 6px } .item p { font-size: 17px; color: var(--gris); margin: 0 }
/* demo */
.pasos { list-style: none; display: grid; grid-template-columns: 1fr 1fr; grid-auto-flow: column; grid-template-rows: repeat(5, 76px);
         gap: 4px 64px; margin-top: 34px }
.pasos li { display: grid; grid-template-columns: 48px 1fr; column-gap: 18px; align-items: center }
.pasos i { grid-row: span 2; width: 44px; height: 44px; border-radius: 50%; border: 3px solid var(--claro); display: grid; place-items: center;
           font: 700 20px "Barlow Condensed"; font-style: normal }
.pasos li.clave i { background: var(--ambar); border-color: var(--ambar); color: var(--tinta) }
.pasos b { font: 700 24px "Barlow Condensed"; align-self: end } .pasos span { font-size: 16px; color: var(--claro); align-self: start }
.leyenda { position: absolute; left: 72px; bottom: 92px; color: var(--ambar); font-size: 16px }
/* capturas */
.caps { display: flex; gap: 28px; margin-top: 26px; align-items: flex-start }
.caps figure { flex: 1 1 0 } .caps figure.ancha { flex: 1.25 1 0 } .caps figure.angosta { flex: 0.75 1 0 }
.caps img { width: 100%; height: auto; display: block; border: 1px solid var(--via) }
figcaption { font-size: 15px; color: var(--gris); margin-top: 10px; line-height: 1.3 }
.cifras { flex: 0.8 1 0; padding-top: 6px } .cifras p { font-size: 17px; color: var(--gris); margin-bottom: 22px }
.cifras b { display: block; font: 700 34px "Barlow Condensed"; color: var(--tinta); line-height: 1.05 }
.cifras b.grande { font-size: 64px; color: var(--verde) }
/* costos */
.costos { margin-top: 30px } .cifra { font: 700 108px "Barlow Condensed"; color: var(--verde); line-height: 0.95; margin-bottom: 18px }
/* cierre */
.lecciones { margin-top: 40px } .lecciones p { font-size: 28px; color: #fff; margin-bottom: 18px; max-width: 46ch }
.preguntas { font: 700 80px "Barlow Condensed"; color: var(--claro); margin-top: 40px; line-height: 1 }
.repo { font-size: 20px; color: #fff; margin-top: 6px }
"""

doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>MediSur · Presentación</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600;700&display=block" rel="stylesheet">
<style>{CSS}</style></head>
<body>
{"".join(slides)}
</body></html>"""
SALIDA.write_text(doc, encoding="utf-8")
print(f"escrita {SALIDA} con {len(slides)} diapositivas")
