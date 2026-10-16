# Plan de Implementación — US-8.1.4

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | Copiar `alembic.ini` y `migrations/` a la imagen | `Dockerfile` |
| 2 | `fly.toml` mínimo con `release_command` y servicio HTTP | `fly.toml` |
| 3 | Tests estáticos: Dockerfile, CMD sin Alembic, `fly.toml`, app sin Alembic | `tests/unit/inc8/test_us_8_1_4_migraciones_release.py` |
| 4 | Script de verificación contra base descartable (vacía→head, idempotencia, base inaccesible) | `tests/uat/inc8/verificar_migraciones.sh` |
| 5 | Ejecutar el script contra una base descartable real y registrar la evidencia | reporte |

Sin cambios de dominio ni frontend. No se toca la base de desarrollo: el script crea y borra su propia base.
