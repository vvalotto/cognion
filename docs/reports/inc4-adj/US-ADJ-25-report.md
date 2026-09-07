# Reporte de Implementación: US-ADJ-25 - Administrador asigna un Docente a una Comisión

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-25 |
| **Título** | Administrador asigna un Docente a una Comisión |
| **Producto** | cognion |
| **Prioridad** | Alta — precondición de `US-ADJ-26` (generar invitación) |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | 23 min (Fases 0-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Tercera US de la Iteración 1a del Incremento 4-ADJ: el Administrador ahora puede ver el
detalle de una Comisión puntual y asignarle un Docente, precondición de `US-ADJ-26` (generar
invitación — una Comisión sin Docente no sirve para eso). `POST /comisiones/{id}/docentes` y
`GET /usuarios?rol=docente` ya existían sin cambios desde el Incremento 1/2. Único componente
de backend nuevo: `GET /comisiones/{comision_id}`, que no existía — necesario porque la
pantalla de detalle se navega directamente (sin conocer de antemano la `materia_id` de la
Comisión) y el listado por Materia (`US-ADJ-23`) no sirve para resolver una Comisión puntual.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/interface_adapters/controllers/comisiones_query_controller.py` —
  `obtener_comision(comision_id)` nuevo: pass-through sobre
  `ComisionRepositoryPort.obtener_por_id()` (ya inyectado), sin Use Case dedicado, mismo
  criterio que el resto del controller de consultas.
- ✅ `src/identidad/frameworks/api/comisiones_router.py` — `GET /comisiones/{comision_id}`
  nuevo, guard `require_docente_o_administrador` (ya existente, reutilizable por `US-ADJ-26`).

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/identidad-comisiones-api.ts` — `obtenerComision()`, `asignarDocente()`
  nuevos.
- ✅ `frontend/src/pages/identidad/ComisionDetalle.tsx` (nuevo) — pantalla de detalle:
  breadcrumb, alerta si no hay Docente asignado, select + botón "Asignar", tabla de
  Estudiantes inscriptos.
- ✅ `frontend/src/pages/_placeholders.tsx` — `ComisionPlaceholder` eliminado (sin más
  consumidores tras esta US).
- ✅ `frontend/src/router.tsx` — `/comisiones/:comisionId` usa `ComisionDetalle`.

**Total archivos:** 6 (2 backend, 4 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc4/test_comisiones_query_controller.py` — `TestObtenerComision`, 2 tests
  nuevos (existente, inexistente).

#### Tests de Integración
- ✅ `tests/integration/inc4/test_comisiones_query_router.py` — `TestObtenerComision`, 5 tests
  nuevos (sin docente, con docente, 404, regresión Docente, 403 Estudiante).

**Total tests backend nuevos:** 7 · **Estado:** 882/882 backend pasando (suite completa,
sin regresiones — confirmado en corrida limpia sin procesos concurrentes contra la misma DB)

#### Escenarios BDD
- ✅ `tests/features/inc4-adj/US-ADJ-25-asignar-docente-comision.feature` — 8 escenarios
- ✅ `tests/step_defs/inc4-adj/test_us_adj_25_steps.py`

**Estado:** 8/8 pasando

#### Tests Frontend
- ✅ `frontend/src/pages/identidad/ComisionDetalle.test.tsx` (nuevo) — 6 tests
- ✅ `frontend/src/lib/identidad-comisiones-api.test.ts` — +3 tests (`obtenerComision` ×2,
  `asignarDocente` ×1)

**Total tests frontend nuevos:** 9 · **Estado:** 282/282 frontend pasando

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (`comisiones_query_controller.py`) | 10.00/10 | ≥ 8.0 | ✅ |
| **Pylint** (`comisiones_router.py`) | 8.57/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx) | 3 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** (mín) | 83.8 | > 20 | ✅ |
| **Coverage** (`comisiones_query_controller.py`) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **oxlint** (frontend) | 0 errores (5 warnings preexistentes) | 0 errores | ✅ |
| **tsc -b** (frontend) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (2 archivos backend) | 7 errors\*, 0 warnings, 11 infos | 0 CRITICAL | ✅ |

\* Los 7 "errors" son timeouts de bandit/mypy dentro de CodeGuard (10s, sin `--cache-dir`) y
herramientas no instaladas (`vulture`, `codespell`) — mismo patrón ya documentado en
`CLAUDE.md` (`software_limpio#70`). pylint directo y mypy directo (fuente de verdad local del
proyecto) están limpios sobre el mismo código.

Fuente: `quality/reports/inc4-adj/US-ADJ-25-quality.json`,
`quality/reports/inc4-adj/US-ADJ-25-codeguard.json`.

---

## Criterios de Aceptación

- [x] En el detalle de una Comisión, select con los usuarios de rol `docente` + botón
      "Asignar"
- [x] Si la Comisión no tiene ningún Docente asignado, alerta informativa
- [x] Después de asignar, el Docente aparece listado en el detalle sin recargar la página

**Estado:** 3/3 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Clean Architecture BC-first. El único componente de backend nuevo (`obtener_comision`) vive
en `interface_adapters/controllers` como pass-through sobre un puerto ya inyectado
(`ComisionRepositoryPort`), sin agregar una capa de Use Case para una lectura simple — mismo
criterio ya aplicado en el resto de `ComisionesQueryController` (`listar_estudiantes`). El
frontend sigue el patrón ya establecido por `Comisiones.tsx`/`NuevaComision.tsx`: cliente API
tipado + pantalla que resuelve nombres de Docente vía `listarCuentas({ rol: "docente" })`.

### Flujo de Datos

```
Administrador (browser)
  → GET /comisiones/{id} (identidad, nuevo — ComisionesQueryController.obtener_comision)
  → GET /usuarios?rol=docente (identidad, US-2.2.2, sin cambios) — resuelve nombres
  → GET /comisiones/{id}/estudiantes (identidad, US-4.2.2/US-ADJ-23, sin cambios)
  → [Asignar] POST /comisiones/{id}/docentes (identidad, US-1.1.1, sin cambios)
      → actualiza el estado local con la respuesta, sin recargar la página
```

---

## Cambios no Previstos

- **Gap de backend detectado en Fase 0** (antes de escribir la spec, no en QA): no existía
  `GET /comisiones/{comision_id}`. Se agregó a la spec desde el inicio (no fue un descubrimiento
  tardío) porque la navegación a `/comisiones/:comisionId` no pasa por ningún listado de
  Materia que ya resuelva ese dato — a diferencia de `Comisiones.tsx`, que sí conoce la
  `materia_id` de antemano. Resuelto sin Use Case dedicado, reutilizando el puerto ya
  inyectado en el controller.
- **`ComisionPlaceholder` eliminado**: tras esta US ningún placeholder de `_placeholders.tsx`
  lo consume (`US-ADJ-24` ya había reemplazado `/comisiones/nueva`) — se eliminó en vez de
  dejarlo huérfano.

---

## Testing Manual Realizado

No se hizo un recorrido dedicado en navegador real contra backend real para esta US
específica — se verificó con la suite automatizada completa (backend + frontend) y BDD. El
recorrido en navegador real queda cubierto por la Validación E2E consolidada de `US-ADJ-31`
(Iteración 2 del incremento), que ejercita el flujo completo Administrador → crear Comisión →
asignar Docente → invitación → registro de Estudiante en una sola corrida.

---

## Deuda Técnica

- Ninguna introducida por esta US. La deuda de cobertura de branches del frontend detectada en
  `US-ADJ-24` (`task_ec36dcbe`) sigue abierta, fuera del alcance de esta US.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-26` — Docente genera el link de invitación de una Comisión (siguiente en orden,
      ahora desbloqueada: ya existe al menos el mecanismo para que una Comisión tenga un
      Docente asignado)

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
