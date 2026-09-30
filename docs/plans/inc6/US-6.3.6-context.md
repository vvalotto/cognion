# Contexto de Ejecución — US-6.3.6

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.6.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna") + `docs/rf/ARQ_v1.md`
- **Fuente UX:** `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1, §1.1, §2.3, §2.4, §6.1 (H1), §6.2 (H2), §6.8 (H8); prototipo `#stage-pregunta-sola`, `#stage-pregunta-opciones`

## Historia de Usuario
- **ID:** US-6.3.6
- **Título:** Docente proyecta la pregunta, muestra las opciones y la cierra
- **Tipo:** Nueva funcionalidad — frontend puro (primera mitad de la pantalla de proyección)
- **Puntos:** 5 (estimado, no está en la spec — mismo orden que `US-6.3.5`)
- **Prioridad:** Alta — bloquea `US-6.3.7`

## Decisiones de Ejecución
- **BDD:** Sí — la spec trae 10 escenarios Gherkin completos
- **skip_bdd:** false (validados con Vitest, sin step_defs — mismo criterio que `US-6.3.4`/`US-6.3.5`)
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5 (adaptadas a frontend/Vitest), 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (backend) — para frontend, mismo patrón que `US-6.3.4`/`US-6.3.5`
- **Umbrales de calidad (frontend):** `oxlint` 0 errores, `tsc -b` 0 errores, cobertura ≥ 80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.6-context.md`
- BDD feature: `tests/features/inc6/US-6.3.6-proyeccion-pregunta-opciones.feature`
- Plan: `docs/plans/inc6/US-6.3.6-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.6-report.md`
- Quality report: `quality/reports/inc6/US-6.3.6-quality.json`

## Notas propias de esta US
- **Sin cambios de `src/`** — todos los endpoints (`mostrarOpciones`, `cerrarPregunta`, `obtenerEstadoSesion`)
  y los mensajes del canal ya existen (`US-6.2.x`, `US-6.3.3`, `US-6.3.4`).
- `preguntaActualIndice` es 0-based en backend y canal → el eyebrow muestra `indice + 1`.
- Contenedor `ProyeccionSesionEnVivo` con máquina de etapas: esta US implementa `pregunta-sola` y
  `pregunta-opciones`; las etapas `cerrada`/`finalizada` quedan como punto de extensión para `US-6.3.7`.
- El chip "Reconectando…" (H8) se repite acá (segundo consumidor) — extraer componente compartido
  si el plan lo justifica.
- `lib/temporizador-pregunta.ts` y `lib/opciones-en-vivo.ts` son compartidos con `US-6.3.9`.
