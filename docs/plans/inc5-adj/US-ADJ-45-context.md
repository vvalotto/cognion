# Contexto de Ejecución — US-ADJ-45

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-45.md`
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna" + `docs/design/domain/BC-analytics-modelo.md` §8

## Historia de Usuario
- **ID:** US-ADJ-45
- **Título:** Docente consulta la evolución temporal de aciertos
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5 (sin asignación formal, mismo criterio que el resto de Analytics)
- **Prioridad:** Segunda US de la Iteración 4 del Incremento 5-ADJ — implementada junto con
  `US-ADJ-46`/`47` en una sola ejecución/branch/PR (decisión de Víctor 2026-09-14, evita repetir
  el ciclo de "romper Fakes + revisar WMC" tres veces por separado)

## Decisiones de Ejecución
- **BDD:** Sí
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:** pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/US-ADJ-45-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-45-evolucion-temporal.feature
- Plan: docs/plans/US-ADJ-45-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-45-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-45-quality.json

## Notas específicas de esta US
- Amplía `EvaluacionDesempenoConsultaPort` con `obtener_titulos_actividades` (gap detectado en
  la spec: el eje X del gráfico necesita título de actividad, dato que ningún DTO expone hoy).
- Reusa `listar_evaluaciones_finalizadas` ya existente (US-4.1.1) para la serie individual.
- **Lección de US-ADJ-44 a aplicar desde el arranque de Fase 3:** ampliar el puerto rompe todos
  sus `Fake*(EvaluacionDesempenoConsultaPort)` existentes en `tests/unit/` — agregar el método
  nuevo a cada uno (con `raise NotImplementedError` donde no se ejercita) en la misma tarea que
  agrega el método al puerto, no como fix posterior.
