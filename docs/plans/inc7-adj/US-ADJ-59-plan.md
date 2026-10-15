# Plan de Implementación: US-ADJ-59 - Una cuenta deshabilitada no puede iniciar sesión

**Patrón:** Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`) + frontend React
**Producto:** cognion — BC Identidad
**Spec:** `docs/specs/ajustes/US-ADJ-59.md` · **Issue:** #474 · **UX aprobado:** `wireframes-cuentas-administracion.md` §2.9

## Componentes a Implementar

### 1. Parte A — Backend, BC Identidad
- [ ] `src/identidad/entities/errors.py`
  - `CuentaDeshabilitadaError(usuario_id)`, mismo patrón que `CuentaBloqueadaError`
  - Mensaje: "La cuenta está deshabilitada. Contactá a un administrador."
- [ ] `src/identidad/use_cases/iniciar_sesion.py`
  - Guarda `if usuario.deshabilitada: raise CuentaDeshabilitadaError(usuario.id)` **antes** del
    chequeo de `bloqueada` y de la verificación de contraseña (INV-ID-18)
  - No incrementa contadores ni llama a `actualizar`; sin dependencias nuevas (CBO sin riesgo)
  - Docstrings de la clase y de `execute` (orden de las guardas, prioridad sobre `bloqueada`)
- [ ] `src/identidad/frameworks/api/auth_router.py`
  - `except CuentaDeshabilitadaError` → `403` con `detail` **estructurado**
    `{"codigo": "cuenta_deshabilitada", "mensaje": str(exc)}`
  - El `403` de `CuentaBloqueadaError` conserva su `detail` en texto plano (contrato ya testeado)
  - Docstring del endpoint

### 2. Parte B — Frontend
- [ ] `frontend/src/pages/identidad/LoginCuentaDeshabilitadaError.tsx` (nuevo)
  - Alerta destructiva con ícono 🚫, título "Cuenta deshabilitada" y el texto del prototipo
    (pantalla 8), mismo markup que `LoginCuentaBloqueadaError.tsx`; sin link de recuperación
- [ ] `frontend/src/pages/identidad/Login.tsx`
  - Reemplazar el booleano `bloqueada` por un estado `bloqueo: "bloqueada" | "deshabilitada" | null`
  - Todo `403` sigue bloqueando el formulario (`fieldset`, marca oculta, sin link "Registrate");
    la alerta se elige por `err.detail.codigo === "cuenta_deshabilitada"` → deshabilitada,
    cualquier otro `403` → bloqueada (comportamiento actual intacto)
  - Lectura segura de `ApiError.detail` (`unknown`): sin `codigo` reconocible cae en bloqueada

### 3. Integración
- [ ] Sin cambios de composition root: `AuthController` ya propaga las excepciones del use case
  - El router es el único punto de mapeo a HTTP
- [ ] `ApiError` ya transporta `detail` estructurado (`api-client.ts` `extractError`, desde
  `US-2.2.8`): no hay cambios de infraestructura de frontend

**Fuera del plan (otras fases):** tests unitarios/integración/BDD (Fases 4-6), quality gates
(Fase 7), documentación del modelo — `BC-identidad-modelo.md` §3 (error de `IniciarSesion`) y §4
(`deshabilitada` + `INV-ID-18`) — (Fase 8, requiere tu aprobación).

**Estado:** ✅ COMPLETADO — 5/5 tareas
**Fecha completado:** 2026-10-03

## Métricas de Tiempo (tracking real)

Los tiempos de las fases 0 a 7 salen del tracker (`.claude/tracking/US-ADJ-59-tracking.json`);
la Fase 8 y el reporte final se miden al cerrar. Las esperas de aprobación de Víctor (Fases 1 y 2)
no están en estos tiempos.

| Fase | Real |
|------|------|
| 0 Validación de contexto | 2 min 35 s |
| 1 Escenarios BDD | 27 s |
| 2 Plan | 48 s |
| 3 Implementación (5 tareas) | 2 min 4 s |
| 4 Tests unitarios | 3 min 6 s |
| 5 Tests de integración | 3 min 14 s |
| 6 Validación BDD | 5 min 55 s |
| 7 Quality gates | 9 min 28 s |

## Lecciones Aprendidas
- 💡 **Se pueden correr integración y BDD sin tocar la base de desarrollo:** crear una base
  aparte (`psql -d postgres -c 'CREATE DATABASE …'` como superusuario local, `alembic upgrade
  head` con `DATABASE_URL` apuntando a ella) y borrarla al final. Así se verificó todo en
  local, igual que en `US-ADJ-58` (`cognion_test_adj58`), en vez de dejarlo para CI.
- ✅ Correrlas atrapó un error del propio test: `SQLAlchemyUsuarioRepository.guardar()` no
  persiste `deshabilitada`/`bloqueada`/contadores (solo `actualizar()`), así que un fixture que
  hacía `setattr` + `guardar` dejaba la cuenta activa y el test daba `200` en lugar de `403`.
- ⚠️ Los "errores" de CodeGuard en modo `full` (vulture/codespell no instalados, timeouts de
  pylint/mypy) vuelven a ser tooling, no código: hay que verificar pylint/mypy/radon por
  separado para tener valores reales.
- 💡 `ApiError.detail` estructurado (`US-2.2.8`) permitió distinguir dos `403` sin tocar la
  infraestructura del frontend.
