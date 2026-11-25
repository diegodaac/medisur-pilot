# syntax=docker/dockerfile:1

# ---------- Etapa 1: builder ----------
# Instala las dependencias fijadas en un venv aislado. Nada de esta etapa
# (pip, caches, herramientas de compilación) llega a la imagen final.
FROM python:3.12-slim AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---------- Etapa 2: imagen final ----------
FROM python:3.12-slim

# Usuario sin privilegios con UID/GID fijos (coincide con runAsUser del Deployment).
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv
WORKDIR /srv
COPY app ./app

# Metadatos de la versión: se inyectan al construir (docker build --build-arg ...)
# y la app los expone en /version y en la métrica app_info.
# Van al final para no invalidar la caché de las capas anteriores.
ARG APP_VERSION=dev
ARG GIT_SHA=unknown
ARG BUILD_DATE=unknown
ENV APP_VERSION=${APP_VERSION} \
    GIT_SHA=${GIT_SHA} \
    BUILD_DATE=${BUILD_DATE} \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

LABEL org.opencontainers.image.title="medisur-pilot" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.created="${BUILD_DATE}"

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=2)"]

CMD ["python", "-m", "app.main"]
