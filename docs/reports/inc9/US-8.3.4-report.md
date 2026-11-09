# Reporte — US-8.3.4: `alembic downgrade base` funciona

**Estado:** implementada en `feature/inc-9-iter-1-correcciones` (2026-11-07), un commit por US; el PR sale al cierre de la Iteración 1.
**Issue:** [#527](https://github.com/vvalotto/cognion/issues/527) · **Spec:** `docs/specs/inc8/US-8.3.4.md` · **Origen:** hallazgo verificado el 2026-11-07 al revisar los Issues pendientes

## Qué se hizo
- `migrations/versions/dd44a181d7fc_estudiante_comision_id.py`: el `downgrade` pasa de `op.drop_constraint(None, ...)` a `op.drop_constraint("estudiante_comision_id_fkey", "estudiante", type_="foreignkey")`. El `upgrade` no cambia, así que las bases ya migradas (la local y la de la VM de GCP) no se tocan. Es la única de las 18 migraciones con ese patrón.
- `tests/uat/inc8/verificar_migraciones.sh`: pasos nuevos 5a a 5c (`downgrade base` con datos cargados, sin tablas restantes, `upgrade head` otra vez).
- Sin cambios en `src/`, API ni frontend.

## Decisiones
- **Guarda que no estaba en la spec:** `tests/unit/inc9/test_us_8_3_4_migraciones_con_nombre.py` falla si el `downgrade` de alguna migración llama `drop_constraint(None, ...)`. Alembic autogenera `None` por defecto, así que el mismo error volvería con la próxima migración que agregue una clave foránea.
- **Los escenarios BDD ejecutan `alembic` real** sobre una base descartable propia (`cognion_mig_<id>`), que crean y borran. Para crearla intentan con el rol de `DATABASE_URL` (superusuario en el CI) y después con el usuario del sistema; si ninguno puede, se saltean con aviso. Se dejaron como BDD y no como tests de integración porque estos últimos tienen un fixture automático que vacía la base de `DATABASE_URL`.

## Hallazgos al probar
- **Son 18 migraciones, no 19:** el conteo inicial con `ls | wc -l` incluía la carpeta `__pycache__`. Se corrigió en la spec, el plan, el contexto y la guarda.
- **Un escenario pasaba con el error presente:** migrar–deshacer–migrar pasaba aun con el `downgrade` roto, porque un `downgrade` fallido se revierte y la base no cambia (la revisión "coincidía"). Se reforzó exigiendo que todas las operaciones terminen sin error.
- El fallo original deja la base intacta: `downgrade base` se revierte entero y no queda a medias.

## Calidad
2 unitarios, 5 escenarios BDD y los pasos 5a a 5c del script de UAT, todos en verde; los 48 tests de la iteración que usan base pasan. **Con el `downgrade` anterior fallan** la guarda unitaria, los escenarios BDD 1, 2 y 5 y el paso 5a del script. Se comprobó que no quedan bases huérfanas. `mypy` 0 errores (315 archivos), `ruff`/`black`/`isort` limpios en lo nuevo. La migración conserva los avisos de estilo autogenerado por Alembic que tenía antes (el CI verifica `src/`). La suite completa se corre una sola vez al cerrar la Iteración 1. Evidencia: `quality/reports/inc9/US-8.3.4-quality.json`.

## Tiempo
Ver `.claude/tracking/US-8.3.4-tracking.json`. La Fase 1 cuenta 22 minutos por la espera de tu aprobación.

## Pendiente
- Eliminar la base descartable `cognion_dg_descartable` al cerrar la iteración.
- Ejecutar la suite completa y abrir el PR único de la Iteración 1.
