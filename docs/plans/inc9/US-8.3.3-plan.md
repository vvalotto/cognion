# Plan de Implementación: US-8.3.3 - Observabilidad mínima: logs estructurados y healthcheck de readiness

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** transversal (`shared`) y la aplicación (`src/app.py`) · **Capas:** `frameworks` y `deploy/`

## Diseño
Son dos piezas independientes que comparten la US: un chequeo de la base y un formato de log. Ninguna toca los BC, los casos de uso ni el frontend.

```
GET /health          → {"status": "ok"}                              (sin cambios, no mira la base)
GET /health/ready    → salud.base_disponible()   (SELECT 1, tope 2 s)
        ├─ ok     → 200 {"status": "ok", "base_de_datos": "ok"}
        └─ falla  → 503 {"status": "error", "base_de_datos": "no disponible"}   (el error real va al log, sin credenciales)

settings.log_format ("texto" | "json")  ──►  configurar_logging(nivel, formato)
        ├─ texto → handler y formato de hoy
        └─ json  → FormateadorJson sobre el handler de `src` y sobre los de `uvicorn.access` / `uvicorn.error`
                    {"ts", "nivel", "logger", "mensaje"[, "excepcion"]}  — una línea; vuelve a enmascarar tokens
```

- **Readiness inyectable:** el endpoint depende de una función `comprobar_base` (con `Depends`), de modo que los tests de la API usan `app.dependency_overrides` y la prueba real usa un `uvicorn` apuntado a una base inexistente; nunca se apaga la base de desarrollo.
- **Sin credenciales en el log:** el error de conexión se escribe con una función que elimina el `usuario:clave@` de cualquier URL.
- **El filtro no alcanza:** `FiltroTokens` sanea `msg` y `args`; el formateador JSON enmascara de nuevo el mensaje ya formateado y el traceback.

## Componentes a Implementar

### 1. Salud (`src/shared/frameworks/salud.py`, nuevo)
- [ ] `base_disponible(tiempo_maximo=2.0) -> bool`: `SELECT 1` con `SessionLocal` y `asyncio.wait_for`; ante cualquier excepción o tiempo agotado registra `ERROR` (sin credenciales) y devuelve `False`.

### 2. Aplicación (`src/app.py`)
- [ ] `GET /health/ready` con `Depends(comprobar_base)`; `200` o `503` según corresponda. Docstring que aclare la diferencia con `/health`.

### 3. Logging (`src/shared/frameworks/logging_config.py`, `src/settings.py`)
- [ ] `FormateadorJson` (`ts` UTC ISO 8601, `nivel`, `logger`, `mensaje`, `excepcion`); enmascara el mensaje y el traceback.
- [ ] `configurar_logging(nivel, formato="texto")`: idempotente; en `json` cambia el formatter de los handlers existentes de `uvicorn`.
- [ ] `Settings.log_format: Literal["texto", "json"] = "texto"`; `src/app.py` lo pasa a `configurar_logging`.

### 4. Operación (`deploy/gcp/`)
- [ ] `salud.sh` (nuevo) con `mostrar_salud <url_base>`: consulta `/api/health` y `/api/health/ready`, imprime las dos respuestas con su código y marca el `503`; sin ocultar la primera si la segunda falla.
- [ ] `cognion.sh estado` usa `mostrar_salud` en lugar del `curl` único.

### 5. Documentación y configuración
- [ ] `LOG_FORMAT` en `.env.example` y, comentada, en `deploy/gcp/.env.example`; una línea en `docs/plans/DESPLIEGUE-LOCAL.md` y en la guía de GCP.

### 6. Sin cambios
`docker-compose.yml` (el healthcheck sigue en `/api/health`), `desplegar.sh`, los BC, `frontend/`.

## Tests (Fases 4 a 6)
- **Unitarios (sin base):** `FormateadorJson` (campos, una sola línea con excepción, tokens enmascarados en `mensaje` y `excepcion`, caracteres especiales), `configurar_logging` en ambos formatos e idempotencia, `Settings.log_format` válido e inválido, `base_disponible` con una sesión que responde, que falla y que se cuelga (tiempo agotado), eliminación de credenciales del texto de error.
- **Integración (base descartable inline):** `/health/ready` por HTTP con la base real (`200`) y con la dependencia en falla (`503`, cuerpo sin motivo ni credenciales); `/health` con la base caída; sin `Authorization`; `ServidorReal` con `LOG_FORMAT=json` (líneas de `uvicorn.access` en JSON, token enmascarado, texto por defecto sin cambios) y con `LOG_FORMAT=xml` (no arranca, mensaje claro); `ServidorReal` con `DATABASE_URL` hacia una base inexistente: `/health` `200` y `/health/ready` `503`.
- **BDD (`tests/step_defs/inc9/test_us_8_3_3_steps.py`):** los 10 escenarios aprobados; el de `cognion.sh estado` con `curl` simulado en el `PATH`.
- **Que los tests detectan el error:** con el código anterior deben fallar los escenarios de readiness, `json` y `estado`; los de texto por defecto y `/health` pasan en ambos.

## Documentación (Fase 8)
- Docstrings de `salud.py`, `logging_config.py` y del endpoint.
- Variable `LOG_FORMAT` en los `.env.example` y las guías de despliegue; nota en `CLAUDE.md` si cambia algún comando operativo.
