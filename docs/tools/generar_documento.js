// Genera el documento Word del trabajo final a partir de los archivos reales del repositorio.
// Uso:  (cd /tmp && npm install docx@9) && NODE_PATH=/tmp/node_modules node docs/tools/generar_documento.js . entrega/MediSur_Trabajo_Final.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, HeadingLevel,
  AlignmentType, WidthType, ShadingType, BorderStyle, PageBreak, TableOfContents, Footer,
  PageNumber, LevelFormat, ExternalHyperlink, TabStopType,
} = require("docx");

const REPO = process.argv[2];
const OUT = process.argv[3];
const rd = (p) => fs.readFileSync(path.join(REPO, p), "utf8");

// ---------- utilidades ----------
const FONT = "Arial";
const W = 9360; // ancho útil carta con márgenes de 1": 12240 - 2*1440
const C = { azul: "1F4E79", gris: "F2F4F7", borde: "BFC5CC", amar: "FFF4CE", amarBorde: "E0B000" };
const limpiar = (s) => s.replace(/\*\*/g, "").replace(/`/g, "").replace(/\\\|/g, "|").trim();

function runs(texto, base = {}) {
  // Soporta **negritas** y `código` en línea.
  const out = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(texto))) {
    if (m.index > last) out.push(new TextRun({ text: texto.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", ...base }));
    last = m.index + t.length;
  }
  if (last < texto.length) out.push(new TextRun({ text: texto.slice(last), ...base }));
  return out;
}
const P = (texto, opts = {}) => new Paragraph({ children: runs(texto, opts.run || {}), spacing: { after: 120, line: 276 }, alignment: opts.align || AlignmentType.JUSTIFIED, ...opts.p });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], pageBreakBefore: true });
const H1b = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: "vinetas", level: 0 }, children: runs(t), spacing: { after: 60, line: 264 } });
const numero = (t) => new Paragraph({ numbering: { reference: "numeros", level: 0 }, children: runs(t), spacing: { after: 60, line: 264 } });

const borde = { style: BorderStyle.SINGLE, size: 4, color: C.borde };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };

function tabla(encabezados, filas, anchos, tam = 17) {
  const total = anchos.reduce((a, b) => a + b, 0);
  const celda = (txt, i, head) => new TableCell({
    width: { size: anchos[i], type: WidthType.DXA },
    borders: bordes,
    shading: head ? { fill: C.azul, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: String(txt).split("\n").map((linea) => new Paragraph({
      children: runs(linea, { size: tam, color: head ? "FFFFFF" : undefined, bold: head || undefined }),
      spacing: { after: 0, line: 240 },
    })),
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: anchos,
    rows: [
      new TableRow({ tableHeader: true, children: encabezados.map((h, i) => celda(h, i, true)) }),
      ...filas.map((f, r) => new TableRow({
        children: f.map((v, i) => {
          const c = celda(v, i, false);
          return c;
        }),
      })),
    ],
  });
}
const espacio = () => new Paragraph({ children: [], spacing: { after: 120 } });
const pie = (t) => new Paragraph({ children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })], alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 } });

function captura(num, desc) {
  // Devuelve [espaciador, recuadro]: el espaciador evita que Word fusione los
  // bordes de dos recuadros seguidos en uno solo.
  return [new Paragraph({ children: [], spacing: { after: 0 } }), new Paragraph({
    children: [
      new TextRun({ text: `[ INSERTAR CAPTURA ${num} ]  `, bold: true, color: "7A5C00" }),
      new TextRun({ text: desc, color: "7A5C00" }),
    ],
    shading: { fill: C.amar, type: ShadingType.CLEAR, color: "auto" },
    border: { top: { style: BorderStyle.DASHED, size: 6, color: C.amarBorde, space: 6 }, bottom: { style: BorderStyle.DASHED, size: 6, color: C.amarBorde, space: 6 }, left: { style: BorderStyle.DASHED, size: 6, color: C.amarBorde, space: 6 }, right: { style: BorderStyle.DASHED, size: 6, color: C.amarBorde, space: 6 } },
    spacing: { before: 160, after: 200 },
    alignment: AlignmentType.CENTER,
  })];
}

function codigo(texto, tam = 14) {
  return texto.replace(/\t/g, "  ").split("\n").map((l, i, arr) => new Paragraph({
    children: [new TextRun({ text: l.length ? l : " ", font: "Consolas", size: tam })],
    shading: { fill: C.gris, type: ShadingType.CLEAR, color: "auto" },
    spacing: { after: 0, line: 220 },
    keepLines: true,
  }));
}

// Tabla markdown -> filas
function tablaMd(md, encabezadoContiene) {
  const lineas = md.split("\n");
  const ini = lineas.findIndex((l) => l.startsWith("|") && l.includes(encabezadoContiene));
  const filas = [];
  for (let i = ini + 2; i < lineas.length && lineas[i].startsWith("|"); i++) {
    const celdas = lineas[i].replace(/\\\|/g, "§").split("|").slice(1, -1).map((c) => c.replace(/§/g, "|").trim());
    filas.push(celdas);
  }
  return filas;
}
// Mantiene ** y ` para que runs() los formatee
const md = (s) => s.replace(/\\\|/g, "|").trim();

// ---------- contenido real del repo ----------
const jenkinsfile = rd("Jenkinsfile");
const decisiones = rd("docs/decisiones.md");
const ailog = rd("docs/AI_LOG.md");
const filasDec = tablaMd(decisiones, "| Tema |");
const filasInc = tablaMd(decisiones, "| Fecha | Secreto |");
const limitaciones = decisiones.split("## Limitaciones conocidas")[1].split("\n").filter((l) => l.startsWith("- ")).map((l) => l.slice(2));
const filasIA = tablaMd(ailog, "| # | Dónde se usó |");
const prosaIA = ailog.split("## Explicación")[1].trim().split(/\n\s*\n/).map((s) => s.trim());
const alertas = rd("monitoring/rules/alerts.yml");
const diagrama = fs.readFileSync(path.join(REPO, "docs/arquitectura.png"));

// ---------- documento ----------
const children = [];

// Portada
children.push(
  new Paragraph({ children: [new TextRun({ text: "Universidad Autónoma de Nuevo León", bold: true, size: 30 })], alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: "Facultad de Ciencias Físico Matemáticas", size: 26 })], alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({ text: "Trabajo final", size: 26, color: "555555" })], alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  new Paragraph({ children: [new TextRun({ text: "Automatización de entrega continua sobre Kubernetes", bold: true, size: 44, color: C.azul })], alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
  new Paragraph({ children: [new TextRun({ text: "Piloto para MediSur, S.A. de C.V.", size: 30 })], alignment: AlignmentType.CENTER, spacing: { after: 1400 } }),
);
const portada = [
  ["Materia", "Cómputo en la Nube"],
  ["Integrante y rol", "Diego Alejandro Alvarado Castañón — trabajo individual: arquitectura, infraestructura en Azure, pipeline CI/CD, Kubernetes, monitoreo y documentación"],
  ["Profesor", "[Nombre del profesor]"],
  ["Repositorio", "https://github.com/diegodaac/medisur-pilot"],
  ["Fecha", "25 de noviembre de 2026"],
];
children.push(tabla(["Dato", "Valor"], portada, [2400, 6960], 20));

// Índice
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(new Paragraph({ children: [new TextRun({ text: "Índice", bold: true, size: 32, color: C.azul })], spacing: { after: 200 } }));
children.push(new TableOfContents("Índice", { hyperlink: true, headingStyleRange: "1-2" }));
children.push(P("Si el índice aparece vacío, en Word haz clic derecho sobre él y elige **Actualizar campo → Actualizar toda la tabla**.", { run: { italics: true, size: 18, color: "777777" } }));

// 2. Problemática y objetivo
children.push(H1("1. Problemática y objetivo"));
children.push(H2("Problemática"));
children.push(P("MediSur, S.A. de C.V. (caso ficticio del curso) necesita publicar cambios de su software sin depender de pasos manuales. Cuando una persona compila, copia y reinicia servicios a mano, los despliegues se vuelven lentos, difíciles de repetir y propensos a error; no queda registro de qué versión corre en producción, y los problemas se descubren cuando ya afectan a los usuarios. Tampoco hay una barrera que impida publicar código sin pruebas o con defectos graves."));
children.push(H2("Objetivo"));
children.push(P("Construir un **piloto de entrega continua** en Azure que, con cada cambio en el repositorio, ejecute de forma automática pruebas, análisis de calidad, construcción y publicación de la imagen de contenedor, y despliegue en Kubernetes sin interrupción, con reversión automática si algo falla. El piloto debe ser **observable**: tableros con datos reales y alertas que avisen antes de que un problema escale."));
children.push(P("Lo que se evalúa es la automatización, no la aplicación. Por eso la aplicación es deliberadamente sencilla (una API de inventario de insumos) y el esfuerzo se concentra en el pipeline, el despliegue, la seguridad del proceso y el monitoreo."));
children.push(H2("Alcance"));
[
  "API FastAPI con `/health`, `/ready`, `/version`, `/metrics` y `/api/items` (GET y POST), configurada solo por variables de entorno.",
  "Dos máquinas virtuales separadas: VM-TOOLS (construir, analizar, vigilar) y VM-K8S (ejecutar la aplicación).",
  "Pipeline declarativo en `Jenkinsfile`, versionado en el repositorio y disparado por webhook.",
  "Despliegue en MicroK8s con 2 réplicas, sondas, actualización gradual y reversión con `kubectl rollout undo`.",
  "Prometheus, Grafana y Alertmanager fuera del clúster, con dos tableros y tres alertas que notifican a Discord.",
].forEach((t) => children.push(bullet(t)));

// 3. Arquitectura
children.push(H1("2. Arquitectura"));
children.push(new Paragraph({ children: [new ImageRun({ type: "png", data: diagrama, transformation: { width: 624, height: Math.round(624 * 2428 / 3812) } })], alignment: AlignmentType.CENTER }));
children.push(pie("Figura 1. Arquitectura del piloto (diagrama propio, fuente versionada en docs/arquitectura.dot)."));
children.push(P("La solución vive en la suscripción Azure for Students, en la región mexicocentral, dentro de una sola red virtual (172.16.0.0/16). Hay **dos máquinas virtuales con responsabilidades separadas**:"));
children.push(bullet("**VM-TOOLS** (Standard_B4as_v2, 4 vCPU, 16 GB, IP privada 172.16.0.5) construye, analiza y vigila: Jenkins nativo, SonarQube con PostgreSQL, Docker y el stack de monitoreo (Prometheus, Alertmanager, Grafana y blackbox exporter) en Docker Compose."));
children.push(bullet("**VM-K8S** (Standard_B2as_v2, 2 vCPU, 8 GB, IP privada 172.16.0.4) solo ejecuta: MicroK8s 1.35 con RBAC activo, la aplicación en el namespace `medisur`, kube-state-metrics y node_exporter."));
children.push(P("**Flujo de entrega (azul).** El desarrollador sube un cambio a una rama y abre un Pull Request. GitHub avisa a Jenkins por webhook; Jenkins ejecuta el `Jenkinsfile` del propio repositorio: revisiones de seguridad, pruebas con cobertura, análisis en SonarQube y espera del veredicto del Quality Gate (SonarQube responde con otro webhook). Si todo pasa, construye la imagen, la escanea con Trivy y la publica en GHCR con dos etiquetas: `<VERSION>-<sha>` y `<sha>`. Solo en la rama `main`, Jenkins actualiza el Deployment con `kubectl`, espera el `rollout status` y hace una prueba de humo contra `/health` y `/version`. Si la prueba falla, el bloque `post` ejecuta `kubectl rollout undo`."));
children.push(P("**Flujo de observabilidad (naranja).** Prometheus corre en VM-TOOLS, fuera del clúster, y recolecta métricas de los node_exporter de ambas VMs, de kube-state-metrics, de cada pod de la aplicación (a través del proxy del API server, con un ServiceAccount de solo lectura) y de cAdvisor. Grafana lo consulta para los tableros y Alertmanager envía las alertas a un canal de Discord."));
children.push(P("**Seguridad de red.** Los NSG solo admiten SSH, Jenkins, SonarQube, Grafana y Prometheus desde la IP del administrador; el puerto de Jenkins además acepta los rangos de webhooks publicados por GitHub. Los exporters de VM-K8S solo aceptan conexiones desde la IP privada de VM-TOOLS."));

// 4. Inventario
children.push(H1("3. Inventario de aplicaciones y herramientas"));
children.push(P("Una fila por herramienta instalada o usada. Las versiones se tomaron directamente de las VMs y del repositorio el 25 de noviembre de 2026."));
const inv = [
  ["Ubuntu Server", "22.04.5 LTS / 24.04.5 LTS", "Sistema operativo", "VM-TOOLS / VM-K8S", "Base de ambas VMs", "LTS con soporte largo; VM-K8S se reutilizó de LAB-03 (24.04)", "Gratuito"],
  ["Jenkins", "2.580.3 LTS", "CI/CD", "VM-TOOLS (apt, systemd)", "Ejecuta el pipeline multirrama", "Exigido por el enunciado; Jenkinsfile versionado, plugins para Sonar y GitHub", "MIT, gratuito"],
  ["OpenJDK", "21.0.13", "Runtime", "VM-TOOLS", "Requisito de Jenkins", "Jenkins 2.580 exige Java 21 o 25", "GPLv2 + CE"],
  ["Docker Engine / Compose", "29.1.3 / 2.40.3", "Contenedores", "VM-TOOLS", "Build de imágenes y stacks de Sonar y monitoreo", "Estándar de facto; Compose versiona la configuración", "Apache 2.0"],
  ["SonarQube Community", "10.7.0.96327", "Calidad de código", "VM-TOOLS (Docker)", "Análisis estático y Quality Gate", "Exigido; Community basta para una rama. Fijado por estabilidad", "LGPL v3"],
  ["PostgreSQL", "16.16", "Base de datos", "VM-TOOLS (Docker)", "Persistencia de SonarQube", "Base recomendada por SonarQube", "PostgreSQL License"],
  ["SonarScanner CLI", "8.5.0.16571", "Calidad de código", "VM-TOOLS (herramienta de Jenkins)", "Envía código y cobertura a Sonar", "Instalación automática desde Jenkins", "LGPL v3"],
  ["Jenkins: SonarQube Scanner / Prometheus metrics / GitHub Branch Source", "2.19.1 / 873.v054598e6e84d / 1988.v87ea_66346560", "Plugins", "VM-TOOLS", "Gate en Jenkins, métricas /prometheus/, Multibranch desde GitHub", "Integraciones oficiales", "MIT"],
  ["MicroK8s (containerd)", "v1.35.6 (2.1.6)", "Orquestación", "VM-K8S (snap)", "Ejecuta la aplicación", "Continuidad con LAB-03; un solo nodo, ligero", "Apache 2.0"],
  ["kubectl", "v1.35.6", "Orquestación", "VM-TOOLS", "Despliegue desde Jenkins", "Misma versión que el clúster", "Apache 2.0"],
  ["kube-state-metrics", "v2.19.1", "Monitoreo", "VM-K8S (NodePort 30808)", "Réplicas, reinicios, estado de objetos", "Versión compatible con Kubernetes 1.35", "Apache 2.0"],
  ["node_exporter", "1.8.2", "Monitoreo", "Ambas VMs (systemd)", "CPU, memoria, disco, red, systemd", "Exporter oficial de Prometheus", "Apache 2.0"],
  ["Prometheus", "v3.1.0", "Monitoreo", "VM-TOOLS (Docker)", "Recolección de métricas y reglas de alerta", "Exigido; fuera del clúster, retención 15 d", "Apache 2.0"],
  ["Alertmanager", "v0.28.1", "Alertas", "VM-TOOLS (Docker)", "Agrupa y envía alertas", "Soporte nativo de Discord desde 0.28", "Apache 2.0"],
  ["Grafana", "11.4.0", "Visualización", "VM-TOOLS (Docker)", "Dos tableros provisionados como JSON", "Exigido; tableros como código", "AGPL v3"],
  ["blackbox exporter", "v0.25.0", "Monitoreo", "VM-TOOLS (Docker)", "Estado HTTP de Jenkins, Sonar, Prometheus, Grafana", "Los servicios en Docker no aparecen en systemd", "Apache 2.0"],
  ["GitHub", "SaaS", "Repositorio", "Nube", "Código, PR, webhook, protección de main", "Una sola plataforma con el registro", "Gratuito"],
  ["GitHub Container Registry", "SaaS", "Registro", "Nube", "Almacena las imágenes", "Integrado con GitHub; permitido por el enunciado", "Gratuito"],
  ["Python / FastAPI / starlette / uvicorn", "3.12 / 0.128.0 / 0.50.0 / 0.34.0", "Aplicación", "Imagen python:3.12-slim", "API del piloto", "Dominio previo; starlette fijado por CVE-2025-62727", "PSF / MIT / BSD-3 / BSD-3"],
  ["prometheus_client / pytest / pytest-cov", "0.21.1 / 8.3.4 / 6.0.0", "Aplicación y pruebas", "Imagen / contenedor de pruebas", "Métricas y pruebas con cobertura XML", "coverage.py genera el XML que lee Sonar", "Apache 2.0 / MIT / MIT"],
  ["Hadolint (extra)", "v2.15.1", "Seguridad", "VM-TOOLS (contenedor)", "Lint del Dockerfile", "Barato y en contenedor", "GPL v3"],
  ["gitleaks (extra)", "v8.30.1", "Seguridad", "VM-TOOLS (contenedor)", "Busca secretos en todo el historial", "Detecta secretos antes de publicar", "MIT"],
  ["Trivy (extra)", "0.76.2", "Seguridad", "VM-TOOLS (contenedor)", "Vulnerabilidades de la imagen antes del push", "Ya detectó un CVE real en starlette", "Apache 2.0"],
  ["Azure CLI", "2.93.0", "Operación", "VM-TOOLS y laptop", "Autoapagado (deallocate) e infraestructura", "Identidad administrada sin secretos", "MIT"],
  ["Discord", "SaaS", "Notificaciones", "Nube", "Canal de alertas", "Gratuito y con receptor nativo en Alertmanager", "Gratuito"],
];
children.push(tabla(["Nombre", "Versión exacta", "Categoría", "Dónde corre", "Para qué", "Por qué esa y no otra", "Licencia o costo"], inv, [1350, 1300, 1050, 1300, 1450, 1810, 1100], 14));

// 5. CMDB
children.push(H1("4. CMDB de la solución"));
children.push(P("Elementos de configuración (CI) con sus atributos principales, seguidos de sus relaciones. Se usan los tipos de relación del enunciado: «se ejecuta en», «depende de», «construye a», «monitorea a» y «almacena a»."));
const cis = [
  ["CI-01", "VM-TOOLS (vm-tools)", "Máquina virtual", "Standard_B4as_v2; Ubuntu 22.04; 172.16.0.5 / 158.23.177.202; disco 64 GB StandardSSD"],
  ["CI-02", "VM-K8S (vm-microk8s)", "Máquina virtual", "Standard_B2as_v2; Ubuntu 24.04; 172.16.0.4 / 158.23.21.125"],
  ["CI-03", "Clúster MicroK8s", "Plataforma", "v1.35.6; un nodo; RBAC,Node; API :16443"],
  ["CI-04", "Deployment medisur-api", "Carga de trabajo", "ns medisur; 2 réplicas; RollingUpdate maxSurge 1 / maxUnavailable 0; liveness /health; readiness /ready; no root (UID 10001)"],
  ["CI-05", "Service medisur-api", "Red", "NodePort 30080 → puerto 8000"],
  ["CI-06", "Imagen medisur-pilot", "Artefacto", "ghcr.io/diegodaac/medisur-pilot:<VERSION>-<sha> y :<sha>; última 1.0.0-3b5f159"],
  ["CI-07", "Registro GHCR", "Servicio externo", "Paquete privado; acceso por PAT con write:packages"],
  ["CI-08", "Repositorio diegodaac/medisur-pilot", "Código fuente", "GitHub público; main protegida (PR + check de Jenkins obligatorio)"],
  ["CI-09", "Jenkins", "Servicio CI/CD", "2.580.3; Multibranch medisur-pilot; 4 credenciales; :8080"],
  ["CI-10", "SonarQube", "Servicio de calidad", "10.7 Community; Quality Gate MediSur; :9000"],
  ["CI-11", "Prometheus", "Servicio de monitoreo", "v3.1.0; retención 15 d; :9090"],
  ["CI-12", "Grafana", "Servicio de visualización", "11.4.0; tableros Infraestructura y Aplicación; :3000"],
  ["CI-13", "Alertmanager", "Servicio de alertas", "v0.28.1; receptor Discord"],
  ["CI-14", "kube-state-metrics", "Exporter", "v2.19.1; NodePort 30808"],
];
children.push(tabla(["ID", "Elemento", "Tipo", "Atributos"], cis, [800, 2300, 1700, 4560], 16));
children.push(espacio());
const rel = [
  ["CI-09 Jenkins", "se ejecuta en", "CI-01 VM-TOOLS"],
  ["CI-10 SonarQube", "se ejecuta en", "CI-01 VM-TOOLS"],
  ["CI-11 Prometheus / CI-12 Grafana / CI-13 Alertmanager", "se ejecuta en", "CI-01 VM-TOOLS"],
  ["CI-03 Clúster MicroK8s", "se ejecuta en", "CI-02 VM-K8S"],
  ["CI-04 Deployment / CI-14 kube-state-metrics", "se ejecuta en", "CI-03 Clúster"],
  ["CI-09 Jenkins", "depende de", "CI-08 Repositorio (Jenkinsfile y webhook)"],
  ["CI-09 Jenkins", "depende de", "CI-10 SonarQube (Quality Gate)"],
  ["CI-09 Jenkins", "construye a", "CI-06 Imagen"],
  ["CI-07 GHCR", "almacena a", "CI-06 Imagen"],
  ["CI-08 Repositorio", "almacena a", "Jenkinsfile, manifiestos k8s/ y configuración de monitoreo"],
  ["CI-04 Deployment", "depende de", "CI-06 Imagen"],
  ["CI-05 Service", "depende de", "CI-04 Deployment"],
  ["CI-11 Prometheus", "monitorea a", "CI-01, CI-02, CI-03, CI-04 y CI-09"],
  ["CI-12 Grafana", "depende de", "CI-11 Prometheus"],
  ["CI-13 Alertmanager", "depende de", "CI-11 Prometheus"],
];
children.push(tabla(["Origen", "Relación", "Destino"], rel, [3600, 1600, 4160], 16));

// 6. Pipeline
children.push(H1("5. Diseño del pipeline"));
children.push(P("El pipeline es declarativo y vive en el `Jenkinsfile` del repositorio; Jenkins solo tiene configurado de dónde leerlo (Multibranch Pipeline). Construye todas las ramas y Pull Requests; las etapas de entrega continua solo corren en `main`. **Si cualquier etapa falla, el pipeline se detiene y nada llega a Kubernetes.**"));
const etapas = [
  ["Checkout", "Descarga el commit exacto; calcula SHA corto, versión y fecha", "—", "Todas"],
  ["Seguridad estática (paralelo)", "Hadolint revisa el Dockerfile; gitleaks busca secretos en todo el historial", "Error en Dockerfile o secreto encontrado", "Todas"],
  ["Pruebas y cobertura", "venv con dependencias fijadas en python:3.12-slim; pytest con coverage.xml", "Una prueba falla", "Todas"],
  ["Análisis SonarQube", "SonarScanner envía código y cobertura", "Error de análisis", "Todas"],
  ["Quality Gate", "waitForQualityGate abortPipeline: true (5 min)", "Cobertura < 60 %, confiabilidad o seguridad peor que A", "Todas"],
  ["Docker build", "Imagen multietapa con APP_VERSION, GIT_SHA y BUILD_DATE", "Error de build", "Todas"],
  ["Escaneo de imagen (Trivy)", "Reporta HIGH; bloquea CRITICAL con parche", "Vulnerabilidad crítica corregible", "Todas"],
  ["Push a GHCR", "Publica <VERSION>-<sha> y <sha>; nunca latest", "Login o push fallido", "Todas"],
  ["Preparar clúster", "Namespace, ConfigMap, Service; Secrets generados desde Jenkins Credentials", "Error de kubectl", "Solo main"],
  ["Desplegar a Kubernetes", "Aplica el Deployment, set image y rollout status --timeout=120s", "Pods no listos a tiempo", "Solo main"],
  ["Prueba de humo", "curl a /health y /version; el SHA debe coincidir", "SHA distinto o servicio caído", "Solo main"],
  ["post { failure }", "kubectl rollout undo si el fallo ocurrió ya en el despliegue", "—", "Solo main"],
];
children.push(tabla(["Etapa", "Qué hace", "Falla si…", "Ramas"], etapas, [2000, 3800, 2400, 1160], 16));
children.push(espacio());
children.push(P("**Credenciales.** Ninguna vive en el repositorio. Jenkins Credentials guarda `sonar-token` (Secret text), `ghcr-pat` (usuario y PAT con write:packages), `medisur-api-key` (Secret text) y `kubeconfig-k8s` (Secret file, apuntando a la IP privada de VM-K8S con TLS verificado). Los bloques `sh` con secretos usan comillas simples para que Groovy no los interpole y Jenkins los enmascare en el log."));
children.push(P("**Protección de la rama main.** GitHub exige Pull Request y el check `continuous-integration/jenkins/pr-head` en verde para fusionar, y bloquea el force-push y el borrado de la rama. Un PR con el Quality Gate en rojo no se puede fusionar."));
children.push(H2("Jenkinsfile comentado (versión entregada)"));
children.push(...codigo(jenkinsfile, 13));

// 7. Monitoreo
children.push(H1("6. Monitoreo"));
children.push(P("Prometheus corre en VM-TOOLS (no dentro del clúster) y conserva las métricas 15 días (opción `--storage.tsdb.retention.time=15d`). Toda la configuración está versionada en `monitoring/`: la plantilla de Prometheus, las reglas de alerta, el ejemplo de Alertmanager y los tableros de Grafana provisionados como JSON."));
children.push(H2("Fuentes de métricas"));
const jobs = [
  ["node-tools / node-k8s", "node_exporter en ambas VMs (:9100)", "CPU, memoria, disco, red, systemd, tiempo encendido"],
  ["kube-state-metrics", "VM-K8S :30808", "Réplicas listas y deseadas, reinicios de contenedor"],
  ["medisur-pods", "Cada pod vía proxy del API server (SA de solo lectura)", "http_requests_total, http_request_duration_seconds, app_info"],
  ["cadvisor", "Kubelet vía proxy del API server", "CPU y memoria por pod"],
  ["blackbox-servicios", "Probes HTTP", "Estado de Jenkins, SonarQube, Prometheus y Grafana"],
  ["jenkins / prometheus / grafana", "Endpoints propios", "Salud de las herramientas"],
];
children.push(tabla(["Job", "Origen", "Qué aporta"], jobs, [2200, 3400, 3760], 16));
children.push(P("Las métricas de la aplicación se leen **pod por pod**, no a través del Service: con dos réplicas, leerlas por el Service mezclaría los contadores de ambos pods de forma incoherente."));
children.push(H2("Tablero 1: Infraestructura"));
children.push(P("Las dos VMs lado a lado (una serie por VM): CPU, memoria disponible, disco usado en `/`, red recibida y enviada, estado de servicios (ACTIVO/CAÍDO), tiempo encendido, estado de `jenkins.service` en systemd y destinos de Prometheus."));
children.push(...captura("11", "Tablero Infraestructura con datos reales de VM-TOOLS y VM-K8S"));
children.push(H2("Tablero 2: Aplicación"));
children.push(P("Versión desplegada (etiqueta de `app_info`), réplicas listas contra deseadas, tasa de errores 5xx, peticiones por segundo por endpoint, latencia p95, CPU y memoria por pod y reinicios de contenedor."));
children.push(...captura("12", "Tablero Aplicación con datos reales"));
children.push(...captura("13", "Tablero Aplicación durante la eliminación de un pod y su recuperación"));
children.push(H2("Alertas"));
const filasAl = [
  ["DiscoLleno", "Uso de / > 80 % en cualquier VM", "2 min", "warning"],
  ["PodReiniciandose", "increase(kube_pod_container_status_restarts_total{namespace=\"medisur\"}[10m]) > 3", "—", "critical"],
  ["ReplicasNoDisponibles", "réplicas disponibles < réplicas deseadas", "5 min", "critical"],
  ["DestinoCaido (adicional)", "up == 0", "2 min", "warning"],
];
children.push(tabla(["Alerta", "Condición", "Durante", "Severidad"], filasAl, [2200, 4760, 1000, 1400], 16));
children.push(P("Alertmanager agrupa por alerta e instancia y notifica a un canal de Discord, incluidos los avisos de resolución. El webhook de Discord vive solo en `monitoring/alertmanager.yml` en la VM (ignorado por git); el repositorio contiene únicamente `alertmanager.example.yml`."));
children.push(...captura("15", "Las tres alertas recibidas en Discord"));
children.push(...captura("14", "Prometheus › Status › Targets con todos los destinos en UP"));

// 8. IA
children.push(H1("7. Uso de inteligencia artificial"));
children.push(P("Declaración obligatoria. Herramienta: **Claude Code** (agente de programación de Anthropic) en la app de escritorio de Claude, con los modelos Claude Sonnet 5.5 al inicio y Claude Opus 5.5 desde la revisión de Azure."));
children.push(tabla(["#", "Dónde se usó", "Herramienta", "Qué se le pidió", "Qué devolvió", "Qué se corrigió", "Justificación"],
  filasIA.map((f) => f.map(md)), [350, 1200, 1000, 1500, 1600, 2210, 1500], 13));
children.push(espacio());
prosaIA.forEach((t) => children.push(P(md(t))));

// 9. Evidencias
children.push(H1("8. Evidencias"));
children.push(P("Capturas del funcionamiento real. Cada build está identificado por su número en Jenkins y por el SHA del commit."));
[
  ["04", "Pipeline en rojo detenido por el Quality Gate (PR #4, cobertura 30.2 %): las etapas de imagen y despliegue aparecen saltadas"],
  ["05", "SonarQube: Quality Gate MediSur en Failed por cobertura"],
  ["06", "Pipeline en verde completo en main (CI + CD)"],
  ["07", "Paquete en GHCR con las etiquetas <VERSION>-<sha> y <sha>, sin latest"],
  ["08", "kubectl get pods -n medisur con 2 réplicas 1/1 Running"],
  ["09", "curl http://<IP-VM-K8S>:30080/version con el SHA desplegado"],
  ["10", "kubectl get pods -w durante la actualización gradual"],
  ["16", "kubectl rollout undo y /version con la versión anterior"],
  ["17", "El Jenkinsfile en GitHub y la protección de main con el check obligatorio"],
].forEach(([n, d]) => children.push(...captura(n, d)));

// 10. Decisiones
children.push(H1("9. Decisiones de diseño"));
children.push(P("Decisiones y desviaciones respecto al enunciado, con su motivo. Fuente: `docs/decisiones.md` del repositorio."));
children.push(tabla(["Tema", "Decisión", "Motivo"], filasDec.map((f) => f.map(md)), [1800, 3400, 4160], 14));
children.push(H2("Incidentes de secretos"));
children.push(tabla(["Fecha", "Secreto", "Qué pasó", "Acción"], filasInc.map((f) => f.map(md)), [1100, 2000, 3000, 3260], 15));
children.push(H2("Limitaciones conocidas"));
limitaciones.forEach((t) => children.push(bullet(md(t))));

// 11. Costos
children.push(H1("10. Control de costos"));
children.push(P("Consumo real del crédito de Azure for Students (100 USD), consultado con la API de Cost Management. Azure publica el consumo con un retraso de hasta 24 horas, así que **actualiza esta tabla con la cifra del portal justo antes de entregar**."));
children.push(tabla(["Concepto", "Grupo de recursos", "Costo (USD)"], [
  ["Almacenamiento (discos)", "rg-lab03-k8s", "2.18"],
  ["Red virtual e IP públicas", "rg-lab03-k8s", "2.97"],
  ["Cómputo de las VMs", "rg-lab03-k8s", "[pendiente de reflejarse]"],
  ["Total del mes al 25-nov-2026", "", "5.15 + cómputo"],
], [4000, 2800, 2560], 18));
children.push(espacio());
children.push(P("**Controles aplicados:**"));
[
  "Alerta de presupuesto de 50 USD en Cost Management (captura 02).",
  "Apagado automático diario a las 23:00 (hora de Monterrey) en ambas VMs. El autoapagado nativo de Azure no está disponible para VMs en mexicocentral, así que se implementó con un cron en VM-TOOLS que ejecuta `az vm deallocate` autenticado con una identidad administrada limitada al grupo de recursos.",
  "Las VMs siempre se detienen con deallocate (portal o CLI), nunca con `shutdown` desde el sistema operativo, para dejar de pagar el cómputo.",
  "Retención de Prometheus de 15 días, discos StandardSSD y tamaños B (de ráfaga).",
  "Al terminar el curso se borra el grupo de recursos completo.",
].forEach((t) => children.push(bullet(t)));
children.push(...captura("02", "Alerta de presupuesto de 50 USD y consumo actual en Cost Management"));

// 12. Conclusiones
children.push(H1("11. Conclusiones y lecciones aprendidas"));
children.push(P("El piloto demuestra un ciclo completo de entrega continua: un cambio en una rama dispara el pipeline sin intervención humana, la puerta de calidad detiene de verdad el código que no cumple (el PR de demostración con 30 % de cobertura nunca generó imagen ni llegó al clúster) y un merge a `main` actualiza la versión en producción sin que nadie se conecte por SSH, con reversión automática si la prueba de humo falla."));
children.push(H2("Lecciones aprendidas"));
[
  "**Verificar contra el sistema real, no contra la memoria.** Varias versiones \"conocidas\" ya no eran válidas: la llave del repositorio de Jenkins había caducado, Jenkins 2.580 exige Java 21 y la versión de kube-state-metrics debía coincidir con Kubernetes 1.35.",
  "**Un requisito de seguridad solo cuenta si se comprueba.** El ServiceAccount \"de solo lectura\" no lo era, porque MicroK8s tenía RBAC desactivado; se descubrió con `kubectl auth can-i` y se corrigió.",
  "**Las herramientas por defecto no siempre hacen lo que se espera.** SonarQube 10.7 agregó condiciones sobre código nuevo al Quality Gate, y GitHub marca `repo` completo al pedir `write:packages`.",
  "**Las puertas automáticas atrapan errores humanos y de la IA.** gitleaks detuvo un build por un comentario que citaba un patrón de credencial, y Trivy encontró un CVE real en una dependencia.",
  "**Los secretos se rotan, no se esconden.** El único token que se expuso se revocó de inmediato y quedó documentado.",
].forEach((t) => children.push(bullet(t)));
children.push(H2("Trabajo futuro"));
["Ingress con TLS (cert-manager) en lugar de NodePort.", "Estado persistente para `/api/items` (hoy cada réplica guarda el suyo en memoria).", "Actualizar SonarQube a una versión con soporte y migrar el Quality Gate al nuevo modo de calificación.", "GitOps con Argo CD y un entorno de staging."].forEach((t) => children.push(bullet(t)));

// 13. Anexos
children.push(H1("12. Anexos"));
children.push(H2("Enlaces"));
children.push(new Paragraph({ children: [new TextRun({ text: "Repositorio: ", bold: true }), new ExternalHyperlink({ link: "https://github.com/diegodaac/medisur-pilot", children: [new TextRun({ text: "https://github.com/diegodaac/medisur-pilot", style: "Hyperlink" })] })], spacing: { after: 80 } }));
children.push(new Paragraph({ children: [new TextRun({ text: "Video de respaldo (10 a 15 min): ", bold: true }), new TextRun({ text: "[pegar aquí el enlace al video]", color: "7A5C00", highlight: "yellow" })], spacing: { after: 80 } }));
children.push(new Paragraph({ children: [new TextRun({ text: "Imágenes: ", bold: true }), new TextRun("ghcr.io/diegodaac/medisur-pilot")], spacing: { after: 200 } }));
children.push(H2("Referencias"));
[
  "Enunciado del trabajo final: wiki del curso Cómputo en la Nube (github.com/jorgealbertopineda78-del/cloud-compute).",
  "Jenkins. Pipeline Syntax y Multibranch Pipeline. https://www.jenkins.io/doc/book/pipeline/",
  "SonarSource. SonarQube 10.7: Quality Gates y Web API. https://docs.sonarsource.com/sonarqube/10.7/",
  "Kubernetes. Deployments, probes y RBAC. https://kubernetes.io/docs/",
  "Canonical. MicroK8s: addons rbac y certificados. https://microk8s.io/docs",
  "kube-state-metrics: matriz de compatibilidad. https://github.com/kubernetes/kube-state-metrics",
  "Prometheus y Alertmanager: configuración y discord_configs. https://prometheus.io/docs/",
  "Grafana: provisionamiento de tableros. https://grafana.com/docs/grafana/latest/administration/provisioning/",
  "GitHub. Working with the Container registry. https://docs.github.com/packages",
  "Aqua Security Trivy, Gitleaks y Hadolint: documentación oficial de cada proyecto.",
  "Microsoft. Azure Cost Management y identidades administradas. https://learn.microsoft.com/azure/",
].forEach((t) => children.push(numero(t)));

const doc = new Document({
  creator: "Diego Alejandro Alvarado Castañón",
  title: "Automatización de entrega continua sobre Kubernetes — MediSur",
  description: "Trabajo final de Cómputo en la Nube (UANL FCFM)",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 32, bold: true, color: C.azul }, paragraph: { spacing: { before: 240, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 26, bold: true, color: "2E5C8A" }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
      { reference: "numeros", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "MediSur · Entrega continua sobre Kubernetes · ", size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "777777" })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("escrito", OUT, buf.length, "bytes"); });
