# Reporte de Implementación: US-ADJ-62

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-62 — Recuperar la contraseña por autoservicio también desbloquea la cuenta
- **Iteración:** `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1` (tercera US)
- **Puntos estimados:** 2
- **Tiempo real:** ver `.claude/tracking/US-ADJ-62-tracking.json` (PRIN-001)
- **Estado:** ✅ Parte A (backend) COMPLETADA · ⏳ Parte B (frontend) pendiente del gate UX
- **Fecha completado (Parte A):** 2026-10-04
- **Origen:** UAT manual de cierre de alcance v1, hallazgo **#5** 🟡 (`quality/reports/uat/inc7/registro-hallazgos.md`)
- **Aporta:** quien canjea el link de recuperación recibido por email ya no queda bloqueado: la cuenta se desbloquea y los contadores vuelven a 0. Revierte la decisión de `US-ADJ-39`.

## Componentes Implementados

### Entities
- ✅ `usuario.py` — `recuperar_password()` delega en `resetear_password()` y devuelve si la cuenta estaba bloqueada (limpia también `bloqueada_hasta`); no toca `deshabilitada`
- ✅ `eventos.py` — docstring de `CuentaDesbloqueada` (reseteo **o recuperación**)

### Use Cases
- ✅ `confirmar_nueva_password.py` — devuelve `(Usuario, PasswordRecuperada, CuentaDesbloqueada | None)`; el evento de desbloqueo solo si estaba bloqueada

### Interface Adapters y Frameworks
- ✅ `recuperacion_password_controller.py` — desempaqueta los 3 valores, contrato de retorno sin cambios
- ✅ `recuperacion_password_router.py` — docstring; contrato HTTP sin cambios (mismo endpoint y status)

### Frontend
- ⏳ `LoginCuentaBloqueadaError.tsx` — **no implementado**: el copy de `#login-bloqueada` está aprobado con la regla anterior; hay que actualizar prototipo y `wireframes-cuentas-administracion.md` §2.8 y obtener la aprobación de Víctor (gate UX). Sin esto el Issue #477 no se cierra.

### Documentación
- ✅ `BC-identidad-modelo.md` (enmienda a INV-ID-10, `CuentaDesbloqueada` en `ConfirmarNuevaPassword`), `US-ADJ-39.md` (enmendada), `wireframes-identidad-autoservicio.md` §3.1 y "Fuera de alcance", spec de esta US

## Tests

| Nivel | Resultado |
|-------|-----------|
| Unit backend | 879/879 ✅ (corregidos y nuevos en `test_usuario.py` y `test_confirmar_nueva_password_use_case.py`) |
| Integración | 6 nuevos (`tests/integration/inc7-adj/test_recuperar_password_desbloquea_api_integration.py`) + 14 de `inc5-adj` ✅ |
| BDD | 7 de esta US + 6 de US-ADJ-39 (escenario enmendado) = 13/13 ✅ |

Los tests se corrieron por fases contra una base descartable (`DATABASE_URL` inline). **En Fase 7 no se re-ejecutó la suite completa ni se midió cobertura**, por decisión de Víctor (ya corridos en Fases 4-6). El evento `CuentaDesbloqueada` no es observable por HTTP: el BDD verifica la transición de estado y su emisión exacta la cubre el test unitario del use case.

Verificación: `mypy` 0 errores (303 archivos), `ruff` limpio en los archivos tocados, `pylint` 9,85 (único aviso preexistente: R0903 en el use case), CC máx. B (8, preexistente), MI mín. 64,10. CodeGuard `--analysis-type full` (9 checks): sus 14 errores son de tooling (vulture y codespell no instalados; timeouts de bandit/mypy/pylint con la suite corriendo en paralelo), no del código. Detalle en `quality/reports/inc7-adj/US-ADJ-62-quality.json`.

## Decisiones y notas

- Se reutilizó `resetear_password()` en vez de duplicar la lógica: los dos métodos eran idénticos salvo por no desbloquear.
- Los tests existentes de US-ADJ-39 que afirmaban "sigue bloqueada" (unit, feature y steps) se invirtieron a la regla nueva.
- Una cuenta `deshabilitada` sigue sin poder iniciar sesión tras recuperar la contraseña (`US-ADJ-59`).

## Próximos pasos

1. Parte B: actualizar prototipo y wireframe §2.8 con el copy que ofrece la recuperación por email y el link a `/recuperar-password`; aprobación de Víctor; luego `LoginCuentaBloqueadaError.tsx` + test.
2. Cerrar el Issue #477 recién al completar la Parte B.
