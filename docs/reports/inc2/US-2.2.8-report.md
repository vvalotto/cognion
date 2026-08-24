# Reporte de Implementación: US-2.2.8

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.8 - Cualquier usuario autenticado cambia su propia contraseña (UI)
- **Puntos estimados:** 3
- **Tiempo real:** ~67 min (fases 0-8, ver `docs/plans/inc2/US-2.2.8-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-20

---

## Alcance

Consume `PUT /usuarios/me/password` (`US-2.2.5`), pantalla accesible a los tres roles (sin
`RequireRole`), a diferencia del resto de la Iteración 2. **Amplía el alcance previsto en la
spec**: dos gaps de diseño detectados durante la implementación (Fase 2 y Fase 3) llevaron a
extender el backend además del frontend.

---

## Componentes Implementados

### Backend (extensión mínima sobre `US-2.2.5`)
- ✅ **`Usuario.intentos_restantes_cambio_password()`** (`src/identidad/entities/usuario.py`)
  — `max(0, 3 - intentos_fallidos_password)`, reutiliza `_INTENTOS_MAXIMOS_CAMBIO_PASSWORD`
- ✅ **`PasswordActualIncorrecta.intentos_restantes`** (`src/identidad/entities/errors.py`) —
  nuevo atributo, mismo patrón que `evento_cuenta_bloqueada`
- ✅ **`cambiar_password.py`** (extendido) — fija `exc.intentos_restantes` tras registrar el fallo
- ✅ **`perfil_router.py`** (extendido) — `detail` del error pasa de string genérico a objeto
  estructurado (`{"mensaje", "intentos_restantes"}` o `{"mensaje", "bloqueada": true}`), sin
  cambiar ningún status code existente (401/403/422 se mantienen)

### Frontend
- ✅ **`api-client.ts`** (extendido) — `ApiError.detail` (cuerpo estructurado del error),
  opción `handleUnauthorized` en `apiFetch` (default `true`, no cambia ningún caller existente)
- ✅ **`cuentas-api.ts`** (extendido) — `cambiarPassword(passwordActual, passwordNueva)` con
  `handleUnauthorized: false`; `CambiarPasswordError` mapea el `detail` estructurado
  (snake_case→camelCase)
- ✅ **`CambiarPassword.tsx`** (nuevo) — un solo componente con los 3 estados del wireframe
  (formulario/error/éxito), sin ruta separada para el error; "Continuar" vuelve con
  `navigate(-1)`
- ✅ **`router.tsx`** — ruta `/mi-cuenta/cambiar-password`, sin `RequireRole`

---

## Gaps de diseño detectados durante la implementación

1. **Fase 2 (planificación):** la spec asumía que el backend de `US-2.2.5` exponía
   `intentos_fallidos_password` en el error del `PUT /usuarios/me/password` — no era así
   (`detail` string genérico). Decisión de Víctor: extender el backend.
2. **Fase 3 (implementación):** el plan aprobado en Fase 2 proponía 403 para el 3er fallo
   consecutivo (cuenta recién bloqueada); al correr la suite existente de `US-2.2.5`
   (`test_us_2_2_5_steps.py`) se detectó que ya afirmaba 401 en ese caso — corregido antes de
   tocar ningún test, manteniendo el contrato de `US-2.2.5` intacto.
3. **Fase 3 (implementación):** el interceptor global de 401 de `api-client.ts` (limpia sesión,
   navega a `/login`) rompía el criterio "no requiere volver a iniciar sesión" al mostrar el
   error de contraseña incorrecta. Resuelto con `handleUnauthorized: false`, sin tocar ningún
   status code del backend.

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (archivos backend tocados) | 9.88/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 5 | ≤ 10 | ✅ |
| Índice de Mantenibilidad | Grado A | ≥ 20 | ✅ |
| Coverage backend global | 99% | — | ✅ |
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `CambiarPassword.tsx` (statements/branches/lines) | 97.29% / 85.71% / 97.29% | ≥ 80% | ✅ |
| Coverage `cuentas-api.ts` (statements/branches) | 95.83% / 94.44% | ≥ 80% | ✅ |
| Pre-push gate (DesignReviewer) | 0 CRITICAL | 0 CRITICAL | ✅ |

Fuente: `quality/reports/inc2/US-2.2.8-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Backend (3 tests nuevos + 2 aserciones agregadas a tests existentes)
- `test_usuario.py` (+3 tests) — `intentos_restantes_cambio_password()` sin fallos, con
  fallos parciales, nunca negativo tras el bloqueo
- `test_cambiar_password_use_case.py` (aserciones agregadas a 2 tests existentes) —
  `intentos_restantes` correcto en fallo parcial (1) y en el 3er fallo (0)
- Suite completa backend: **357/357 passed**

### Frontend (12 tests nuevos, Vitest)
- `cuentas-api.test.ts` (+6 tests) — `cambiarPassword` hace PUT con el body correcto, no
  navega a `/login` ante un 401, lanza `CambiarPasswordError` con `intentosRestantes`, con
  `bloqueada=true` al 3er fallo y con cuenta ya bloqueada (403)
- `CambiarPassword.test.tsx` (6 tests) — cambio exitoso, "Continuar" vuelve a la pantalla de
  origen, rechaza contraseña corta/no coincidente sin llamar al backend, muestra intentos
  restantes y limpia campos, muestra bloqueo tras el 3er fallo

**BDD (3 escenarios frontend)**
- `tests/features/inc2/US-2.2.8-cambiar-password.feature` — validados por mapeo directo a los
  tests de `CambiarPassword.test.tsx` (sin step_defs/pytest-bdd, misma adaptación de
  `US-2.2.6`/`US-2.2.7`)

**Todos los tests pasando:** ✅ 357/357 backend, 145/145 frontend

---

## Archivos Creados/Modificados

### Código de producción — backend
- `src/identidad/entities/usuario.py` (extendido)
- `src/identidad/entities/errors.py` (extendido)
- `src/identidad/use_cases/cambiar_password.py` (extendido)
- `src/identidad/frameworks/api/perfil_router.py` (extendido)

### Código de producción — frontend
- `frontend/src/lib/api-client.ts` (extendido)
- `frontend/src/lib/cuentas-api.ts` (extendido)
- `frontend/src/pages/CambiarPassword.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado)

### Tests
- `tests/features/inc2/US-2.2.8-cambiar-password.feature` (nuevo)
- `tests/unit/inc1/test_usuario.py` (extendido)
- `tests/unit/inc1/test_cambiar_password_use_case.py` (extendido)
- `frontend/src/lib/cuentas-api.test.ts` (extendido)
- `frontend/src/pages/CambiarPassword.test.tsx` (nuevo)

### Documentación
- `docs/specs/inc2/US-2.2.8.md` (ya existente, ampliado en alcance por los gaps de diseño)
- `docs/plans/inc2/US-2.2.8-context.md`
- `docs/plans/inc2/US-2.2.8-plan.md`
- `docs/reports/inc2/US-2.2.8-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.8-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)
- `CLAUDE.md` (estado del incremento actualizado)

