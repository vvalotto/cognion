# Contexto de Ejecución — US-ADJ-25

## Fuentes
- **Fuente HU:** GitHub Issue [#270](https://github.com/vvalotto/cognion/issues/270) + spec `docs/specs/ajustes/US-ADJ-25.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first, perfil `clean-architecture-bc`)

## Historia de Usuario
- **ID:** US-ADJ-25
- **Título:** Administrador asigna un Docente a una Comisión
- **Tipo:** Nueva funcionalidad (pantalla de detalle de Comisión — no existía) + gap de backend detectado (GET /comisiones/{id} no existe)
- **Puntos:** 2
- **Prioridad:** Alta — precondición de `US-ADJ-26` (generar invitación)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación claros (Issue #270)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-first (entities/use_cases/interface_adapters/frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Gap detectado en Fase 0 (antes de escribir la spec)

No existe ningún endpoint `GET /comisiones/{comision_id}` — la pantalla de detalle de
Comisión necesita mostrar horario + docentes asignados de una comisión puntual sin conocer de
antemano su `materia_id` (se llega ahí por navegación directa desde `Comisiones.tsx` o desde
`NuevaComision.tsx` tras crear). `ComisionRepositoryPort.obtener_por_id()` ya devuelve
exactamente esos datos (incluidos los docentes vía `selectinload`, `US-ADJ-23`) — falta
exponerlo por HTTP. Se agrega a `ComisionesQueryController` (mismo patrón que
`listar_estudiantes`, sin Use Case dedicado — la Query ya es un pass-through fino sobre el
repositorio) y un endpoint nuevo con el guard `require_docente_o_administrador` ya existente
(reutilizable por `US-ADJ-26`, que necesitará el mismo dato para el Docente).

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-25-context.md`
- BDD feature: `tests/features/inc4-adj/US-ADJ-25-asignar-docente-comision.feature`
- Plan: `docs/plans/inc4-adj/US-ADJ-25-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-25-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-25-quality.json`
