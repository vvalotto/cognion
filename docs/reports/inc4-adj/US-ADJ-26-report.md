# Reporte de Implementación: US-ADJ-26 - Docente genera el link de invitación de una Comisión

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-26 |
| **Título** | Docente genera el link de invitación de una Comisión |
| **Producto** | cognion |
| **Prioridad** | Alta — última US de la cadena Comisiones/Invitación de la Iteración 1a |
| **Puntos estimados** | 2 |
| **Tiempo real** | 25 min |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

`POST /comisiones/{id}/invitaciones` ya existía desde `US-1.1.1` y ya validaba del lado del
dominio que el Docente estuviera asignado a la Comisión (`DocenteNoAsignadoAComision`,
INV-ID-08), pero ninguna pantalla lo consumía. Se detectaron y resolvieron dos gaps antes de
escribir la spec (decididos con Víctor): (1) `InvitacionResponse` no exponía el `token` — el
endpoint estaba diseñado para enviar el link por email, no para mostrarlo en pantalla, así que
`email_destinatario` pasó a opcional y la respuesta ahora incluye `token`; (2) no había forma
de que un Docente listara sus propias Comisiones — se resolvió reutilizando la navegación
Materias → Comisiones de la materia (`GET /materias/{id}/comisiones`, ya accesible con rol
`docente`) en vez de agregar un endpoint nuevo. Dos pantallas nuevas del lado Docente
(`ComisionesDeMateria.tsx`, `ComisionDetalleDocente.tsx`) completan el flujo: generar el link,
copiarlo, y regenerar uno nuevo. Cierra la cadena Comisiones/Invitación de la Iteración 1a
del Incremento 4-ADJ junto con `US-ADJ-23`/`24`/`25`.

---

## Componentes Implementados

### Código Fuente

- ✅ `src/identidad/frameworks/api/schemas.py` — `GenerarInvitacionRequest.email_destinatario`
  opcional; `InvitacionResponse.token` nuevo
- ✅ `src/identidad/use_cases/generar_invitacion.py` — envío de email condicional a
  `email_destinatario is not None`
- ✅ `src/identidad/interface_adapters/controllers/invitaciones_controller.py` — ajuste de
  tipo (`email_destinatario: str | None`)
- ✅ `src/identidad/frameworks/api/invitaciones_router.py` — `token` agregado a la respuesta
- ✅ `frontend/src/lib/identidad-comisiones-api.ts` — `generarInvitacion(comisionId, docenteId)`
- ✅ `frontend/src/pages/actividad-evaluativa/ComisionesDeMateria.tsx` — listado de Comisiones
  de una materia (Docente)
- ✅ `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx` — generar/copiar
  link, tabla de estudiantes
- ✅ `frontend/src/pages/actividad-evaluativa/Actividades.tsx` — botón "Ver Comisiones"
- ✅ `frontend/src/router.tsx` — 2 rutas nuevas, `RequireRole rol="docente"`

