# Contexto de Ejecución — US-2.1.4

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.4.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas no negociables) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.1.4
- **Título:** Docente carga una pregunta de Verdadero/Falso
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — bloquea US-2.1.5/2.1.6/2.1.7 y el frontend de carga (US-2.1.11)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya define 2 escenarios Gherkin (carga con respuesta Verdadero / Falso)
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
- Contexto: docs/plans/inc2/US-2.1.4-context.md
- BDD feature: tests/features/inc2/US-2.1.4-cargar-pregunta-verdadero-falso.feature
- Plan: docs/plans/inc2/US-2.1.4-plan.md
- Reporte: docs/reports/inc2/US-2.1.4-report.md
- Quality report: quality/reports/inc2/US-2.1.4-quality.json

## Artefactos a modificar (de la spec)
- `src/banco_preguntas/entities/pregunta_plantilla.py` — Aggregate `PreguntaPlantillaVerdaderoFalso`
- `src/banco_preguntas/use_cases/cargar_pregunta_verdadero_falso.py` — Orquesta la creación
- `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` — Nuevo endpoint/rama para este tipo
- `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` — Extiende el repositorio de `US-2.1.3`
- `src/banco_preguntas/frameworks/api/preguntas_router.py` — Endpoint FastAPI (requiere rol `docente`)
- `src/banco_preguntas/frameworks/db/models.py` — Reutiliza el modelo de `US-2.1.3` (columna discriminadora)
