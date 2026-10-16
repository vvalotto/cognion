# Stage 1: Frontend build
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ .
# URL base de la API embebida en el build: `/api` = mismo origen, la API montada bajo /api (US-8.1.2, US-8.1.6)
ARG VITE_API_BASE_URL="/api"
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY src/ ./src/
# Migraciones: se aplican como paso de release (fly.toml `release_command`), nunca al arrancar la app (US-8.1.4)
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
ENV PYTHONPATH=/app/src
EXPOSE 8000
# `--proxy-headers`: detrás del proxy de Fly las redirecciones deben conservar https (US-8.1.6)
CMD ["uv", "run", "uvicorn", "src.servidor:servidor", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
