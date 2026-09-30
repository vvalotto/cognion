# Contexto de Ejecución — US-6.3.7

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.7.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna") + `docs/rf/ARQ_v1.md`
- **Fuente UX:** `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.1, §2.5, §2.6, §2.7, §6.7 (H7), §6.8 (H8), §6.9 (H9); prototipo `#stage-histograma`, `#stage-ranking`, `#stage-final`, `#stage-ranking-pocos`

## Historia de Usuario
- **ID:** US-6.3.7
- **Título:** Docente proyecta histograma, ranking y resultado final; avanza o finaliza
- **Tipo:** Nueva funcionalidad — frontend puro (segunda mitad de la pantalla de proyección)
- **Puntos:** 5 (estimado, no está en la spec — mismo orden que `US-6.3.6`)
- **Prioridad:** Alta — completa el flujo del Docente, bloquea `US-6.3.10`

## Decisiones de Ejecución
- **BDD:** Sí — la spec trae 13 escenarios Gherkin completos
- **skip_bdd:** false (validados con Vitest, sin step_defs — mismo criterio que `US-6.3.4` a `US-6.3.6`)
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5 (adaptadas a frontend/Vitest), 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (backend) — para frontend, mismo patrón que `US-6.3.4`/`US-6.3.5`
- **Umbrales de calidad (frontend):** `oxlint` 0 errores, `tsc -b` 0 errores, cobertura ≥ 80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.7-context.md`
- BDD feature: `tests/features/inc6/US-6.3.7-histograma-ranking-podio.feature`
- Plan: `docs/plans/inc6/US-6.3.7-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.7-report.md`
- Quality report: `quality/reports/inc6/US-6.3.7-quality.json`

## Notas propias de esta US
- **Sin cambios de `src/`** — `avanzarPregunta`, `finalizarSesion`, `obtenerRankingSesion`, `obtenerEstadoSesion`
  y los mensajes `pregunta_cerrada`/`sesion_finalizada` ya existen.
- Completa la máquina de etapas de `ProyeccionSesionEnVivo` (`US-6.3.6`): la etapa `cerrada` se divide en
  histograma → ranking (presentación, temporizador local de 6 s); `finalizada` → podio.
- Contrato real verificado en backend: `distribucion.opcion` = índice como texto (`"0"`, `"1"`…) o
  `"verdadero"`/`"falso"`, solo opciones con cantidad ≥ 1; `respuestaCorrecta.contenido` = `{opcion_indice}` o
  `{valor}`; `respuestaCorrecta.opciones` = textos en orden (null en V/F). El `GET estado` con la pregunta cerrada
  trae `preguntaActual.respuestaCorrecta` + `resultadoPregunta`.
- Tras recargar con la sesión finalizada el podio sale de `GET .../ranking` (spec).
- Top 3 en todas las pantallas (decisión de Víctor, 2026-09-21); con 0 participantes "Nadie participó" (H9).
