# Contexto de Ejecución — US-ADJ-69

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-69.md`, Issue [#604](https://github.com/vvalotto/cognion/issues/604) (cierra [#502](https://github.com/vvalotto/cognion/issues/502) al mergear)
- **Fuente UX:** `docs/design/ux/wireframes-identidad.md` §2.2b y prototipo `docs/design/ux/prototipos/identidad-registro-login.html` (`#login-aviso`), aprobados el 2026-11-08
- **Origen:** observación O-1 de la UAT del 7-ADJ; decisión de Víctor del 2026-11-08 (opción 3, avisar antes)
- **Código existente:** `src/identidad/use_cases/iniciar_sesion.py` (contador `intentos_fallidos_login`, `_INTENTOS_MAXIMOS = 3`), `src/identidad/entities/errors.py` (`CredencialesInvalidas`), `src/identidad/frameworks/api/auth_router.py` (401 con `detail` texto), patrón a seguir: `PasswordActualIncorrecta.intentos_restantes` y `perfil_router.py` (`detail` objeto). Frontend: `frontend/src/pages/identidad/Login.tsx` y `LoginError.tsx`

## Historia de Usuario
- **ID:** US-ADJ-69 — El login avisa "te queda 1 intento" tras el 2.º fallo
- **Tipo:** ajuste de producto, backend + frontend (Identidad)
- **Puntos:** 3 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 2 (rama `feature/inc-9-iter-2-link-grupal`, un commit por US y un solo PR al cierre)

## Decisiones de Ejecución
- **El aviso se fija en el caso de uso**, no en el router: `IniciarSesionUseCase` ya incrementa el contador; cuando queda 1 intento marca `CredencialesInvalidas.intentos_restantes = 1`. El atributo es `None` por defecto (primer fallo y fallo que bloquea).
- **Solo "queda 1"**: el backend no informa 2 ni 0. Revela lo mínimo, como pide el wireframe.
- **Contrato HTTP:** con aviso, `detail` es `{"mensaje": ..., "intentos_restantes": 1}`; sin aviso, el texto de siempre. No cambia ningún status code (el 3.er fallo sigue `401` y el 4.º `403`).
- **Email inexistente:** el caso de uso lanza `CredencialesInvalidas` sin tocar contadores; nunca lleva `intentos_restantes`.
- **Frontend:** `Login.tsx` lee `err.detail.intentos_restantes` y se lo pasa a `LoginError`; el link lleva a `/recuperar-password` (ya existe).
- **Tests:** unitarios del caso de uso y de la excepción (sin base); BDD de punta a punta por HTTP con base descartable inline (como `US-2.2.1`); Vitest para `Login`/`LoginError`.
- **Documentación a enmendar** en Fase 8: specs de `US-2.2.1` y `US-ADJ-60`, `BC-identidad-modelo.md` (`INV-ID-10`) y el docstring de `CredencialesInvalidas`.
- **Fases:** todas, con BDD.

## Rutas
- Plan: docs/plans/inc9/US-ADJ-69-plan.md · Reporte: docs/reports/inc9/US-ADJ-69-report.md · Quality: quality/reports/inc9/US-ADJ-69-quality.json
- Feature: tests/features/inc9/US-ADJ-69-aviso-ultimo-intento.feature
