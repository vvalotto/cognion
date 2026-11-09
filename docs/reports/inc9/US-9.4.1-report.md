# Reporte — US-9.4.1: Banco de Preguntas deja de leer `ComisionModel` de Identidad

**Estado:** implementada en `feature/inc-9-iter-4-adaptadores-sin-orm-ajeno` (2026-11-09), un commit por US y un solo PR al cierre de la Iteración 4.
**Issue:** [#600](https://github.com/vvalotto/cognion/issues/600) · **Spec:** `docs/specs/inc9/US-9.4.1.md` · **ADR:** `ADR-026`, caso 1 de 3

## Qué se hizo
- `ComisionQueryPort` (Identidad) suma `existe_comision_en_materia(materia_id)`; `SQLAlchemyComisionQueryRepository` lo implementa con `SELECT id ... LIMIT 1`.
- `ComisionConsultaPortInProcess` (Banco de Preguntas): `tiene_comisiones` delega en ese método. El adaptador ya no importa `identidad.frameworks.db.models` ni usa la sesión directamente.
- `pyproject.toml`: se borró la línea `# #600` de `ignore_imports`; `lint-imports` sigue con 4 contratos cumplidos.
- Los dos fakes de `ComisionQueryPort` implementan el método nuevo. El comportamiento observable no cambia.

## Decisiones
- **Sin BDD:** es un refactor. Los escenarios de la spec se cubren con un test de caracterización de integración, que se commiteó y pasó **antes** de migrar, y con `lint-imports`.
- **Método nuevo en el puerto en vez de reutilizar `listar_comisiones_por_materia(incluir_inactivas=True)`**, que carga las comisiones completas con sus docentes para responder un sí o no.

## Hallazgos al probar
- El servicio `postgresql@16` de Homebrew no arranca: `postmaster.pid` quedó viejo y el PID 912 hoy es otro proceso. No se tocó. Los tests corrieron en un cluster descartable fuera del repo (puerto 55432).

## Calidad
Ver `quality/reports/inc9/US-9.4.1-quality.json`: 1209 unitarios y 86 de integración en verde, mypy 0 errores, `lint-imports` 4 contratos cumplidos, 0 CRITICAL en DesignReviewer.

## Pendiente
- `US-9.4.2` (#601) y `US-9.4.3` (#602), en la misma rama.
- Apagar el cluster descartable y, al cerrar la iteración, actualizar `CLAUDE.md` (hoy dice "tres excepciones pendientes, #600 a #602") y abrir el PR único.
