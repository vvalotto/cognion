# US-8.5.4: Backup y restauración local probada

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `tooling operativo` (scripts)
**Bounded Context**: transversal (`scripts/local/`)
**Issue**: #539 · **Decisión**: `ADR-022` (variante local)

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba con alumnos**,
quiero **respaldar la base antes y después de cada clase y saber que ese respaldo se puede restaurar**,
para **no perder lo que los alumnos hicieron si la máquina falla**.

---

## Contexto

Los datos (cuentas, respuestas, sesiones) viven en un único equipo. `ADR-022` decidió `pg_dump` con retención; el envío a
Drive desde la nube quedó en standby (`US-8.3.1`). Un respaldo que nunca se restauró no es un respaldo.

## Especificacion del comportamiento

- `scripts/local/respaldar.sh`: `pg_dump -Fc` de `cognion_local` a `~/CognionRespaldos/` (configurable con
  `COGNION_RESPALDOS`), archivo con fecha y hora; verifica que no esté vacío y que `pg_restore --list` lo lea; guarda
  su `sha256`; conserva los últimos N (default 30) y borra los más viejos.
- `scripts/local/restaurar.sh <archivo>`: por defecto restaura en una base **nueva y temporal** y compara conteos de las
  tablas principales contra los de origen (usuarios, eventos del event store, preguntas); solo con `--sobre-local`, y
  después de escribir una confirmación, reemplaza `cognion_local`.
- Ensayo documentado: respaldar → restaurar a base temporal → comparar → borrar la temporal.
- La carpeta de respaldos queda fuera de git. No se sube a ningún servicio externo en esta US.

## Escenarios (BDD)

1. Base con datos → `respaldar.sh` genera un archivo no vacío, legible por `pg_restore --list`, con su `sha256`.
2. `restaurar.sh <archivo>` → base temporal con los mismos conteos que el origen; la base temporal se elimina al final.
3. Más de N respaldos → se conservan los N más recientes.
4. Archivo corrupto → la restauración falla con mensaje claro y no toca `cognion_local`.
5. `--sobre-local` sin confirmación → no hace nada.

## Fuera de alcance

Subida a Drive o a la nube (`US-8.3.1`); respaldo continuo o PITR.

## Fuente de verdad UX

No aplica.
