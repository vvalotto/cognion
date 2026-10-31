# Reporte — US-ADJ-64: Logging local — los emails de consola se ven y los tokens no quedan completos en el log

**Estado:** implementada en `feature/US-ADJ-64-logging-local` (2026-10-26), apilada sobre `fix/fechas-zona-horaria`. PR único al final de la Iteración 8.
**Issue:** [#570](https://github.com/vvalotto/cognion/issues/570) · **Spec:** `docs/specs/ajustes/US-ADJ-64.md` · **Origen:** hallazgos #2 (🔴) y #9 de la UAT de `v0.9.0`

## Qué se hizo
- `src/shared/frameworks/logging_config.py`: `configurar_logging()` pone un handler en el logger `src` (los `INFO` de la aplicación ya no se descartan) y `FiltroTokens` enmascara `token=<valor>` y `/recuperar-password/<token>` en `uvicorn.access` y `uvicorn.error`, tanto en el mensaje como en los argumentos. Es idempotente y conserva `propagate`.
- `src/settings.py`: `LOG_LEVEL` (`DEBUG|INFO|WARNING|ERROR`, por defecto `INFO`); un valor inválido falla al arrancar y lista los válidos.
- `src/app.py`: una línea que llama a `configurar_logging` al importar (cubre `src.app:app` y `src.servidor:servidor`). `.env.example` documenta la variable.
- Sin cambios en dominio, casos de uso, routers ni frontend.

## Decisiones
- **Ampliación de la spec** (aprobada en la Fase 2): también se enmascara el link de recuperación, que lleva el token en la **ruta** (`/recuperar-password/<token>`) y no en `?token=`; sin tocar `solicitar` ni `confirmar` de la API.
- El cuerpo de los emails de consola conserva los tokens completos: es lo que permite recuperar una cuenta sin correo.
- Las pruebas leen la salida de un `uvicorn` real; `caplog`, que dejó pasar el error original, no alcanza.

## Hallazgo al implementar
El email de invitación trae el **token suelto** ("Token de invitación: …") y no un link, contra lo que decía la spec. No se cambió el email (fuera de alcance); la guía explica cómo armar el link o generarlo desde la pantalla de la Comisión.

## Calidad
Suite completa 2130 pasaron, 0 fallos (contra una base descartable); 24 tests unitarios, 8 de integración con un `uvicorn` real y 10 casos BDD. Sin la configuración fallan 7 de los 8 de integración (el octavo es el de regresión del health check). Pylint 10,00/10, `mypy` y `ruff` limpios, CodeGuard sin advertencias reales en los archivos propios, DesignReviewer 0 bloqueantes. `logging_config.py` queda fuera de la medición de cobertura por la configuración del proyecto (`src/*/frameworks/*`). Evidencia: `quality/reports/inc8/US-ADJ-64-quality.json`.

## Pendiente
- Verificar en tu instalación local (`levantar.sh`) que el email de recuperación aparece en `logs/uat/` y que no hay JWT completos: es parte de repetir los pasos C7 y D1 de la UAT (paso 5 de la iteración).
- Eliminar la base descartable `cognion_test_adj64` al cerrar la iteración.
