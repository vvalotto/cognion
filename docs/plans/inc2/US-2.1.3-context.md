# Contexto de Ejecución — US-2.1.3

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.3.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas no negociables) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.1.3
- **Título:** Docente carga una pregunta de opción múltiple
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — bloquea US-2.1.5/2.1.6/2.1.7 y el frontend de carga (US-2.1.11)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya define 4 escenarios Gherkin (carga exitosa + 3 rechazos por INV-BP-02/03)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc2/US-2.1.3-context.md
- BDD feature: tests/features/inc2/US-2.1.3-cargar-pregunta-opcion-multiple.feature
- Plan: docs/plans/inc2/US-2.1.3-plan.md
- Reporte: docs/reports/inc2/US-2.1.3-report.md
- Quality report: quality/reports/inc2/US-2.1.3-quality.json

## Artefactos a modificar (de la spec)
- `src/banco_preguntas/entities/pregunta_plantilla.py` — Aggregate `PreguntaPlantillaOpcionMultiple`
- `src/banco_preguntas/entities/eventos.py` — `PreguntaCargada`
- `src/banco_preguntas/entities/ports/pregunta_repository_port.py` — Puerto de persistencia
- `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py` — Orquesta INV-BP-02, INV-BP-03
- `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`
- `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
- `src/banco_preguntas/frameworks/api/preguntas_router.py`
- `src/banco_preguntas/frameworks/db/models.py`
- `src/banco_preguntas/frameworks/db/migrations/`

## Issue asociado
- GitHub Issue #44 (labels `us-iedd`, `incremento-2`)
