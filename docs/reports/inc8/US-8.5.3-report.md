# Reporte — US-8.5.3: Comando único para levantar y detener el despliegue local

**Estado:** implementada en `feature/US-8.5.1-entorno-local` (2026-10-18), apilada sobre `US-8.5.1`/`8.5.2`. PR diferido al cierre de la Iteración 5 (CI lento).
**Issue:** #538 · **Spec:** `docs/specs/inc8/US-8.5.3.md`

## Qué se hizo
- `scripts/local/levantar.sh` (idempotente, `--fondo` opcional): prerrequisitos con mensajes accionables y sin traza; base propia `cognion_local` (nunca la de desarrollo, con guard explícito); `.env.local` en la primera vez (`ENTORNO=local`, `EMAIL_MODO=consola`, `SECRET_KEY` de `openssl rand -hex 32`, permisos 600); build del frontend con `VITE_API_BASE_URL=/api` solo si falta o está viejo; `alembic upgrade head`; bootstrap del Administrador solo si no hay uno operativo; IP y `<equipo>.local` con `FRONTEND_URL`/CORS; `uvicorn` en `0.0.0.0` bajo `caffeinate -dims` con log en `logs/local/`. Imprime las URLs para los alumnos y el recordatorio de red.
- `scripts/local/detener.sh`: detiene el servidor en segundo plano y espera el cierre para dejar el puerto libre.
- `tests/uat/inc8/verificar_levantar_local.sh`: verificación con base y puerto descartables.
- `.gitignore`: `.env.local`.

## Hallazgos durante la verificación (corregidos)
1. Una ruta absoluta en `COGNION_LOCAL_ENV` rompía la carga del archivo.
2. El guard de la base de desarrollo comparaba contra la URL de `.env.local` y rechazaba la propia base en la segunda ejecución.
3. `detener.sh` no esperaba al cierre y la segunda ejecución encontraba el puerto ocupado.

## Decisiones
- Sin `.feature` ni pytest: tooling de shell, verificado con un script propio (mismo precedente que `verificar_migraciones.sh`).
- El acceso desde otro dispositivo de la red no se automatiza: queda como paso manual en la guía (`US-8.5.6`). El escenario 5 se verificó por la IP local desde esta misma máquina.

## Calidad
Verificación 12/12 OK; huella de la base de desarrollo idéntica antes y después; sin bases ni procesos huérfanos; `tests/unit/inc8` 68/68; designreviewer 0 blocking. `shellcheck` no está instalado: solo `bash -n`. Evidencia en `quality/reports/inc8/US-8.5.3-quality.json`.
