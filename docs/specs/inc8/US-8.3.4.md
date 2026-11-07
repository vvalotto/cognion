# US-8.3.4: `alembic downgrade base` funciona

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 1 (nació en el Incremento 8, Iteración 3, y se movió porque no depende de la nube)
**Tipo**: `corrección` backend (migración de base de datos)
**Agregado principal afectado**: ninguno
**Bounded Context**: Identidad (tabla `estudiante`)
**Origen**: hallazgo verificado el 2026-11-07 al revisar los Issues pendientes; antes era un ítem de `inc8-candidatas.md`.
**Issue**: [#527](https://github.com/vvalotto/cognion/issues/527)
**Interactúa con**: `US-8.1.4` (migraciones como paso explícito), `tests/uat/inc8/verificar_migraciones.sh`, `US-8.2.3` (rollback de esquema, diferida con la nube).

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar Cognión**,
quiero **poder deshacer las migraciones de la base hasta el estado vacío**,
para **volver atrás una versión mala o ensayar una instalación limpia sin armar la base a mano**.

---

## Contexto

Verificado el 2026-11-07 sobre una base descartable: `alembic upgrade head` llega bien a `c4d1f9a27b60`, pero
`alembic downgrade base` **falla** con

```
sqlalchemy.exc.CompileError: Can't emit DROP CONSTRAINT for constraint
ForeignKeyConstraint(..., table=Table('estudiante', ...)); it has no name
```

y la base queda **intacta** (sigue en `head`, con todas las tablas): la operación se revierte entera, no deja un estado
a medias.

**Causa:** la migración `dd44a181d7fc_estudiante_comision_id` crea la clave foránea sin nombre
(`op.create_foreign_key(None, "estudiante", "comision", ...)`) y su `downgrade` hace `op.drop_constraint(None, ...)`. Es la
**única** migración de las 18 con este patrón (verificado con `grep`). PostgreSQL nombra esa restricción
`estudiante_comision_id_fkey` (verificado en una base migrada).

## Especificacion del comportamiento

- `alembic downgrade base` ejecuta las 18 migraciones hacia atrás sin error y deja la base **sin tablas de la aplicación**
  (solo `alembic_version`, vacía).
- Después, `alembic upgrade head` vuelve a construir todo y deja la base en el mismo `head`.
- El `upgrade` de `dd44a181d7fc` **no cambia**: las bases ya migradas (la local, la de la VM de GCP) no se tocan.
- Solo cambia el `downgrade`: nombra la restricción `estudiante_comision_id_fkey`.

## Escenarios (BDD)

1. **Downgrade completo.** Sobre una base en `head`, `downgrade base` termina con código `0` y no quedan tablas de la
   aplicación.
2. **Round-trip.** `upgrade head` → `downgrade base` → `upgrade head` termina en el mismo `head`.
3. **Idempotencia del upgrade.** Una segunda corrida de `upgrade head` no hace nada (código `0`), como hoy.
4. **Base ya migrada.** Una base creada con el `upgrade` anterior admite el `downgrade` nuevo (el nombre de la restricción
   es el que PostgreSQL asignó).
5. **Paso a paso.** `downgrade -1` desde `head` y hasta la revisión anterior a `dd44a181d7fc` también funciona.

## Fuera de alcance

Rehacer el `downgrade` de migraciones que ya funcionan; convenciones de nombres de restricciones para migraciones futuras
(se puede proponer como mejora, pero no es parte de esta US); el rollback de esquema en producción (`US-8.2.3`).

## Notas para `/implement-us`

- Cambio mínimo en `migrations/versions/dd44a181d7fc_estudiante_comision_id.py`: `op.drop_constraint("estudiante_comision_id_fkey", "estudiante", type_="foreignkey")`.
- **Verificación:** ampliar `tests/uat/inc8/verificar_migraciones.sh` (base descartable propia, ya existente) con
  `downgrade base`, comprobación de que no quedan tablas y `upgrade head` otra vez. Es un script de UAT, no un test de
  `pytest`, porque los tests de integración vacían la base de `DATABASE_URL`.
- **Comprobar que detecta el error:** correr el script con el `downgrade` anterior y ver que falla.
- Probar también el escenario 4: migrar con la revisión actual, aplicar el cambio y hacer `downgrade`.

---

## Decisiones tomadas al implementar (Incremento 9, 2026-11-07)

- **Son 18 migraciones, no 19:** el conteo inicial con `ls | wc -l` incluía la carpeta `__pycache__`.
- **Arreglo:** una sola línea en el `downgrade` de `dd44a181d7fc` (`estudiante_comision_id_fkey`). El `upgrade` no se tocó.
- **Guarda que no estaba en la spec:** `tests/unit/inc9/test_us_8_3_4_migraciones_con_nombre.py` falla si el `downgrade` de
  alguna migración llama `drop_constraint(None, ...)`. Alembic autogenera `None` por defecto, así que el error se repetiría
  con la próxima migración que tenga una clave foránea.
- **Verificación con `alembic` real:** los 5 escenarios BDD crean su propia base descartable (`cognion_mig_<id>`), la
  migran y la deshacen, y la borran al terminar. Se saltean con aviso si ningún rol puede crear bases (el rol de
  `DATABASE_URL` en tu Mac no tiene `CREATEDB`; en el CI es superusuario). Además, `tests/uat/inc8/verificar_migraciones.sh`
  suma los pasos 5a a 5c (`downgrade base` con datos cargados, sin tablas restantes, `upgrade head` de nuevo).
- **Escenario reforzado:** migrar–deshacer–migrar pasaba igual con el `downgrade` roto (un `downgrade` fallido se revierte y
  la base no cambia), así que ahora exige que todas las operaciones terminen sin error.
- **Verificado al revés:** con el `downgrade` anterior fallan la guarda, los escenarios 1, 2 y 5 y el paso 5a del script.

