# Contexto de Ejecución — US-ADJ-58

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-58.md` (decisiones aprobadas por Víctor 2026-09-27), Issue #445
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna", `docs/architecture/`, `BC-actividad-evaluativa-modelo.md` §§10-18
- **Fuente UX:** `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §8 + prototipo, pantallas 20-22 (gate aprobado 2026-09-27)

## Historia de Usuario
- **ID:** US-ADJ-58
- **Título:** Cancelar una sesión no iniciada, terminar una en curso en cualquier etapa, y no iniciar sin participantes
- **Tipo:** Nueva funcionalidad + mejora de comportamiento existente (backend + frontend)
- **Puntos:** 5 (estimado)
- **Prioridad:** Alta — primera US de `SP-ADJ-02`, completa el modo en vivo antes de `BL-011`

## Decisiones de Ejecución
- **Perfil:** `clean-architecture-bc`
- **BDD:** Sí — 9 escenarios de la spec
- **Fases a ejecutar:** 0 a 9

## Umbrales de calidad
- Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95% del código nuevo; CodeGuard con `--analysis-type full`
- Frontend: `npm run test:coverage` (umbral 80% branches), `tsc -b` y `oxlint` 0 errores
- Pre-push: DesignReviewer 0 CRITICAL (vigilar CBO de controllers y del aggregate)

## Rutas de Artefactos
- Contexto: `docs/plans/sp-adj-02/US-ADJ-58-context.md`
- BDD feature: `tests/features/sp-adj-02/US-ADJ-58-cancelar-finalizar-sesion.feature`
- Step defs: `tests/step_defs/sp-adj-02/test_us_adj_58_steps.py`
- Plan: `docs/plans/sp-adj-02/US-ADJ-58-plan.md`
- Reporte: `docs/reports/sp-adj-02/US-ADJ-58-report.md`
- Quality report: `quality/reports/sp-adj-02/US-ADJ-58-quality.json`

## Hallazgos de la Fase 0 (lectura de código)
- `ActividadEvaluativaEnVivo.iniciar()` no exige participantes a propósito (`US-6.1.4`); el conteo sale de
  `ParticipantesSesionQueryPort.listar()` (ya existe, lo usa `ListarParticipantesUseCase`).
- `finalizar()` exige `pregunta_actual_cerrada` (`_validar_para_finalizar`) — INV-AEV-03 a relajar.
- El listado de sesiones (`SQLAlchemySesionesEnVivoQueryRepository`) filtra por `estados` pedidos por el cliente y
  deriva el estado con un mapa `event_type → estado` propio (duplicado del aggregate): sumar
  `SesionEnVivoCancelada → Cancelada` en ambos mapas. El frontend ya pide solo `EnEspera`/`EnCurso`.
- `validar_para_unirse()` solo rechaza `Finalizada`; una sesión `Cancelada` también debe rechazar la unión.
- Controllers: `ConduccionEnVivoController` tiene 4 use cases y `SesionesEnVivoController` 3 — decidir en la Fase 2
  dónde vive `CancelarSesionEnVivoUseCase` cuidando el CBO.
- Regla local: no correr `tests/integration` ni BDD contra la base local compartida (la vacían); solo `tests/unit`.
  Integración y BDD se verifican en CI.
