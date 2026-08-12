# Contexto de Ejecución — US-2.1.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.1.6.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas no negociables) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.1.6
- **Título:** Docente elimina (baja lógica) una pregunta
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — depende de US-2.1.3/2.1.4 (crean lo que esta US elimina), bloquea
  US-2.1.7 (`FiltrarBanco` excluye inactivas) y el frontend de eliminación (US-2.1.13)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya define 2 escenarios Gherkin (eliminación exitosa, rechazo por
  pregunta ya eliminada)
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
- Contexto: docs/plans/inc2/US-2.1.6-context.md
- BDD feature: tests/features/inc2/US-2.1.6-eliminar-pregunta.feature
- Plan: docs/plans/inc2/US-2.1.6-plan.md
- Reporte: docs/reports/inc2/US-2.1.6-report.md
- Quality report: quality/reports/inc2/US-2.1.6-quality.json

## Artefactos a modificar (de la spec)
- `src/banco_preguntas/entities/pregunta_plantilla.py` — Método `eliminar()`, valida INV-BP-04
- `src/banco_preguntas/entities/eventos.py` — Agregar `PreguntaEliminada`
- `src/banco_preguntas/use_cases/eliminar_pregunta.py` — Orquesta la baja lógica
- `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` — Endpoint de
  eliminación
- `src/banco_preguntas/frameworks/api/preguntas_router.py` — `DELETE /preguntas/{id}` (UPDATE
  de `activa`, no DELETE SQL)

## Nota de riesgo (heredada del reporte de US-2.1.5)
`PreguntasController` ya inyecta 3 use cases; sumar `EliminarPreguntaUseCase` puede repetir el
CRITICAL de CBO≥11/10 visto en `US-2.1.2` y `US-2.1.5`, detectado recién en el pre-push gate
(`DesignReviewer`/`CBOAnalyzer`), no en los Quality Gates de Fase 7. Mitigación ya usada:
tipar el evento de retorno como `object` en el controller.
