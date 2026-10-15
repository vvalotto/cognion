# Contexto de Ejecución — US-ADJ-60

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-60.md`, Issue [#475](https://github.com/vvalotto/cognion/issues/475)
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna", `docs/architecture/`, `docs/design/domain/BC-identidad-modelo.md`
- **Fuente UX:** `docs/design/ux/wireframes-cuentas-administracion.md` §2.10 y §2.11 + prototipo `identidad-cuentas-administracion.html` pantallas 9, 10 y 11 (gate aprobado por Víctor 2026-10-03)

## Historia de Usuario
- **ID:** US-ADJ-60
- **Título:** El sistema siempre conserva al menos un Administrador operativo
- **Tipo:** feat backend + migración + frontend (INV-ID-19/20/21)
- **Puntos:** 5
- **Prioridad:** Alta — hallazgo #4 🔴 de la UAT v1; segunda US del Incremento 7-ADJ

## Decisiones de Ejecución
- **Perfil:** `clean-architecture-bc`; BDD sí (11 escenarios de la spec); fases 0 a 9.
- **Una sola US con Parte A (backend + migración) y Parte B (frontend)**, gate UX ya aprobado.
- Duración del bloqueo temporal: `settings.administrador_bloqueo_temporal_minutos` = 15, inyectada desde `frameworks/dependencies.py`.

## Umbrales de calidad
- Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95% del código nuevo; CodeGuard `--analysis-type full`
- Frontend: `npm run test:coverage` (80% branches), `tsc -b` y `oxlint` 0 errores
- Pre-push: DesignReviewer 0 CRITICAL (vigilar CBO en `EliminarCuentaUseCase`)

## Rutas de Artefactos
- Contexto: `docs/plans/inc7-adj/US-ADJ-60-context.md`
- BDD feature: `tests/features/inc7-adj/US-ADJ-60-siempre-un-administrador-operativo.feature`
- Step defs: `tests/step_defs/inc7-adj/test_us_adj_60_steps.py`
- Plan: `docs/plans/inc7-adj/US-ADJ-60-plan.md`
- Reporte: `docs/reports/inc7-adj/US-ADJ-60-report.md`
- Quality report: `quality/reports/inc7-adj/US-ADJ-60-quality.json`

## Regla local de ejecución de tests
`tests/unit` y Vitest corren sobre la base local. `tests/integration` y BDD vacían la base
compartida: correrlos solo contra una base descartable (`CREATE DATABASE` + `alembic upgrade
head` + `DATABASE_URL` propio, y `DROP DATABASE` al terminar). La migración nueva se verifica
con round-trip `upgrade`/`downgrade` sobre esa base.

## Hallazgos de la Fase 0 (lectura de código)
- `Usuario` (entidad) no tiene `bloqueada_hasta`; `registrar_fallo_cambio_password()` bloquea
  siempre de forma permanente; `IniciarSesionUseCase` bloquea inline (`usuario.bloqueada = True`).
- `EliminarCuentaUseCase` trata al Administrador como cualquier cuenta (borra si no creó
  Comisiones). `tiene_comisiones_creadas` queda sin uso tras la Regla 1.
- `CambiarPasswordUseCase` e `IniciarSesionUseCase` ya reciben el `UsuarioRepositoryPort`:
  el conteo de Administradores operativos va ahí, sin colaboradores nuevos (CBO).
- El `detail` estructurado ya tiene patrón (`US-ADJ-59`, `US-2.2.8`); `ApiError.detail?: unknown`.
- `resetear_password` ya limpia `bloqueada` y contadores: agrega `bloqueada_hasta = None`.
