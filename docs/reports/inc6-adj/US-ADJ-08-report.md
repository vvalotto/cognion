# Reporte de Implementación: US-ADJ-08 - Estudiante ve la materia/comisión de la invitación antes de registrarse

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-08 |
| **Título** | Estudiante ve la materia/comisión de la invitación antes de registrarse |
| **Producto** | cognion (BC Identidad) |
| **Prioridad** | Media (deuda de UX relevada en UAT 2026-08-23) |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-30 |
| **Fecha fin** | 2026-09-30 |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

El prototipo aprobado de `identidad-registro-login.html` muestra un chip "Te vas a unir a
{materia} — {comisión}" antes del formulario de registro, que `Registro.tsx` nunca implementó
porque no existía ningún endpoint de solo lectura para consultar los datos de una invitación
antes de aceptarla — `POST /identidad/registro` valida y consume el token en la misma
operación. Esta US cierra el gap con un endpoint público nuevo (`GET
/identidad/invitaciones/{token}`) que reutiliza `Invitacion.verificar_vigente()` sin mutar la
invitación, y con el chip real en el frontend, usando el `horario` de la Comisión en lugar de
una letra ("Comisión A") que no existe en el dominio.

---

## Componentes Implementados

### Código Fuente

- ✅ `src/identidad/use_cases/obtener_invitacion.py` — `ObtenerInvitacionUseCase` (query) +
  `InvitacionPreview` (DTO sin datos sensibles)
- ✅ `src/identidad/interface_adapters/controllers/invitaciones_controller.py` — extendido con
  `obtener_invitacion()`, segunda dependencia inyectada
- ✅ `src/identidad/frameworks/api/schemas.py` — `InvitacionPreviewResponse`
- ✅ `src/identidad/frameworks/api/registro_router.py` — `GET /identidad/invitaciones/{token}`
- ✅ `src/identidad/frameworks/dependencies.py` — wiring del use case nuevo
- ✅ `frontend/src/pages/identidad/Registro.tsx` — fetch al montar, chip `.comision-tag`,
  estados de carga/error

