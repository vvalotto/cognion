# Plan de Implementación: US-ADJ-64 - Logging local: los emails de consola se ven y los tokens no quedan completos en el log

**Patrón:** clean-architecture-bc · **Producto:** cognion · **Capa:** `shared/frameworks` (infraestructura transversal)

## Diseño
`uvicorn` configura solo sus loggers (`uvicorn`, `uvicorn.error`, `uvicorn.access`); los de la aplicación (`src.*`) quedan sin handler y sus `INFO` se descartan. La corrección es una configuración de logging aplicada una vez al importar la aplicación, más un filtro que enmascara los tokens en las líneas de acceso.

- **Verificado en `uvicorn` 0.51:** las líneas `WebSocket <ruta>?token=… [accepted]` salen por `uvicorn.error` (con la ruta como argumento) y las de acceso HTTP por `uvicorn.access` (la ruta es un argumento). El filtro debe sanear **mensaje y argumentos** de los dos loggers.
- **Handler solo en el logger `src`**, con `propagate=True`: `caplog` sigue funcionando y, en un `uvicorn` real, el logger raíz no tiene handlers, así que no hay líneas duplicadas.
- **Idempotente:** importar `src.app` más de una vez (tests) no agrega handlers ni filtros repetidos.

**Una decisión que sumo respecto de la spec:** el link de recuperación es `/recuperar-password/<token>` (token en la **ruta**, no en `?token=`), así que al abrirlo aparece completo en el log de acceso. El filtro lo enmascara también (`/recuperar-password/***`), sin tocar las rutas de la API `/recuperar-password/solicitar` y `/confirmar`. Cubre la misma intención de la spec (que el log no guarde tokens) y se prueba con tests unitarios.

## Componentes a Implementar

### 1. Configuración
- [ ] `src/settings.py`: campo `log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"` (un valor inválido falla al arrancar y Pydantic lista los válidos).
- [ ] `.env.example`: documentar `LOG_LEVEL`.

### 2. Módulo de logging (`src/shared/frameworks/logging_config.py`)
- [ ] `enmascarar_tokens(texto) -> str`: `token=<valor>` → `token=***` y `/recuperar-password/<token>` → `/recuperar-password/***` (sin tocar `solicitar` ni `confirmar`).
- [ ] `FiltroTokens(logging.Filter)`: sanea `record.msg` y cada argumento de texto (tupla o dict) y devuelve siempre `True` (no descarta líneas).
- [ ] `configurar_logging(nivel: str) -> None`: nivel y `StreamHandler` (stderr, formato `INFO:     mensaje`) en el logger `src`; `FiltroTokens` en `uvicorn.access` y `uvicorn.error`; idempotente.

### 3. Integración
- [ ] `src/app.py`: llamar `configurar_logging(settings.log_level)` al importar, antes de crear los routers/lifespan.
- [ ] Sin cambios en dominio, casos de uso, routers ni frontend.

## Tests (Fases 4 a 6)
- **Unitarios:** `enmascarar_tokens` (query, ruta de recuperación, rutas de la API sin tocar, varios tokens, sin token); `FiltroTokens` (mensaje, argumentos tupla, no descarta); `configurar_logging` (nivel, idempotencia, el logger de smtp emite a stderr); `Settings.log_level` (válidos e inválido).
- **Integración:** helper que arranca `python -m uvicorn src.app:app` como subproceso real contra una **base descartable** y captura su salida; recuperar contraseña, invitación por email, aviso de actividad, WebSocket con token válido e inválido, `GET /registro?token=`, health check.
- **BDD:** los 8 escenarios aprobados, reutilizando el helper.

## Riesgos
- **Una línea duplicada** si algún entorno agrega un handler al logger raíz: se cubre con `propagate=True` y el caso de uso real (raíz sin handlers).
- **Orden de configuración de `uvicorn`:** `uvicorn` aplica su `dictConfig` antes de importar la app, así que el filtro agregado después persiste. Se verifica con el subproceso real, no solo con tests unitarios.
- **Las pruebas con subproceso necesitan puerto libre y base descartable:** puerto elegido al azar, `DATABASE_URL` inline, nunca `cognion_local` ni `cognion_uat`.
