# Plan de Implementación — US-8.6.2

## Tareas
1. `deploy/gcp/docker-compose.yml`: tres servicios.
   - `db` (`postgres:16`): sin `ports`, volumen nombrado, `mem_limit`, healthcheck, reinicio `unless-stopped`, ajuste para 1 GB
     (`shared_buffers=64MB`, `work_mem=2MB`, `maintenance_work_mem=32MB`, `effective_cache_size=256MB`, `max_connections=100`).
   - `app` (imagen por `COGNION_IMAGE`): sin `ports`, `mem_limit`, healthcheck sobre `/api/health`, `depends_on` con `db` sano, `env_file`.
   - `caddy` (`caddy:2`): único con `ports` 80/443, certificados en volumen, `reverse_proxy app:8000`.
   - Todos con `logging` json-file rotado (10 MB × 3) y reinicio automático.
2. `deploy/gcp/Caddyfile`: `{$COGNION_DOMINIO}` → `reverse_proxy app:8000` (HTTPS automático; los WebSockets pasan sin configuración extra).
3. `deploy/gcp/.env.example`: plantilla sin valores reales (`ENTORNO=local`, `EMAIL_MODO=consola`, URLs derivadas del dominio, `POSTGRES_PASSWORD`, `SECRET_KEY`).
4. `deploy/gcp/preparar-env.sh`: genera `.env` con secretos aleatorios, `chmod 600`, idempotente (no pisa un `.env` existente), pide el dominio.
5. `deploy/gcp/cognion.sh`: `iniciar` (db → migraciones como paso explícito → app y caddy), `migrar`, `administrador` (bootstrap con contraseña por terminal), `estado`, `logs`, `detener`.
6. `Dockerfile`: reemplazar `uv run uvicorn` por `uvicorn` del entorno ya instalado (`PATH` a `/app/.venv/bin`), para que el arranque no intente sincronizar dependencias.
7. `.github/workflows/imagen-smoke.yml`: se dispara solo si cambian `Dockerfile`, `deploy/**`, `pyproject.toml`, `uv.lock` o el propio workflow (y a mano). Construye la imagen, levanta la composición con dominio `localhost`, y verifica: `/api/health` por HTTPS, migraciones aplicadas, Postgres sin puerto publicado, límites de memoria aplicados, reinicio de un contenedor caído, secretos ausentes del log, y registra la memoria en reposo.
8. `tests/unit/inc8/test_us_8_6_2_composicion_gcp.py`: validación estática con PyYAML (límites, reinicio, rotación de logs, puertos, healthchecks, plantilla sin secretos, `Dockerfile` sin `uv run` en el arranque, Caddyfile).

## Riesgos y decisiones a validar
- **`NullPool` (ADR-018):** cada operación abre una conexión, así que con 60 alumnos puede haber ~60 simultáneas. `max_connections=100` es un punto de partida a medir en `US-8.6.7`, no un valor probado. No se cambia el `NullPool` en esta US.
- **Límites de memoria como techo, no reserva:** app 300 MB, db 300 MB, caddy 64 MB. Se reajustan con la medición real.
- **Docker en la Mac:** no existe; la verificación de runtime depende de CI y de la VM. Un fallo en el workflow se corrige y se vuelve a empujar, sin la VM de por medio.
- **Estas cosas no se pueden probar sin la VM:** reinicio tras reiniciar la VM, memoria real en 1 GB y el puerto de PostgreSQL visto desde internet.
