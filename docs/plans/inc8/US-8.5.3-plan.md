# Plan de Implementación — US-8.5.3

## Tareas
1. `.gitignore`: agregar `.env.local` (hoy `.env`/`*.env` no lo cubren). `logs/` ya está ignorado.
2. `scripts/local/levantar.sh` (idempotente, `--fondo` opcional), en 7 pasos según la spec:
   prerrequisitos con mensaje accionable (sin traza); `.env.local` en primera vez (SECRET_KEY por
   `openssl rand -hex 32`, `ENTORNO=local`, `EMAIL_MODO=consola`, `DATABASE_URL` a `cognion_local`, base creada
   con los mismos usuario/host que el `.env` de desarrollo pero nombre propio, jamás `cognion`); build del
   frontend con `VITE_API_BASE_URL=/api` si `dist` falta o es más viejo que `frontend/src`; `alembic upgrade
   head`; bootstrap del Administrador solo si no hay uno (consulta SQL; contraseña por terminal sin eco);
   IP (`ipconfig getifaddr`) y `<equipo>.local`, `FRONTEND_URL` + `CORS_ALLOWED_ORIGINS` con esa IP, y se
   imprimen las URLs y el recordatorio de red; `uvicorn src.servidor:servidor --host 0.0.0.0 --port 8000`
   bajo `caffeinate -dims`, log a `logs/local/uvicorn-<fecha>.log` con `tee` (en `--fondo`, nohup + PID).
3. `scripts/local/detener.sh`: lee el PID, detiene el servidor (y su `caffeinate`), limpia el archivo de PID.
4. `tests/uat/inc8/verificar_levantar_local.sh`: corre `levantar.sh --fondo` en un directorio de trabajo
   aislado (`COGNION_LOCAL_BASE`/`COGNION_LOCAL_PUERTO` sobreescribibles → base y puerto descartables), y
   verifica los escenarios 1-4 (+5 con la IP local desde esta máquina): `/`, `/api/health`, login del
   Administrador, segunda ejecución sin pisar, Postgres inaccesible → exit ≠ 0 sin traza, la base `cognion`
   intacta (huella antes/después). Limpia al terminar.

## Riesgos
- Idempotencia: `.env.local` y el Administrador nunca se pisan.
- La verificación crea/borra solo bases propias; el script acepta `COGNION_LOCAL_BASE` para no usar `cognion_local`.
- El escenario 5 desde otro dispositivo no es automatizable; queda como paso manual en la guía (`US-8.5.6`).
