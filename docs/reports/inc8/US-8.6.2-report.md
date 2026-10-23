# Reporte — US-8.6.2: Composición de servicios y configuración de la VM

**Estado:** implementada en `feature/US-8.6.2-composicion-servicios` (2026-10-23). PR diferido al cierre de la Iteración 6 (CI lento).
**Issue:** #546 · **Spec:** `docs/specs/inc8/US-8.6.2.md` · **Decisiones:** `ADR-025`

## Qué se hizo
- `deploy/gcp/docker-compose.yml`: PostgreSQL 16, la aplicación (imagen de CI) y Caddy. Solo Caddy publica puertos (80/443); la base y la aplicación quedan en la red interna. Cada servicio con techo de memoria (db 300 MB, app 300 MB, caddy 64 MB), reinicio `unless-stopped`, healthcheck donde corresponde y logs rotados (10 MB × 3). PostgreSQL ajustado para 1 GB (`shared_buffers=64MB`, `work_mem=2MB`, `max_connections=100`).
- `deploy/gcp/Caddyfile`: HTTPS automático para el dominio de DuckDNS, reenviando a `app:8000` (los WebSockets pasan sin configuración extra).
- `deploy/gcp/.env.example` + `preparar-env.sh`: plantilla con marcadores y generador idempotente de `.env` con secretos aleatorios y permisos 600, sin imprimirlos. `ENTORNO=local`, `EMAIL_MODO=consola` (ADR-025, decisión 2).
- `deploy/gcp/cognion.sh`: `iniciar` (base → migraciones como paso explícito → aplicación y proxy), `migrar`, `administrador` (bootstrap con contraseña por terminal), `estado`, `logs`, `detener`.
- `Dockerfile`: el arranque pasa de `uv run uvicorn` a `uvicorn` del entorno virtual ya instalado (`PATH` a `/app/.venv/bin`).
- `.github/workflows/imagen-smoke.yml` + `tests/uat/inc8/verificar_composicion_gcp.sh`: construye la imagen, levanta la composición completa (dominio `localhost`, certificado interno) y verifica 12 puntos. Se dispara por `push` a ramas que no sean `main`/`develop`, filtrado por rutas, para no alargar el CI de los demás cambios. El script es reutilizable en la VM.
- 23 tests estáticos (PyYAML) en `tests/unit/inc8/test_us_8_6_2_composicion_gcp.py`.

## Hallazgos durante la verificación
1. **`docker kill` no activa la política de reinicio.** Docker lo trata como una detención manual: el contenedor quedó en `Exited (137)` y no volvió. Una caída real se simula matando el proceso desde el host.
2. **Mandar `SIGTERM` al PID 1 desde dentro del contenedor no lo mata** (el núcleo lo ignora): la aplicación seguía viva y `RestartCount` quedaba en 0.
3. **El primer request tras arrancar Caddy puede fallar:** la verificación reintenta hasta 40 s.
4. **La hipótesis del `uv run` no se confirmó como bloqueo** (la imagen arrancaba y migraba), pero el cambio es más limpio y evita depender de la red al arrancar.

## Decisiones
- Sin `.feature` ni pytest de integración (tooling, mismo precedente que `US-8.5.x`); la verificación de runtime corre en CI.
- No se cambió el `NullPool` (ADR-018): con 60 alumnos puede haber ~60 conexiones simultáneas, por eso `max_connections=100`. Es un valor inicial a medir en `US-8.6.7`.
- No se tocó `fly.toml` (`release_command = "uv run alembic …"` sigue funcionando; Fly.io sigue en standby).

## Calidad
Verificación en CI 12/12 (run 39946600794): health por HTTPS, migraciones, sin puertos publicados (db, app, 5432), límites y reinicio en los 3 servicios, caída real recuperada, reinicio de Docker, secretos fuera de logs, Administrador y login. Memoria en reposo ~115 MiB (Caddy 17, app 78, db 20). `tests/unit/inc8` 91/91, `pylint` 10.00, `ruff`/`black`/`mypy` limpios, `designreviewer` 0 blocking. CodeGuard full: errores solo de tooling. `shellcheck` y `hadolint` no instalados: solo `bash -n`. Evidencia en `quality/reports/inc8/US-8.6.2-*.json`.

## Pendiente hasta la VM
Reinicio real de la máquina, memoria total con sistema operativo y Docker en 1 GB, el puerto de PostgreSQL visto desde internet y el certificado real de DuckDNS (`US-8.6.3`, `8.6.6`, `8.6.7`).
