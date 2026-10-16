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