**Total archivos creados/modificados:** 9

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc1/test_generar_invitacion_use_case.py` — +1 test (email omitido)
- ✅ `tests/unit/inc1/test_invitaciones_controller.py` — +1 test (email `None`)
- ✅ `frontend/src/lib/identidad-comisiones-api.test.ts` — +1 test (`generarInvitacion`)
- ✅ `frontend/src/pages/actividad-evaluativa/ComisionesDeMateria.test.tsx` — 3 tests
- ✅ `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.test.tsx` — 5 tests

**Total tests unitarios nuevos:** 11
**Estado:** 404/404 backend, 291/291 frontend pasando (sin regresiones)

#### Tests de Integración
- ✅ `tests/integration/inc1/test_invitaciones_api_integration.py` — +2 tests (token sin
  email, 403 Administrador)

**Estado:** 289/289 pasando (suite completa `tests/integration/`)

#### Escenarios BDD
- ✅ `tests/features/inc4-adj/US-ADJ-26-generar-invitacion.feature` — 6 escenarios
  (`tests/step_defs/inc4-adj/test_us_adj_26_steps.py`)

**Estado:** 6/6 pasando, 199/199 escenarios BDD del proyecto sin regresiones

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (`src/identidad` completo) | 9.57/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx/función, archivos de la US) | 3 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** (mín, archivos de la US) | 60.84 | > 20 | ✅ |
| **Coverage** (`src/identidad` completo) | 99% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (4 archivos modificados) | 10 errores*, 2 warnings | 0 CRITICAL | ✅ |

\* Los 10 "errores" de CodeGuard no son hallazgos de código: `vulture`/`codespell` no
instalados en el entorno (`DeadCode`/`Spelling`) y timeout de mypy sin `--cache-dir`, bug
conocido `vvalotto/software_limpio#70` (`Types`) — el hook mypy dedicado (fuente de verdad
local) corrió limpio. El warning de `Pylint` en CodeGuard (score por archivo aislado,
6.88–7.24/10) es un falso negativo del análisis sin el contexto completo del paquete — pylint
corrido correctamente con `--rcfile=pyproject.toml` da 10.00/10 sobre los 4 archivos y
9.57/10 sobre `src/identidad` completo. Detalle completo en
`quality/reports/inc4-adj/US-ADJ-26-quality.json` → `observaciones`.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 4 |
| PEP8 | 0 | 0 | 4 |
| Complexity | 0 | 0 | 4 |
| DeadCode | 4 | 0 | 0 |
| Maintainability | 0 | 0 | 4 |
| Pylint | 0 | 2 | 2 |
| Spelling | 4 | 0 | 0 |
| Types | 2 | 0 | 2 |
| UnusedImports | 0 | 0 | 4 |

Fuente: `quality/reports/inc4-adj/US-ADJ-26-codeguard.json` →
`quality/reports/inc4-adj/US-ADJ-26-quality.json` (`codeguard.checks`).

---

## Criterios de Aceptación

- [x] Docente asignado genera el link de invitación con éxito
- [x] Generar un link nuevo produce una invitación distinta
- [x] Generar la invitación con `email_destinatario` sigue funcionando (regression)
- [x] Docente no asignado no puede generar la invitación (422)
- [x] Generar invitación de una Comisión inexistente (404)
- [x] Administrador no puede generar invitaciones (403)

**Estado:** 6/6 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Clean Architecture BC-first — sin componentes nuevos de dominio. Se reutilizó
`GenerarInvitacionUseCase`/`Invitacion.crear()` (existentes desde `US-1.1.1`), ampliando
únicamente el contrato de entrada/salida (`schemas.py`) y el comportamiento condicional del
use case (email opcional). El frontend sigue el mismo patrón de pantallas ya usado en
`ComisionDetalle.tsx` (`US-ADJ-25`): fetch en `useEffect` con `AbortController` propio por
montaje, manejo de `ApiError` para el 422.

### Integración con Sistema Existente

- Backend: sin cambios de composition root (`dependencies.py`) — mismo `InvitacionesController`
  y guard `require_docente` ya inyectados.
- Frontend: consume `identidad-comisiones-api.ts` (BC Identidad) desde pantallas del BC
  Actividad Evaluativa — mismo patrón cross-BC ya usado por `DesempenoPorAlumno.tsx`/
  `DesempenoPorTema.tsx` (`US-4.2.2`).

---

## Cambios no Previstos

Ninguno — el plan se ejecutó sin desvíos respecto de la spec aprobada.

---

## Documentación Actualizada

- [x] Docstrings agregados a componentes nuevos y modificados
- [x] CHANGELOG.md actualizado (`[Unreleased]`)
- [x] Plan de implementación completado (`docs/plans/inc4-adj/US-ADJ-26-plan.md`)
- [ ] `docs/architecture/` — no aplica, sin cambio de patrón arquitectónico

---

## Deuda Técnica

Ninguna introducida por esta US. `DeadCode`/`Spelling` de CodeGuard siguen sin poder
verificarse localmente (herramientas no instaladas) — deuda de tooling preexistente, ya
señalada en `CLAUDE.md` para otras US de esta iteración.

---

## Próximos Pasos

- [ ] `US-ADJ-27` — Menú de navegación persistente en `AppLayout` (Iteración 1b)
- [ ] `US-ADJ-31` — Validación E2E consolidada del MVP (Iteración 2), que ejercitará este
  flujo de invitación como parte del alta de Estudiante real de punta a punta

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-07
