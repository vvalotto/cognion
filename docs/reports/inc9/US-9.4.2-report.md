# Reporte — US-9.4.2: Actividad Evaluativa deja de leer `UsuarioModel` de Identidad

**Estado:** implementada en `feature/inc-9-iter-4-adaptadores-sin-orm-ajeno` (2026-11-09), un commit por US y un solo PR al cierre de la Iteración 4.
**Issue:** [#601](https://github.com/vvalotto/cognion/issues/601) · **Spec:** `docs/specs/inc9/US-9.4.2.md` · **ADR:** `ADR-026`, caso 2 de 3

## Qué se hizo
- Identidad: nuevo puerto `NombreUsuarioQueryPort` (`obtener_nombres`) y gateway `SQLAlchemyNombreUsuarioQueryRepository` (un solo `SELECT ... WHERE id IN`, `{}` sin consultar si la lista es vacía).
- `EstudianteConsultaPortInProcess` (Actividad Evaluativa): `obtener_nombres` delega en ese gateway; ya no importa `identidad.frameworks.db.models`.
- `pyproject.toml`: se borró la línea `# #601` de `ignore_imports`.
- El comportamiento observable no cambia (canal en vivo, `_resolucion_nombres.py`).

## Decisiones
- **Sin BDD:** refactor; los escenarios se cubren con la caracterización de integración (commiteada antes de migrar) y `lint-imports`.
- **Puerto propio en vez de `CuentaQueryPort`:** el plan lo ponía ahí, pero el CBO de su gateway llegaba a 11 (umbral 10) y DesignReviewer daba CRITICAL. Se separó por responsabilidad y `CuentaQueryPort` no cambió. Spec y plan registran el ajuste.

## Hallazgos al probar
- El CBO se detectó con DesignReviewer manual en la Fase 7; sin esa corrida habría bloqueado recién en el pre-push.
- El PostgreSQL de Homebrew sigue sin arrancar; los tests corrieron en un cluster descartable.

## Calidad
Ver `quality/reports/inc9/US-9.4.2-quality.json`: 1209 unitarios y 165 de integración en verde, mypy 0 errores, `lint-imports` 4 contratos cumplidos, 0 CRITICAL.

## Pendiente
- `US-9.4.3` (#602), en la misma rama; al cerrar la iteración, actualizar `CLAUDE.md` y abrir el PR único.
