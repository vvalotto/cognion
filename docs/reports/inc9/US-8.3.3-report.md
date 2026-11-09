# Reporte — US-8.3.3: Observabilidad mínima: logs estructurados y healthcheck de readiness

**Estado:** implementada en `feature/inc-9-iter-3-guardas-y-observabilidad` (2026-11-08); el PR sale al cierre de la Iteración 3.
**Issue:** [#526](https://github.com/vvalotto/cognion/issues/526) · **Spec:** `docs/specs/inc8/US-8.3.3.md` · **Origen:** plan del Incremento 8; decisiones de Víctor del 2026-11-08

## Qué se hizo
- **Readiness:** `GET /health/ready` (`src/app.py`) comprueba la base con `SELECT 1` y un tope de 2 s (`src/shared/frameworks/salud.py`). `200` con `{"status": "ok", "base_de_datos": "ok"}`; `503` con `{"status": "error", "base_de_datos": "no disponible"}`, sin motivo, URL ni clave. El error real va al log con la URL y la contraseña configurada ya reemplazadas por `***`. `/health` no cambia y ninguno pide autenticación.
- **Logs estructurados:** `LOG_FORMAT=texto|json` (`settings.log_format`, por defecto `texto`). `FormateadorJson` escribe un objeto por línea (`ts`, `nivel`, `logger`, `mensaje` y `excepcion` si hay) y vuelve a enmascarar tokens en el mensaje y en el traceback. Alcanza a `src.*` y a `uvicorn`. Un valor inválido impide arrancar.
- **Operación:** `deploy/gcp/salud.sh` (`mostrar_salud`) y `cognion.sh estado` muestran `/api/health` y `/api/health/ready`, marcando el `503` sin ocultar el `200`.
- **Documentación:** `LOG_FORMAT` en los dos `.env.example` y en las guías local y de GCP.

## Decisiones
- Readiness como endpoint nuevo y `/health` intacto: el healthcheck de Docker y el arranque de Caddy no cambian (Víctor, 2026-11-08). Pasar Docker a `/health/ready` queda para cuando se retome GCP.
- El chequeo es una dependencia de FastAPI (`comprobar_base`): los tests usan `dependency_overrides` y la prueba real apunta un `uvicorn` a una base inexistente; nunca se apaga la base de desarrollo.
- `configurar_logging` se partió en tres funciones auxiliares al superar la complejidad 10.

## Hallazgos al probar
- `uvicorn.error` no tiene handler propio: usa el del logger `uvicorn`. Cambiar solo los handlers de `uvicorn.access` y `uvicorn.error` dejaba los mensajes de arranque en texto; lo destapó la prueba con un `uvicorn` real.
- `cognion.sh` ahora carga `salud.sh` con `source`: los tests de despliegue que copian solo `cognion.sh` a una carpeta aislada fallaron (13) hasta copiar también ese archivo.
- Un `black` sobre todo `tests/` reformateó archivos de otras US; se revirtieron antes de commitear.

## Calidad
22 unitarios, 9 de integración y 10 escenarios BDD en verde; 228 unitarios de `inc8` y la suite unitaria completa pasan. `pylint` 10,00/10, `mypy` 0 errores (324 archivos), `ruff`/`black`/`isort` limpios, 4 contratos de `import-linter` cumplidos. Los módulos de `frameworks` no se miden en la cobertura por configuración del proyecto. La suite completa se corre una sola vez al cerrar la Iteración 3. Evidencia: `quality/reports/inc9/US-8.3.3-quality.json`.

## Tiempo
Ver `.claude/tracking/US-8.3.3-tracking.json`.

## Pendiente
- Verificar `cognion.sh estado` contra la VM real cuando se retome el despliegue (hoy solo con `curl` simulado).
- Eliminar la base descartable `cognion_adj69_descartable` al cerrar la iteración.
