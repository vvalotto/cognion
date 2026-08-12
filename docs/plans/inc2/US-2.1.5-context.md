# Contexto de Ejecución — US-2.1.5

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.5.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas no negociables) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.1.5
- **Título:** Docente edita una pregunta existente
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — depende de US-2.1.3/2.1.4 (crean lo que esta US edita), bloquea el
  frontend de edición (US-2.1.12)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya define 3 escenarios Gherkin (edición exitosa, rechazo por dejar sin
  opción correcta, rechazo por editar pregunta inactiva)
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
- Contexto: docs/plans/inc2/US-2.1.5-context.md
- BDD feature: tests/features/inc2/US-2.1.5-editar-pregunta.feature
- Plan: docs/plans/inc2/US-2.1.5-plan.md
- Reporte: docs/reports/inc2/US-2.1.5-report.md
- Quality report: quality/reports/inc2/US-2.1.5-quality.json

## Artefactos a modificar (de la spec)
- `src/banco_preguntas/entities/pregunta_plantilla.py` — Método `editar(...)` en cada subtipo
  (`PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`), reaplica INV-BP-02/03
  donde corresponda
- `src/banco_preguntas/entities/eventos.py` — Agregar `PreguntaEditada`
- `src/banco_preguntas/use_cases/editar_pregunta.py` — Orquesta la validación según el tipo
  concreto
- `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` — Endpoint de
  edición
- `src/banco_preguntas/frameworks/api/preguntas_router.py` — `PUT /preguntas/{id}`
