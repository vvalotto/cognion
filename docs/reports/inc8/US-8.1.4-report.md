# Reporte — US-8.1.4: Migraciones Alembic como paso explícito de release

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1.
**Issue:** #517 · **Spec:** `docs/specs/inc8/US-8.1.4.md`

## Qué se hizo
- `Dockerfile`: la imagen ahora incluye `alembic.ini` y `migrations/` (antes solo copiaba `src/`, así que no podía migrar). El `CMD` sigue siendo solo `uvicorn`.
- `fly.toml` mínimo: `[deploy] release_command = "uv run alembic upgrade head"` (corre antes de reemplazar la versión; si falla, el deploy se aborta y la anterior sigue sirviendo) y servicio HTTP en 8000, HTTPS forzado, healthcheck `/health`.
- `tests/uat/inc8/verificar_migraciones.sh`: crea una base descartable propia, verifica vacía→head, idempotencia y fallo con base inaccesible, y la borra al terminar. Toma las credenciales del `DATABASE_URL` local; crear/borrar la base usa el usuario admin del SO (`PGADMIN_USER` lo cambia). Lo reutiliza `US-8.4.3`.
- 5 tests unitarios estáticos (imagen, `CMD`, `fly.toml`, y que ningún módulo de `src/` use Alembic).

## Verificación real
`verificar_migraciones.sh` contra Postgres local: 3/3 OK (vacía → `c4d1f9a27b60`, segunda corrida exit 0, base inaccesible exit ≠ 0); sin bases residuales.

## Decisiones y límites
- Sin `.feature` (infra técnica, mismo precedente que el resto de la iteración).
- El `release_command` corre con la misma `Settings` que la app: en `ENTORNO=staging|produccion` exige todas las variables válidas (`US-8.1.3`), incluso para migrar. Es deliberado: una configuración inválida aborta el release.
- **No verificado:** el build de la imagen (no hay Docker local) ni un `fly deploy` real; eso lo cubren `US-8.2.1`/`US-8.2.2`. `app = "cognion"` en `fly.toml` es provisorio.
