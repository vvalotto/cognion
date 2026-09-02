# Contexto de Ejecución — US-3.4.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc3/US-3.4.6.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md` + `CLAUDE.md` (reglas de capas, ADRs 001-019)

## Historia de Usuario
- **ID:** US-3.4.6
- **Título:** Estudiante rinde su evaluación — responde, pausa y reanuda
- **Tipo:** Mejora de comportamiento existente (extiende responses de endpoints ya existentes + nuevo frontend)
- **Puntos:** 8
- **Prioridad:** Alta — Iteración 4 del Incremento 3, lado Estudiante

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad visible de extremo a extremo (rendir, pausar, reanudar), con criterios de aceptación Gherkin ya redactados en la spec.
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
- Contexto: docs/plans/US-3.4.6-context.md
- BDD feature: tests/features/inc3/US-3.4.6-rendir-evaluacion.feature
- Plan: docs/plans/inc3/US-3.4.6-plan.md
- Reporte: docs/reports/inc3/US-3.4.6-report.md
- Quality report: quality/reports/inc3/US-3.4.6-quality.json

## Notas específicas de esta US
- No requiere decisión arquitectónica (spec §Impacto arquitectónico) — extiende dos `response`
  existentes y agrega un método de solo lectura a `PreguntaConsultaPort`.
- Backend: `entities/ports/pregunta_consulta_port.py` (nuevo método `obtener_contenido`),
  `frameworks/api/schemas.py` (`PreguntaAsignadaResponse` + `EvaluacionResponse`),
  `use_cases/iniciar_evaluacion.py` (puebla los campos nuevos).
- Frontend: `RendirEvaluacion.tsx`, `EvaluacionSuspendida.tsx`, rutas nuevas en `router.tsx`.
- Gate UX: `docs/design/ux/wireframes-actividad-evaluativa.md` §3.3/§3.4 ya aprobado — no
  requiere nuevo ciclo de prototipo.