**Total archivos de producción:** 6 (5 backend + 1 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc1/test_obtener_invitacion_use_case.py` — 5 tests
- ✅ `tests/unit/inc1/test_invitaciones_controller.py` — 3 tests (2 existentes actualizados al
  nuevo constructor + 1 nuevo)

**Total tests unitarios backend:** 8 nuevos/actualizados — **847/847** pasando (suite completa)

#### Tests de Integración
- ✅ `tests/integration/inc1/test_obtener_invitacion_api_integration.py` — 5 tests

**Estado:** 5/5 pasando — **570/571** en la suite completa de integración (el único fallo,
`test_notificar_apertura_actividad_integration.py`, confirmado como colisión de concurrencia
ajena al re-ejecutarlo aislado: 4/4 pasando)

#### Escenarios BDD
- ✅ `tests/features/inc6-adj/US-ADJ-08-invitacion-preview.feature` — 5 escenarios
- ✅ `tests/step_defs/inc6-adj/test_us_adj_08_steps.py`

**Estado:** 5/5 pasando

#### Frontend
- ✅ `frontend/src/pages/identidad/Registro.test.tsx` — 10 tests (4 nuevos/reescritos por el
  fetch de preview + 6 existentes adaptados)

**Estado:** 10/10 pasando — **800/800** en la suite completa de frontend

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (real, sobre los archivos tocados) | 10.00/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx/función) | 4 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** (mín) | 59.36 | > 20 | ✅ |
| **Coverage** (entities/use_cases/interface_adapters) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (5 archivos modificados/agregados) | 10 errors, 1 warning | 0 CRITICAL | ✅ |
| **tsc -b** (frontend) | 0 errores | 0 errores | ✅ |
| **oxlint** (frontend) | 0 errores (1 warning preexistente, línea 38, no introducido) | 0 errores | ✅ |

### Detalle de Coverage

```
Name                                                                      Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------------------------------------
src/identidad/interface_adapters/controllers/invitaciones_controller.py      14      0   100%
src/identidad/use_cases/obtener_invitacion.py                                26      0   100%
-------------------------------------------------------------------------------------------------------
TOTAL                                                                         40      0   100%
```

`frameworks/*` está excluido del gate de coverage por diseño (`[tool.coverage.run] omit` en
`pyproject.toml`) — coherente con el resto del proyecto; `schemas.py`, `registro_router.py` y
`dependencies.py` se verifican por los tests de integración/BDD, no por el gate de coverage.

### Detalle de CodeGuard

> Reporte generado con `--analysis-type full` (obligatorio desde `US-ADJ-15`/PR #168).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 6 |
| PEP8 | 0 | 0 | 5 |
| Complexity | 0 | 0 | 5 |
| DeadCode | 5 | 0 | 0 |
| Maintainability | 0 | 0 | 5 |
| Pylint | 0 | 1 | 4 |
| Spelling | 5 | 0 | 0 |
| Types | 0 | 0 | 5 |
| UnusedImports | 0 | 0 | 5 |

Fuente: `quality/reports/inc6-adj/US-ADJ-08-codeguard.json` →
`quality.codeguard.checks` en `quality/reports/inc6-adj/US-ADJ-08-quality.json`.

**Los 10 "errors"** de DeadCode (5) y Spelling (5) son gaps de entorno (`vulture`/`codespell`
no instalados en el venv), no hallazgos de código — mismo patrón en todos los reportes previos
del proyecto que corrieron `codeguard --analysis-type full`.

**El warning de Pylint** (`schemas.py` 7.19/10 aislado) es un falso positivo conocido y
recurrente: `pylint` real sobre el archivo completo con el config del proyecto da 10.00/10.
`schemas.py` es un archivo compartido de ~30 modelos Pydantic entre varios flujos de
Identidad; el check aislado de `codeguard` no aplica el mismo contexto que `pylint` directo.
Mismo patrón ya visto en `US-1.1.0`, `US-ADJ-26`, `US-ADJ-38`, `US-3.4.4`.

---

## Criterios de Aceptación

- [x] `GET /identidad/invitaciones/{token}` devuelve materia y horario de una invitación
  vigente, sin consumirla
- [x] No expone `docente_id` ni email destinatario
- [x] 404 si el token no corresponde a ninguna invitación
- [x] 422 si la invitación venció o ya fue usada
- [x] `Registro.tsx` muestra el chip "Te vas a unir a {materia} — {horario}" antes del
  formulario
- [x] El formulario no se muestra mientras se verifica el token, ni si resultó inválido

**Estado:** 6/6 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Clean Architecture BC-first: la nueva query (`ObtenerInvitacionUseCase`, en `use_cases/`)
reutiliza el aggregate `Invitacion` (`entities/`) sin invariantes nuevas — `verificar_vigente()`
ya existía como operación de solo lectura (no muta `usada_en`, a diferencia de `aceptar()`).
Se resuelve materia/comisión con los mismos puertos cross-BC (`MateriaPort`,
`ComisionRepositoryPort`) que ya usaba `RegistroController`, sin ensanchar ningún puerto.

Se reutilizó el `InvitacionesController` existente (antes solo con `generar_invitacion`,
comando protegido por `require_docente`) agregándole la query pública `obtener_invitacion` como
segunda dependencia — mismo criterio de "command/query en el mismo controller cuando no hay
riesgo de CBO" ya aplicado en `US-2.2.3`. CBO del controller: 2 dependencias, muy por debajo del
umbral de 10.

### Diagrama de Componentes

```
GET /identidad/invitaciones/{token}  (registro_router.py, público, sin JWT)
        │
        ▼
InvitacionesController.obtener_invitacion(token)
        │
        ▼
ObtenerInvitacionUseCase.execute(token)
        │
        ├─▶ InvitacionRepositoryPort.obtener_por_token(token)  → 404 si None
        ├─▶ Invitacion.verificar_vigente(now)                  → 422 si vencida/usada
        ├─▶ ComisionRepositoryPort.obtener_por_id(comision_id)
        └─▶ MateriaPort.obtener(materia_id)
        │
        ▼
InvitacionPreview(materia, horario)
```

### Flujo de Datos (frontend)

```
Registro.tsx (mount)
  → useEffect: apiFetch(GET /identidad/invitaciones/{token})
      → 200: setPreview({materia, horario}) → muestra chip + formulario
      → 404/422: navigate("/registro/error") → no muestra el formulario
```

---

## Desafíos y Soluciones

- **Colisión de tests por DB compartida**: correr la suite completa de `tests/integration/`
  en background mientras se ejecutaba el escenario BDD en paralelo produjo un
  `ForeignKeyViolationError` transitorio (dos procesos limpiando/poblando la misma base
  Postgres local al mismo tiempo). Resuelto esperando a que terminara el proceso en background
  antes de reintentar — no era una regresión del código, confirmado reproduciendo el escenario
  aislado.
- **Constructor de `InvitacionesController` cambiado**: extender el controller con la segunda
  dependencia rompió 2 tests unitarios existentes (`test_invitaciones_controller.py`) que
  instanciaban el controller con un solo argumento. Corregidos en la misma sesión (Fase 4),
  agregando `ObtenerInvitacionUseCase(...)` a ambas instanciaciones.

---

## Archivos Creados/Modificados

### Producción
- `src/identidad/use_cases/obtener_invitacion.py` (nuevo)
- `src/identidad/interface_adapters/controllers/invitaciones_controller.py` (modificado)
- `src/identidad/frameworks/api/schemas.py` (modificado)
- `src/identidad/frameworks/api/registro_router.py` (modificado)
- `src/identidad/frameworks/dependencies.py` (modificado)
- `frontend/src/pages/identidad/Registro.tsx` (modificado)

### Tests
- `tests/unit/inc1/test_obtener_invitacion_use_case.py` (nuevo)
- `tests/unit/inc1/test_invitaciones_controller.py` (modificado)
- `tests/integration/inc1/test_obtener_invitacion_api_integration.py` (nuevo)
- `tests/features/inc6-adj/US-ADJ-08-invitacion-preview.feature` (nuevo)
- `tests/step_defs/inc6-adj/test_us_adj_08_steps.py` (nuevo)
- `frontend/src/pages/identidad/Registro.test.tsx` (modificado)

### Documentación
- `docs/plans/inc6-adj/US-ADJ-08-context.md`
- `docs/plans/inc6-adj/US-ADJ-08-plan.md`
- `docs/reports/inc6-adj/US-ADJ-08-report.md` (este archivo)
- `quality/reports/inc6-adj/US-ADJ-08-quality.json`
- `quality/reports/inc6-adj/US-ADJ-08-codeguard.json`
- `CHANGELOG.md` (entrada bajo `[Unreleased]`)

---

## Próximos Pasos

- [ ] `US-ADJ-07` (nombre legible de comisión en detalle de cuenta) — siguiente candidata del
  Incremento 6-ADJ
- [ ] Barrido documental de `PLAN-CM.md` §12 (`docs/architecture/`, wireframes vs código,
  matriz, `CLAUDE.md`) para cerrar `Incremento 6-ADJ`
- [ ] PR de esta US, revisión, merge a `develop`, cierre de Issue #448

---

**Reporte generado por Claude Code**
**Fecha:** 2026-09-30
