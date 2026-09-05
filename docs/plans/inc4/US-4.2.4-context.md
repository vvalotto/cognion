# Contexto de Ejecución — US-4.2.4

## Fuentes
- **Fuente HU:** `docs/specs/inc4/US-4.2.4.md` (convención establecida del proyecto, `docs/specs/incN/US-N.M.K.md`)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (stack y arquitectura ya decididos — no se pregunta, por convención de sesión de este proyecto)

## Historia de Usuario
- **ID:** US-4.2.4
- **Título:** Docente consulta la tasa de error por unidad/tema de una materia
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta (RF-17, Iteración 2 del Incremento 4)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad de negocio, con criterios de aceptación Gherkin ya redactados en la spec.
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

## Alcance según spec (`docs/specs/inc4/US-4.2.4.md`)
- Extender `EvaluacionDesempenoConsultaPort` con `listar_respuestas_vigentes_de_materia(materia_id, estudiante_ids)`.
- Nuevo `ObtenerTasaErrorPorTemaUseCase` (compone el port extendido + `ComisionConsultaPort.listar_estudiantes` (US-4.2.2) + `PreguntaMetadatoConsultaPort.obtener_metadatos` (US-4.2.3)).
- Extender `AnalyticsController` con `obtener_tasa_error_por_tema`.
- Nuevo endpoint `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=`, rol `docente`.
- BC: Analytics (sin aggregate propio).

## Rutas de Artefactos
- Contexto: `docs/plans/inc4/US-4.2.4-context.md`
- BDD feature: `tests/features/inc4/US-4.2.4-tasa-error-por-tema.feature`
- Plan: `docs/plans/inc4/US-4.2.4-plan.md`
- Reporte: `docs/reports/inc4/US-4.2.4-report.md`
- Quality report: `quality/reports/inc4/US-4.2.4-quality.json`

> Nota de rutas: por convención de este proyecto (`feedback_implement_us_rutas_incN`), las rutas van bajo `incN/`, no en la raíz de `docs/plans/` / `docs/reports/` / `quality/reports/` como sugiere el template genérico del skill.
