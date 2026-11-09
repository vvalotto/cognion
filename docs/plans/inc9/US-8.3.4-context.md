# Contexto de Ejecución — US-8.3.4

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.3.4.md`, Issue [#527](https://github.com/vvalotto/cognion/issues/527)
- **Origen:** hallazgo verificado el 2026-11-07: `alembic downgrade base` falla (`Can't emit DROP CONSTRAINT ... it has no name`)
- **Código existente:** `migrations/versions/dd44a181d7fc_estudiante_comision_id.py` (crea la FK con nombre `None` y su `downgrade` hace `drop_constraint(None, ...)`); `tests/uat/inc8/verificar_migraciones.sh` (`US-8.1.4`)

## Historia de Usuario
- **ID:** US-8.3.4 — `alembic downgrade base` funciona
- **Tipo:** corrección de una migración (solo el `downgrade`); sin cambios en dominio, casos de uso, API ni frontend
- **Puntos:** 2 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 1 (rama `feature/inc-9-iter-1-correcciones`, un commit por US y un solo PR al cierre)

## Decisiones de Ejecución
- **Cambio mínimo:** `op.drop_constraint("estudiante_comision_id_fkey", "estudiante", type_="foreignkey")`. El `upgrade` no cambia: las bases ya migradas (local, VM de GCP) no se tocan. De las 18 migraciones es la única con este patrón (`grep`).
- **Verificación doble:**
  1. Escenarios BDD con pasos que **crean su propia base descartable**, migran y deshacen con `alembic` real (nunca tocan la base de `DATABASE_URL`, solo leen sus credenciales). Para crear la base intentan primero con el rol de `DATABASE_URL` (superusuario en el CI) y luego con el usuario del sistema, como `verificar_migraciones.sh`; si ninguno puede, **se saltean con aviso**.
  2. `tests/uat/inc8/verificar_migraciones.sh` se amplía con `downgrade base`, comprobación de que no quedan tablas y `upgrade head` de nuevo.
- **Que detecta el error:** correr ambos con el `downgrade` anterior y ver que fallan.
- **Cuidado con las variables de shell:** no reutilizar nombres entre un experimento y un script cargado con `source` (una colisión de `U` dejó un archivo suelto en `US-ADJ-63`).
- **Fases:** todas, con BDD.

## Rutas
- Plan: docs/plans/inc9/US-8.3.4-plan.md · Reporte: docs/reports/inc9/US-8.3.4-report.md · Quality: quality/reports/inc9/US-8.3.4-quality.json
- Feature: tests/features/inc9/US-8.3.4-downgrade-base.feature
