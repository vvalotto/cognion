# Reporte de Implementación: US-ADJ-59

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-59 — Una cuenta deshabilitada no puede iniciar sesión
- **Iteración:** `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1` (primera US, antes de RF-07)
- **Puntos estimados:** 3
- **Tiempo real:** ver `.claude/tracking/US-ADJ-59-tracking.json` (PRIN-001: tiempo de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-10-03
- **Origen:** UAT manual de cierre de alcance v1, hallazgo **#11** 🔴 (`quality/reports/uat/inc7/registro-hallazgos.md`)
- **Aporta:** dar de baja una cuenta ahora impide de verdad el inicio de sesión; hasta hoy un Docente "Inactivo" recibía token válido y operaba la API

---

## Decisiones (Víctor, 2026-10-03 — propuestas por defecto de la spec)

1. Error propio `403` con `detail` estructurado `cuenta_deshabilitada` (no reutiliza el `401` de credenciales inválidas).
2. Se chequea **antes** de verificar la contraseña, sin consumir intentos.
3. `deshabilitada` tiene prioridad sobre `bloqueada`.
4. Solo en el login: las sesiones ya emitidas viven hasta expirar (decisión 2 del plan de corrección, `ADR-013`).

**Gate UX (aprobado 2026-10-03):** pantalla `#login-deshabilitada` (ícono 🚫, "Cuenta deshabilitada", sin link de recuperación).

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `errors.py` — `CuentaDeshabilitadaError(usuario_id)`

### Use Cases
- ✅ `iniciar_sesion.py` — guarda `if usuario.deshabilitada` antes de `bloqueada` y de la contraseña (INV-ID-18); sin dependencias nuevas

### Interface Adapters y Frameworks
- ✅ `frameworks/api/auth_router.py` — `403` con `detail` `{"codigo": "cuenta_deshabilitada", "mensaje": ...}`; el `403` de bloqueada conserva su texto plano

### Frontend
- ✅ `pages/identidad/LoginCuentaDeshabilitadaError.tsx` (nuevo) — alerta destructiva del prototipo
- ✅ `pages/identidad/Login.tsx` — el booleano `bloqueada` pasa a `bloqueo: "bloqueada" | "deshabilitada" | null`; todo `403` bloquea el formulario y la alerta se elige por `detail.codigo`

### Documentación
- ✅ `docs/design/domain/BC-identidad-modelo.md` — `CuentaDeshabilitadaError`, fila `deshabilitada` (no figuraba) e `INV-ID-18`
- ✅ `docs/design/ux/wireframes-cuentas-administracion.md` §2.9 + prototipo `identidad-cuentas-administracion.html` (pantalla 8)
- ✅ `docs/specs/ajustes/US-ADJ-59.md` (estado), `docs/plans/inc7-adj/US-ADJ-59-context.md` y `-plan.md`

---

## Tests

| Nivel | Resultado |
|-------|-----------|
| Unitarios backend (`tests/unit`) | 853/853 ✅ — nueva `TestCuentaDeshabilitadaLogin` (6) en `test_iniciar_sesion_use_case.py` |
| Integración | 6/6 ✅ nuevos (`tests/integration/inc7-adj/`) + suite de Identidad completa 267/267 sin regresiones |
| BDD | 6/6 ✅ escenarios backend (`tests/step_defs/inc7-adj/`); el escenario `@frontend` se cubre con Vitest |
| Frontend (Vitest) | 807/807 ✅ — statements 93,51 %, branches 85,79 %; `Login.tsx` 94,87 % / 92,59 % |

**Cómo se verificó integración y BDD:** contra una base aparte (`cognion_us59`, creada y migrada solo para esto y luego borrada), no contra la base de desarrollo, que quedó intacta (6 usuarios antes y después).

**Un error propio detectado al correrlos:** el primer intento de integración falló 4/6 porque el fixture hacía `setattr` + `guardar()` y `SQLAlchemyUsuarioRepository.guardar()` no persiste `deshabilitada`/`bloqueada`/contadores (solo `actualizar()`); la cuenta quedaba activa y el login daba `200`. Era un error del test, no del código; corregido antes de commitear.

---

## Quality Gates (`quality/reports/inc7-adj/US-ADJ-59-quality.json`)

| Métrica | Valor | Umbral | |
|---|---|---|---|
| pylint (archivos tocados) | 9,93 | ≥ 8,0 | ✅ |
| CC máx / promedio | 6 / 1,73 | ≤ 10 | ✅ |
| MI mínimo | 68,97 | > 20 | ✅ |
| Cobertura (módulos tocados, unit + integración) | `iniciar_sesion.py` 100 %, `errors.py` 97,6 % | ≥ 95 % | ✅ |
| mypy `src/` | 0 errores (300 archivos) | 0 | ✅ |
| oxlint / `tsc -b` | 0 errores / limpio | 0 | ✅ |

### Detalle de CodeGuard (`--analysis-type full`, 9 checks ejecutados)

| Check | Errors | Warnings | Nota |
|---|---|---|---|
| Security, PEP8, Complexity, Maintainability | 0 | 0 | — |
| DeadCode / Spelling | 3 / 3 | 0 | tooling: `vulture` y `codespell` no instalados en el venv |
| Pylint / Types / UnusedImports | 2 / 3 / 3 | 1 | timeouts conocidos (>10 s / >5 s, `software_limpio#70`) y un score parcial de `auth_router.py` en aislamiento; pylint directo sobre los 3 archivos: 9,93 (único mensaje, R0903 preexistente del use case) |

Los 14 "errors" son del tooling, no defectos del código (mismo patrón que `US-ADJ-58`).

---

## Criterios de Aceptación

- ✅ Login con contraseña correcta sobre una cuenta deshabilitada → `403` con `codigo "cuenta_deshabilitada"`, sin JWT
- ✅ El rechazo no depende de la contraseña ni consume intentos
- ✅ Reactivar la cuenta restituye el acceso
- ✅ Deshabilitada y bloqueada a la vez → gana `cuenta_deshabilitada`
- ✅ Una cuenta activa no cambia de comportamiento
- ✅ Una cuenta bloqueada conserva su respuesta actual (`detail` en texto plano)
- ✅ El login muestra la alerta "Cuenta deshabilitada" con el formulario deshabilitado (Vitest)

---

## Notas

- **Limitación aceptada:** las sesiones ya emitidas siguen vivas hasta que expire su JWT (60 min, sin blacklist, `ADR-013`); una baja corta el acceso en el próximo login, no al instante. Si molesta, revalidar el estado en el guard (`src/shared`) se suma sin deshacer esto.
- **Pendiente para `US-ADJ-60`:** reutiliza el mismo discriminador `detail.codigo` en `Login.tsx` para `cuenta_bloqueada_temporal`, y su definición de "Administrador operativo" depende de que `deshabilitada` se haga cumplir (esta US).

## Próximos Pasos

- Mergear el PR a `develop`, sincronizar y cerrar el Issue #474.
- `US-ADJ-60` (siempre ≥ 1 Administrador operativo), con su propio paso de UX.
