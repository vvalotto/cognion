# Reporte — US-9.4.3: Identidad deja de leer el event store de Actividad Evaluativa

**Estado:** implementada en `feature/inc-9-iter-4-adaptadores-sin-orm-ajeno` (2026-11-09), un commit por US y un solo PR al cierre de la Iteración 4.
**Issue:** [#602](https://github.com/vvalotto/cognion/issues/602) · **Spec:** `docs/specs/inc9/US-9.4.3.md` · **ADR:** `ADR-026`, caso 3 de 3

## Qué se hizo
- Actividad Evaluativa: puerto `EstudianteEvaluacionesQueryPort` (`tiene_evaluaciones_iniciadas`) y gateway `SQLAlchemyEstudianteEvaluacionesQueryRepository`, con la lógica que tenía el adaptador.
- `EvaluacionConsultaPortInProcess` (Identidad): `tiene_evaluaciones` delega en ese gateway; ya no importa `actividad_evaluativa.frameworks.db.models`.
- `pyproject.toml`: se borró la línea `# #602` de `ignore_imports`.
- El comportamiento observable no cambia (`eliminar_cuenta` sigue sin poder borrar a un estudiante con evaluaciones).

## Decisiones
- **Sin BDD:** refactor; los escenarios se cubren con la caracterización de integración (commiteada antes de migrar) y `lint-imports`.
- **Puerto propio, sin ensanchar `EvaluacionEstudianteQueryPort`:** evita repetir el patrón de CBO de `US-2.1.2`/`US-2.1.5`.
- **Misma consulta:** sigue trayendo los payloads de `EvaluacionIniciada` y filtrando en memoria. Optimizarla queda fuera de alcance.

## Calidad
Ver `quality/reports/inc9/US-9.4.3-quality.json`: 1209 unitarios y 150 de integración en verde, mypy 0 errores, `lint-imports` 4 contratos cumplidos, 0 CRITICAL.

## Cierre de la Iteración 4
Las tres excepciones de `ADR-026` están migradas. Queda actualizar `CLAUDE.md` (hoy dice "tres excepciones pendientes, #600 a #602") y abrir el PR único hacia `develop`.
