# Contexto de Ejecución — US-6.3.5

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.5.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna") + `docs/rf/ARQ_v1.md`
- **Fuente UX:** `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §2.1, §2.2, §6.6 (H6), §6.8 (H8)

## Historia de Usuario
- **ID:** US-6.3.5
- **Título:** Docente crea la sesión en vivo desde una Comisión y abre la sala de espera
- **Tipo:** Nueva funcionalidad — primera pantalla real del modo en vivo (Docente)
- **Puntos:** 5 (estimado, no está en la spec — mismo orden de magnitud que `US-6.3.4`)
- **Prioridad:** Alta — bloquea `US-6.3.6` (proyección)

## Decisiones de Ejecución
- **BDD:** Sí — la spec trae 10 escenarios Gherkin completos
- **skip_bdd:** false (validados con Vitest, sin step_defs — mismo criterio que `US-6.3.4`)
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5 (adaptadas a frontend/Vitest), 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (backend) — para frontend, sigue el patrón de
  `US-2.1.8`/`US-3.4.1`/`US-6.3.4`: `lib/*-api.ts` ya construido, pantallas + tests Vitest, sin
  arquitectura en capas formal
- **Umbrales de calidad (frontend):** `oxlint` 0 errores, `tsc -b` 0 errores, cobertura ≥ 80%

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.5-context.md`
- Plan: `docs/plans/inc6/US-6.3.5-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.5-report.md`
- Quality report: `quality/reports/inc6/US-6.3.5-quality.json`

## Notas propias de esta US
- **Primer consumidor real de `useCanalSesionEnVivo`** (`US-6.3.4`) — la sala de espera lo usa
  para `participantes_actualizados` y `onReconectado`.
- **Gap frontend detectado en Fase 0** (no de backend): `ComisionDetalleResponse`
  (`identidad-comisiones-api.ts`) no expone `materiaId` aunque el backend ya lo devuelve
  (`mapearDetalle` lo descarta) — hace falta para resolver el nombre de la Materia en la sala de
  espera (`GET estado` no trae `materiaId`, solo `comisionId`). Se agrega el campo, cambio
  aditivo, sin tocar `src/`.
- **Breadcrumb:** la spec (texto del wireframe) dice "Actividad evaluativa › {Materia} ›
  {Comisión} › …", pero la convención ya implementada en todo el BC (`Actividades.tsx`,
  `ComisionesDeMateria.tsx`, `NuevaActividad.tsx`) usa "Mis materias" como raíz — se sigue la
  convención de código ya establecida, no el texto literal del wireframe (etiqueta, no
  contenido/comportamiento — no amerita consultar a Víctor).
- **Sin selector de Comisión** en el formulario — `comisionId` viene de la ruta.
- **Badge de estado nuevo:** `estado-en-espera` (ámbar) en `badge.tsx`, para el bloque de
  sesiones activas de `ComisionDetalleDocente.tsx` (H6). `estado-en-curso` ya existe y se
  reutiliza.
