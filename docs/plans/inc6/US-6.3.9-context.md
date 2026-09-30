# Contexto de Ejecución — US-6.3.9

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.9.md`, Issue #420
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna")
- **Fuente UX:** `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §3.3, §3.4, §3.5, §6.1-6.5 (H1-H5), §6.8 (H8), §6.9 (H9);
  prototipo `#est-espera-opciones`, `#est-pregunta`, `#est-pregunta-vf`, `#est-resultado-pregunta`, `#est-sin-respuesta`,
  `#est-resultado-final`

## Historia de Usuario
- **ID:** US-6.3.9
- **Título:** Estudiante responde desde el celular y ve su resultado y el final
- **Tipo:** Nueva funcionalidad — frontend puro (completa el flujo del Estudiante en el modo en vivo)
- **Puntos:** 5 (estimado)
- **Prioridad:** Alta — última US de pantallas antes de la UAT `US-6.3.10`

## Decisiones de Ejecución
- **BDD:** Sí — 15 escenarios de la spec, validados con Vitest (sin step_defs, mismo criterio que `US-6.3.4` a `6.3.7`)
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5 (adaptadas a Vitest), 7, 8, 9

## Umbrales de calidad (frontend)
- `oxlint` 0 errores, `tsc -b` 0 errores, `npm run test:coverage` (`US-ADJ-53`) con cobertura ≥ 80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.9-context.md`
- BDD feature: `tests/features/inc6/US-6.3.9-responder-resultado-estudiante.feature`
- Plan: `docs/plans/inc6/US-6.3.9-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.9-report.md`
- Quality report: `quality/reports/inc6/US-6.3.9-quality.json`

## Notas propias de esta US
- **Sin cambios de `src/`.** Contratos verificados en el backend.
- **Gap de contrato resuelto en el cliente:** `POST .../responder` devuelve `TiempoAgotado`, `RespuestaYaRegistrada` y
  `PreguntaYaCerrada` como `422` con `detail` de **texto libre**, sin código (`sesiones_en_vivo_router.py`). En vez de
  parsear el texto (frágil), ante cualquier `422` se pide `GET estado` y la etapa sale del estado: `yaRespondio` →
  resultado; `preguntaActualCerrada` → sin respuesta (cierre, H4); pregunta abierta y sin respuesta → sin respuesta
  (tiempo agotado, H5). `404` (participación o sesión) → se vuelve a unir y recalcula.
- Tras recargar habiendo respondido, `GET estado` trae `yaRespondio` y `puntajeAcumulado` pero no el acierto ni el
  puntaje de esa pregunta: el resultado muestra solo el acumulado (lo prevé la spec).
- La posición final sale del `ranking` completo (`sesion_finalizada` o `GET .../ranking`) buscando el id propio
  (`obtenerUsuarioId()`, `session.ts`, `US-ADJ-24`).
- Reutiliza `opciones-en-vivo.ts` (colores, V/F, 3 opciones), `temporizador-pregunta.ts` y `ranking-en-vivo.ts` (`top3`).
- `pregunta_cerrada` llega también al celular con la correcta y el ranking: **el Estudiante no los muestra** (sin ranking
  hasta el final, sin revelar la correcta).
