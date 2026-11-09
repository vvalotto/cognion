# Contexto de Ejecución — US-9.4.1

## Fuentes
- **Fuente HU:** `docs/specs/inc9/US-9.4.1.md`, Issue [#600](https://github.com/vvalotto/cognion/issues/600)
- **Fuente arquitectura:** `docs/adr/ADR-026-acoplamiento-entre-bc-por-datos.md`, `docs/rf/ARQ_v1.md`, `CLAUDE.md`
- **Código existente:** `src/banco_preguntas/frameworks/adapters/comision_consulta_port_in_process.py`, `src/identidad/interface_adapters/gateways/comision_query_repository.py`, `src/identidad/entities/ports/comision_query_port.py`

## Historia de Usuario
- **ID:** US-9.4.1 — Banco de Preguntas deja de leer `ComisionModel` de Identidad
- **Tipo:** refactorización sin cambio de comportamiento (backend)
- **Puntos:** 2 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 4 (rama `feature/inc-9-iter-4-adaptadores-sin-orm-ajeno`, un commit por US y un solo PR al cierre)

## Decisiones de Ejecución
- **BDD:** No (refactorización). Los escenarios 1 a 6 de la spec se cubren con un **test de caracterización de integración** (primer commit, antes de migrar) y con `lint-imports`.
- **skip_bdd:** true → se saltean Fases 1 y 6.
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9.
- **Base de datos:** los tests de integración se corren con `DATABASE_URL` inline apuntando a una base descartable; nunca la de desarrollo.
- **Orden:** (1) test de caracterización verde sobre el código actual; (2) método nuevo en `ComisionQueryPort` + gateway + fakes + test; (3) migrar el adaptador; (4) borrar la línea `# #600` de `ignore_imports`.

## Rutas
- Plan: docs/plans/inc9/US-9.4.1-plan.md · Reporte: docs/reports/inc9/US-9.4.1-report.md · Quality: quality/reports/inc9/US-9.4.1-quality.json
