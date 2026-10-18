# Plan de Implementación — US-8.5.1

## Tareas
1. `src/settings.py`: `entorno` admite `"local"`. Extraer la validación del secreto a un helper
   (`_errores_secreto`) usado por `local` y por staging/producción; `local` valida solo el secreto.
   `desarrollo`, `staging` y `produccion` sin cambios de comportamiento ni de mensaje.
2. `.env.example`: documentar `ENTORNO=local` (valores, para qué sirve, que exige `SECRET_KEY` fuerte).
3. `tests/unit/inc8/test_us_8_5_1_entorno_local.py`: los 5 escenarios de la spec, más que el mensaje
   no incluya el valor del secreto.

## Riesgos
- Cuidar que el refactor no cambie el mensaje de staging/producción (cubierto por los tests de `US-8.1.3`).
- CBO/CC de `Settings`: el helper reduce la complejidad del validador existente.
