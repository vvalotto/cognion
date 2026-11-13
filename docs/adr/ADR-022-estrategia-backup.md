# ADR-022 — Estrategia de backup y restauración: pg_dump mensual a Google Drive institucional

**Estado:** Aceptado
**Fecha:** 2026-10-16
**Origen:** `US-8.0.2` (Issue #511), Incremento 8. Resuelve `RNF_v1.md` Escenario 2
(backup mensual, retención 12 meses). Depende de `ADR-021`.

---

## Contexto

Producción corre en Fly.io Postgres (`ADR-021`). Los snapshots nativos no garantizan 12 meses de
retención ni son portables si se migra de proveedor.

## Opciones Consideradas

- **Solo snapshots de Fly.io** — descartada: retención corta, no cubre el RNF.
- **Snapshots + dump externo** — descartada por ahora: duplica mecanismos para una comisión piloto.
- **`pg_dump` programado a almacenamiento externo** — elegida.
- **Bucket S3/R2** como destino — descartado por Víctor a favor de Drive institucional (sin costo,
  bajo su control).

## Decisión

Un workflow programado de GitHub Actions (mensual) ejecuta `pg_dump` contra la base de producción,
comprime el resultado y lo sube a una carpeta de **Google Drive institucional** mediante una cuenta
de servicio. La retención de 12 meses la aplica el mismo workflow, borrando dumps de más de 12
meses. Las credenciales (cuenta de servicio, `DATABASE_URL`) viven en GitHub/Fly secrets.

## Consecuencias

- ✅ Cubre el RNF sin depender del proveedor de hosting; portable.
- ✅ Sin costo adicional.
- ⚠️ Drive no tiene lifecycle nativo: la retención es lógica, implementada en el script.
- ⚠️ Un backup no probado no vale: `US-8.3.2` exige un ensayo de restauración real.
- ⚠️ Los dumps contienen datos de estudiantes: la carpeta debe tener acceso restringido.

## Nota 2026-10-17

El workflow en GitHub Actions hacia Drive queda en standby con la nube (`US-8.3.1`). Mientras tanto la misma
técnica (`pg_dump` con verificación y rotación) se aplica en local con `US-8.5.4`, hacia una carpeta del equipo.

---

## Nota de vigencia 2026-11-12 (Incremento 10.1)

Lo implementado en la `1.0.0` es **más simple** que esta decisión: `respaldar.sh` (y `scripts/local/respaldar.sh`) guarda un `pg_dump` verificado, con `sha256`, en una carpeta local con rotación de 30 copias, y `restaurar.sh` ensaya o reemplaza la base. **No hay copia automática a un Drive institucional ni frecuencia mensual fija**: el operador programa el respaldo (por ejemplo, diario con `cron`) y copia la carpeta fuera del servidor. `cognion.sh desplegar` respalda antes de migrar. La retención de 12 meses de `RNF_v1.md` no está garantizada por la herramienta. Ver `docs/architecture/60-deployment-view.md`.