---

## Criterios de Aceptación

- [x] Cambio exitoso — ejecuta el cambio, navega a la confirmación de éxito, aclara que no
  requiere volver a iniciar sesión
- [x] Contraseña actual incorrecta — muestra la alerta con los intentos restantes, limpia los
  campos para reintentar
- [x] La cuenta queda bloqueada tras el tercer fallo — muestra que la cuenta quedó bloqueada,
  indica contactar a un Administrador

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.9` — Login refleja el estado de cuenta bloqueada (UI, Issue #104) — última US de
  la Iteración 2
- [ ] UAT de cierre de la Iteración 2 y evaluación de cierre de baseline (`BL-003`)

---

## Lecciones Aprendidas

- ⚠️ Cuando una US extiende un endpoint ya shippeado y testeado, correr la suite de tests de
  ese endpoint **antes** de escribir el código nuevo (no solo al final de Fase 3) habría
  anticipado el conflicto de status code con `US-2.2.5` sin necesidad de corregirlo a mitad de
  implementación.
- ✅ Resolver el conflicto del interceptor global de 401 en el frontend (opción
  `handleUnauthorized`) en vez de tocar el status code del backend acotó el riesgo de esta
  extensión a un único archivo (`api-client.ts`), sin afectar ningún caller existente ni los
  tests ya verdes de `US-2.2.5`.
- 💡 Exponer `intentos_restantes` como atributo mutable post-construcción en la excepción de
  dominio (mismo patrón que `evento_cuenta_bloqueada` de `US-2.2.1`) evitó rediseñar la firma
  de `PasswordActualIncorrecta()`, consistente con el estilo ya establecido en el BC.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-20
