# Plan de Implementación — US-8.1.3

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | `entorno: Literal[...]` + `model_validator(mode="after")` que acumula violaciones en staging/produccion | `src/settings.py` |
| 2 | Tests unitarios de los 5 escenarios + cada regla individual | `tests/unit/inc8/test_us_8_1_3_settings_produccion.py` |
| 3 | Documentar `ENTORNO` y reglas en `.env.example` | `.env.example` |

Sin cambios de dominio ni frontend. Verificación: pytest unit, ruff, mypy, pylint, CodeGuard full.
