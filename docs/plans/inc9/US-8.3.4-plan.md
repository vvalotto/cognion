# Plan de Implementación: US-8.3.4 - `alembic downgrade base` funciona

**Patrón:** clean-architecture-bc · **Producto:** cognion · **Capa:** infraestructura de base de datos (`migrations/`)

## Diseño
`alembic downgrade base` falla porque la migración `dd44a181d7fc_estudiante_comision_id` crea la clave foránea sin nombre (`op.create_foreign_key(None, ...)`) y su `downgrade` intenta borrarla con `op.drop_constraint(None, ...)`, que no sabe a cuál se refiere. PostgreSQL la nombró `estudiante_comision_id_fkey` (verificado en una base migrada). Es la **única** de las 18 migraciones con este patrón.

```
dd44a181d7fc  upgrade:   create_foreign_key(None, "estudiante", "comision", ...)   → sin cambios
              downgrade: drop_constraint(None, "estudiante", type_="foreignkey")    → drop_constraint("estudiante_comision_id_fkey", ...)
```

- Solo cambia el `downgrade`. El `upgrade` no se toca: las bases ya migradas (la local y la de la VM de GCP) no se modifican.
- Sin cambios en dominio, casos de uso, API ni frontend.
- Al fallar, `downgrade base` se revierte entero (verificado): no deja la base a medias, así que no hay riesgo de datos al probarlo.

## Componentes a Implementar

### 1. Migración (`migrations/versions/dd44a181d7fc_estudiante_comision_id.py`)
- [ ] `op.drop_constraint("estudiante_comision_id_fkey", "estudiante", type_="foreignkey")` en el `downgrade`.

### 2. Verificación con la base real (`tests/uat/inc8/verificar_migraciones.sh`)
- [ ] Después de los pasos 1 a 4 existentes, agregar: `downgrade base` termina con código 0, no quedan tablas de la aplicación (solo `alembic_version`), y `upgrade head` vuelve al mismo `head`. Usa la misma base propia que ya crea el script.

## Tests (Fases 4 a 6)
- **Unitarios (`tests/unit/inc9/test_us_8_3_4_migraciones_con_nombre.py`, sin base):** una guarda que recorre `migrations/versions/*.py` y falla si algún `downgrade` llama `drop_constraint(None, ...)`. Evita que el error vuelva con una migración futura autogenerada por Alembic (que escribe `None` por defecto). Incluye una prueba de que la guarda detecta el patrón malo y acepta el bueno.
- **Integración (`tests/integration/inc9/test_us_8_3_4_downgrade_integration.py`) y BDD (`tests/step_defs/inc9/test_us_8_3_4_steps.py`):** crean **su propia base descartable** (la que nombra el test, nunca la de `DATABASE_URL`), migran y deshacen con `alembic` real como subproceso, y la borran al terminar. Cubren los 5 escenarios. Para crear la base intentan con el rol de `DATABASE_URL` (superusuario en el CI) y luego con el usuario del sistema; si ninguno puede, **se saltean con aviso**. Una ayuda común: `tests/integration/inc9/_base_descartable.py`.
- **Que detectan el error:** correr todo con el `downgrade` anterior y ver que fallan los escenarios 1, 2 y 5, y el script de UAT.
- **Regresión:** el script de UAT existente (pasos 1 a 4) sigue en verde.

## Documentación (Fase 8)
- Spec `US-8.3.4`: estado → `Implementada`.
- `docs/plans/inc8/inc8-candidatas.md`: sin cambios (ya figura como diferido y movido).

## Riesgos
- **Los pasos de BDD se saltean en una máquina sin permisos para crear bases** (tu Mac con el rol `user`): se compensa con el script de UAT, que usa tu usuario del sistema, y con el CI, donde el rol sí puede.
- **Una base descartable huérfana si un test se interrumpe:** el nombre lleva un sufijo único y se borra en el `finally`; si quedara alguna, se ve con `\l` y se borra a mano.
- **Una migración nueva autogenerada con `None`:** la guarda unitaria la detecta.
