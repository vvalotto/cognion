# Plan de Implementación — US-ADJ-62

Spec: `docs/specs/ajustes/US-ADJ-62.md` · Contexto: `US-ADJ-62-context.md` · BDD: 7 escenarios (Parte A).
Orden: dominio → use case → controller → router → tests existentes → docs. Sin migración, sin puertos nuevos.

## Parte A — Backend (esta corrida)

- [ ] **T1** `Usuario.recuperar_password(hash) -> bool`: delega en `resetear_password` (hash, `bloqueada=False`, `bloqueada_hasta=None`, contadores a 0) y devuelve si estaba bloqueada. No toca `deshabilitada`. Docstring. — `src/identidad/entities/usuario.py`
- [ ] **T2** Docstring de `CuentaDesbloqueada` ("tras un reseteo o una recuperación"). — `src/identidad/entities/eventos.py`
- [ ] **T3** `ConfirmarNuevaPasswordUseCase.execute` devuelve `tuple[Usuario, PasswordRecuperada, CuentaDesbloqueada | None]` (evento solo si estaba bloqueada); docstring. — `src/identidad/use_cases/confirmar_nueva_password.py`
- [ ] **T4** `RecuperacionPasswordController.confirmar` desempaqueta 3 valores (contrato de retorno sin cambios). — `src/identidad/interface_adapters/controllers/recuperacion_password_controller.py`
- [ ] **T5** Docstring del router (quitar "No desbloquea la cuenta…"); contrato HTTP sin cambios. — `src/identidad/frameworks/api/recuperacion_password_router.py`

## Parte B — Frontend (bloqueada por gate UX)
- [ ] **T6** `LoginCuentaBloqueadaError.tsx` con link a `/recuperar-password` — solo tras actualizar prototipo/wireframe §2.8 y aprobación de Víctor. **No se hace en esta corrida.**

## Tests (Fases 4-6)
- Actualizar: `tests/unit/inc1/test_usuario.py`, `test_confirmar_nueva_password_use_case.py`, `test_recuperacion_password_controller.py` (fakes/tuplas, regla nueva).
- Enmendar: `tests/features/inc5-adj/US-ADJ-39-*.feature` (escenario "no desbloquea") y `tests/step_defs/inc5-adj/test_us_adj_39_steps.py`.
- Nuevo: unit en `tests/unit/inc7-adj/`; integration en `tests/integration/inc7-adj/` (base descartable); `tests/step_defs/inc7-adj/test_us_adj_62_steps.py`.

## Docs (Fase 8)
`US-ADJ-39.md` (nota "Enmendada por US-ADJ-62"), `wireframes-identidad-autoservicio.md` §3.1 y "Fuera de alcance", `BC-identidad-modelo.md` (enmienda INV-ID-10), spec → "Implementada (Parte A)".

## Riesgos
- Cambio de firma del use case rompe tests existentes que desempaquetan 2 valores: se corrigen en el mismo cambio.
- CBO: no se agregan colaboradores a ningún controller/use case.
- Parte B queda pendiente: el Issue #477 no se cierra hasta completarla.
