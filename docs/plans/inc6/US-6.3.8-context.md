# Contexto de Ejecución — US-6.3.8

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.8.md`, Issue #419
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna")
- **Fuente UX:** `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §3.1, §3.2, §6.8 (H8); prototipo
  `#est-sesiones`, `#est-sala-espera`; pantalla existente `MisActividades.tsx` (`wireframes-actividad-evaluativa.md` §3)

## Historia de Usuario
- **ID:** US-6.3.8
- **Título:** Estudiante ve las sesiones disponibles, se une y espera en la sala
- **Tipo:** Nueva funcionalidad — frontend puro (primera pantalla del Estudiante en el modo en vivo)
- **Puntos:** 5 (estimado)
- **Prioridad:** Alta — bloquea `US-6.3.9`

## Decisiones de Ejecución
- **BDD:** Sí — 10 escenarios de la spec, validados con Vitest (sin step_defs, mismo criterio que `US-6.3.4` a `6.3.7`)
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5 (adaptadas a Vitest), 7, 8, 9

## Umbrales de calidad (frontend)
- `oxlint` 0 errores, `tsc -b` 0 errores, `npm run test:coverage` (`US-ADJ-53`) con cobertura ≥ 80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.8-context.md`
- BDD feature: `tests/features/inc6/US-6.3.8-sesiones-sala-estudiante.feature`
- Plan: `docs/plans/inc6/US-6.3.8-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.8-report.md`
- Quality report: `quality/reports/inc6/US-6.3.8-quality.json`

## Notas propias de esta US
- **Sin cambios de `src/`.** Backend verificado: `GET /sesiones-en-vivo` acepta `comision_id` opcional
  (`sesiones_en_vivo_router.py:400`) y para el Estudiante resuelve su propia Comisión.
- **Gap frontend (no de backend):** `listarSesionesEnVivo(comisionId, …)` en `lib/sesion-en-vivo-api.ts` exige
  `comisionId`; pasa a opcional (sin él no se manda el query param). Cambio aditivo: el único caller actual
  (`ComisionDetalleDocente.tsx`) lo sigue pasando.
- `SesionEnVivoResumenResponse` ya trae `materiaId`/`materiaNombre`: el filtro por materia es de cliente.
- `estado-en-espera`/`estado-en-curso` ya existen en `badge.tsx` (`US-6.3.5`).
- Contenedor `SesionEnVivoEstudiante` con máquina de etapas; `EnCurso`/`Finalizada` y la transición tras
  `pregunta_presentada` quedan como punto de extensión para `US-6.3.9` (mismo criterio que `US-6.3.6` → `6.3.7`).
- Reutiliza `IndicadorConexion` (`US-6.3.6`) para H8.
