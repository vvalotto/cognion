# Stage 1: Frontend build
FROM node:22.23.5-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ .
# URL base de la API embebida en el build: `/api` = mismo origen, la API montada bajo /api (US-8.1.2, US-8.1.6)
ARG VITE_API_BASE_URL="/api"
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: Runtime
FROM python:3.12.16-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Versión fija de uv (la que se usó para verificar la imagen): una imagen reconstruida no cambia de herramienta sola (DO-01).
# El CI instala el uv más reciente; subir esta versión es un cambio deliberado, no automático.
RUN pip install --no-cache-dir uv==0.9.18 && uv sync --frozen --no-dev
COPY src/ ./src/
# Migraciones: se aplican como paso de release (`cognion.sh desplegar`), nunca al arrancar la app (US-8.1.4)
COPY alembic.ini ./
# Versión única del proyecto (US-10.2.1): `GET /api/health` la informa
COPY VERSION ./
COPY migrations/ ./migrations/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
ENV PYTHONPATH=/app/src
# El entorno virtual ya quedó armado por `uv sync`: se usa directo (`uvicorn`, `alembic`, `python`). `uv run` al arrancar
# podría intentar sincronizar dependencias (incluidas las de desarrollo) y necesitar red (US-8.6.2, ADR-025).
ENV PATH="/app/.venv/bin:$PATH"
# Usuario sin privilegios (DO-01): la aplicación no escribe en disco (el estado vive en PostgreSQL), así que le alcanza con leer /app
RUN useradd --system --no-create-home --uid 10001 cognion
USER cognion
EXPOSE 8000
# `--proxy-headers`: detrás de un proxy (Caddy) las redirecciones deben conservar https (US-8.1.6). Solo se confían las
# cabeceras `X-Forwarded-*` de los proxies listados en la variable `FORWARDED_ALLOW_IPS` (el compose pone la red interna);
# sin esa variable uvicorn solo confía en 127.0.0.1 (DO-01).
# UN SOLO PROCESO (`US-12.2.5`, `IM-05`): no agregar `--workers` ni `WEB_CONCURRENCY`. El canal de la sesión en vivo guarda las
# conexiones en la memoria del proceso (con dos procesos, parte de los alumnos no recibe los mensajes) y el pool de conexiones
# de la base y el event loop son de un único proceso. El verificador de vencimientos sí se protege solo con un bloqueo de PostgreSQL.
CMD ["uvicorn", "src.servidor:servidor", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
