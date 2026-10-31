# Reporte — US-8.5.4: Backup y restauración local probada

**Estado:** implementada en `feature/US-8.5.1-entorno-local` (2026-10-18), apilada sobre `US-8.5.1` a `8.5.3`. PR diferido al cierre de la Iteración 5 (CI lento).
**Issue:** #539 · **Spec:** `docs/specs/inc8/US-8.5.4.md` · **Decisión:** `ADR-022` (variante local)

## Qué se hizo
- `scripts/local/respaldar.sh`: `pg_dump -Fc` de `cognion_local` a `~/CognionRespaldos/` (`COGNION_RESPALDOS`, carpeta 700), archivo con fecha y hora; verifica no vacío y lectura con `pg_restore --list`; guarda `sha256` (formato `shasum -c`); rota conservando los últimos `COGNION_RESPALDOS_N` (default 30).
- `scripts/local/restaurar.sh <archivo> [--sobre-local]`: valida hash y lectura antes de tocar nada; por defecto ensaya en una base temporal, compara conteos de `usuario`, `events` y `pregunta_plantilla` contra la base actual y borra la temporal (exit 3 si difieren). Con `--sobre-local` exige escribir `RESTAURAR`; restaura primero a la temporal y reemplaza por rename solo si salió bien, y exige que no haya conexiones abiertas.
- `scripts/local/_conexion.sh`: helper común que lee `.env.local`. `levantar.sh` no se tocó.
- `tests/uat/inc8/verificar_respaldo_local.sh`: verificación con base descartable y datos sembrados.

## Decisiones
- Un dump defectuoso nunca toca la base local: siempre se restaura primero a una temporal.
- Una diferencia de conteos no es error duro (exit 3): puede ser actividad posterior al respaldo.
- Portabilidad macOS: sin `head -n -N`, `awk` para la rotación, `mktemp` en lugar de `/tmp` fijo.
- Sin envío a Drive ni a la nube (`US-8.3.1`).

## Calidad
Verificación 10/10 OK: escenarios 1 a 5 de la spec, más permisos 700, `sha256` alterado, exit 3 ante diferencia y reemplazo confirmado. Sin bases ni archivos huérfanos; `~/CognionRespaldos` no se tocó. `tests/unit/inc8` 68/68. `shellcheck` no está instalado: solo `bash -n`. Evidencia en `quality/reports/inc8/US-8.5.4-quality.json`.
