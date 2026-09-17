# Contexto de Ejecución — US-ADJ-43

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-43.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (perfil `clean-architecture-bc`)

## Historia de Usuario
- **ID:** US-ADJ-43
- **Título:** Pantallas de autoregistro con selección de perfil
- **Tipo:** Nueva funcionalidad (frontend nuevo, consume backend existente)
- **Puntos:** 5
- **Prioridad:** Tercera y última de la Iteración 3 del Incremento 5-ADJ — cierra la
  iteración (depende de `US-ADJ-41`/`US-ADJ-42`, ya cerradas)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad de UI, mismo criterio que `US-ADJ-38`/`39`/`40`/`41`/`42`
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (sin capas de dominio nuevas — frontend puro)
- **Umbrales de calidad:**
  - Backend: N/A (esta US no toca `src/`)
  - Frontend: oxlint 0 errores, `tsc -b` 0 errores, cobertura de branches ≥ 80% (umbral
    global del proyecto desde `US-ADJ-16`)

## Rutas de Artefactos
- Contexto: `docs/plans/inc5-adj/US-ADJ-43-context.md`
- BDD feature: `tests/features/inc5-adj/US-ADJ-43-pantallas-autoregistro.feature`
- Plan: `docs/plans/inc5-adj/US-ADJ-43-plan.md`
- Reporte: `docs/reports/inc5-adj/US-ADJ-43-report.md`
- Quality report: `quality/reports/inc5-adj/US-ADJ-43-quality.json`

## Notas de alcance (de la spec)
- Frontend puro — sin cambios de backend, consume `POST /identidad/autoregistro/docente`
  (`US-ADJ-41`), `POST /identidad/autoregistro/estudiante` (`US-ADJ-42`), `GET /materias`
  (`US-2.1.9`) y `GET /materias/{id}/comisiones` (`US-4.2.2`).
- Gate UX ya satisfecho: `docs/design/ux/wireframes-identidad-autoservicio.md` §5/§7 +
  prototipo `docs/design/ux/prototipos/identidad-autoservicio.html`.
- Componentes: cliente API nuevo, 4 pantallas nuevas (`AutoregistroPerfil`,
  `AutoregistroDocente`, `AutoregistroEstudiante`, `AutoregistroExito`), link nuevo en
  `Login.tsx`, 4 rutas públicas nuevas en `router.tsx`.
