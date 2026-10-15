# Contexto de Ejecución — US-ADJ-62

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-62.md`, Issue [#477](https://github.com/vvalotto/cognion/issues/477)
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna", `docs/architecture/`, `docs/design/domain/BC-identidad-modelo.md`
- **Fuente UX (solo Parte B):** `docs/design/ux/wireframes-cuentas-administracion.md` §2.8 + prototipo `identidad-cuentas-administracion.html` (`#login-bloqueada`) — **requiere actualización y aprobación de Víctor antes de tocar `frontend/`**

## Historia de Usuario
- **ID:** US-ADJ-62
- **Título:** Recuperar la contraseña por autoservicio también desbloquea la cuenta
- **Tipo:** fix backend (reversa decisión de US-ADJ-39) + copy de frontend
- **Puntos:** 2
- **Prioridad:** Media — hallazgo #5 🟡 de la UAT v1; tercera US del Incremento 7-ADJ

## Decisiones de Ejecución
- **Perfil:** `clean-architecture-bc`; BDD sí (escenarios de la spec); fases 0 a 9.
- **Parte A (backend)** se implementa completa en esta corrida. **Parte B (frontend)** queda
  bloqueada por el gate UX: el copy de `#login-bloqueada` está aprobado con la regla anterior.
- Revierte `US-ADJ-39`: hay que enmendar spec, feature/steps, wireframes §3.1 y modelo de dominio
  (`INV-ID-10`).

## Umbrales de calidad
- Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95% del código nuevo; CodeGuard `--analysis-type full`
- Pre-push: DesignReviewer 0 CRITICAL

## Rutas de Artefactos
- Contexto: `docs/plans/inc7-adj/US-ADJ-62-context.md`
- BDD feature: `tests/features/inc7-adj/US-ADJ-62-recuperar-password-desbloquea.feature`
- Step defs: `tests/step_defs/inc7-adj/test_us_adj_62_steps.py`
- Plan: `docs/plans/inc7-adj/US-ADJ-62-plan.md`
- Reporte: `docs/reports/inc7-adj/US-ADJ-62-report.md`
- Quality report: `quality/reports/inc7-adj/US-ADJ-62-quality.json`

## Regla local de ejecución de tests
`tests/unit` corre sobre la base local. `tests/integration` y BDD vacían la base compartida:
correrlos solo contra una base descartable con `DATABASE_URL` inline (nunca `export` suelto).

## Hallazgos de la Fase 0 (lectura de código)
- `Usuario.recuperar_password()` solo fija el hash; `resetear_password()` ya hace todo lo que pide
  la spec (hash, `bloqueada=False`, `bloqueada_hasta=None`, contadores a 0, devuelve si estaba
  bloqueada) — `recuperar_password` puede delegar.
- `ConfirmarNuevaPasswordUseCase.execute` devuelve `tuple[Usuario, PasswordRecuperada]`; pasa a
  `tuple[Usuario, PasswordRecuperada, CuentaDesbloqueada | None]` (patrón de `ResetearPasswordUseCase`).
- `RecuperacionPasswordController.confirmar` descarta el evento (`_evento`); debe desempaquetar 3.
- `deshabilitada` no se toca (US-ADJ-59 sigue rechazando el login).
