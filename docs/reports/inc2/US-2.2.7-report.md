# Reporte de Implementación: US-2.2.7

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.7 - Administrador ve el detalle de una cuenta y resetea/desbloquea (UI)
- **Puntos estimados:** 3
- **Tiempo real:** ~13 min (fases 0-7, ver `docs/plans/inc2/US-2.2.7-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-20

---

## Alcance

Frontend puro, sin cambios de backend — consume `GET /usuarios/{id}` (`US-2.2.3`) y
`POST /usuarios/{id}/resetear-password` (`US-2.2.4`) tal como quedaron. Agrupa tres pantallas
del wireframe (detalle, reseteo, confirmación) en un único flujo de US, mismo criterio que
`US-2.1.11`.

---

## Componentes Implementados

### Frontend
- ✅ **`cuentas-api.ts`** (extendido, `frontend/src/lib/cuentas-api.ts`) — `obtenerCuenta(id)`,
  `resetearPassword(id, passwordNueva)`, mapeo snake_case↔camelCase para
  `CuentaDetalleResponse`
- ✅ **`CuentaDetalle.tsx`** (nuevo, `frontend/src/pages/CuentaDetalle.tsx`) — reemplaza
  `CuentaDetallePlaceholder` de `US-2.2.6`; breadcrumb, alerta destructiva si `bloqueada`,
  datos de la cuenta (email, rol, estado, comisión si aplica, fecha de creación), botón único
  "Resetear contraseña y desbloquear"
- ✅ **`ResetearPassword.tsx`** (nuevo, `frontend/src/pages/ResetearPassword.tsx`) —
  formulario con validación de cliente (≥8 caracteres, coincidencia contraseña/confirmación),
  aviso de que la acción también desbloquea, "Resetear contraseña"/"Cancelar"
- ✅ **`CuentaReseteada.tsx`** (nuevo, `frontend/src/pages/CuentaReseteada.tsx`) —
  confirmación de éxito, "Volver al listado de cuentas"
- ✅ **`router.tsx`** — rutas `/cuentas/:usuarioId/resetear-password` y
  `/cuentas/:usuarioId/reseteada` nuevas, `/cuentas/:usuarioId` reemplaza el placeholder;
  las tres protegidas con `RequireRole rol="administrador"`
- ✅ **`_placeholders.tsx`** (reducido) — `CuentaDetallePlaceholder` eliminado, sin otros usos

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `CuentaDetalle.tsx` (statements/branches/lines) | 94.11% / 84.61% / 100% | ≥ 80% | ✅ |
| Coverage `ResetearPassword.tsx` (statements/branches/lines) | 93.54% / 78.57% / 100% | ≥ 80% | ✅ |
| Coverage `CuentaReseteada.tsx` (statements) | 100% | ≥ 80% | ✅ |
| Coverage `cuentas-api.ts` (statements) | 100% | ≥ 80% | ✅ |

Fuente: `quality/reports/inc2/US-2.2.7-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios/Integración (16 tests nuevos, Vitest)**
- `cuentas-api.test.ts` (+4 tests) — `obtenerCuenta` hace GET y mapea snake_case→camelCase
  (con y sin `comision_id`), `resetearPassword` hace POST con el body correcto
- `CuentaDetalle.test.tsx` (3 tests) — cuenta activa sin alerta, cuenta bloqueada con alerta,
  navegación al formulario de reseteo
- `ResetearPassword.test.tsx` (4 tests) — reseteo exitoso navega a confirmación, rechaza
  contraseña corta sin llamar al backend, rechaza confirmación que no coincide sin llamar al
  backend, cancelar vuelve al detalle sin cambios
- `CuentaReseteada.test.tsx` (3 tests) — muestra nombre por `location.state`, fallback
  genérico sin state, "Volver al listado" navega a `/cuentas`
- `router.test.tsx` (actualizado + 2 tests nuevos) — `/cuentas/:usuarioId` renderiza el
  detalle real (reemplaza la aserción del placeholder de `US-2.2.6`),
  `/cuentas/:usuarioId/resetear-password` y `/cuentas/:usuarioId/reseteada` con sesión de
  administrador

**BDD (3 escenarios frontend)**
- `tests/features/inc2/US-2.2.7-detalle-cuenta-reseteo.feature` — validados por mapeo directo
  a los tests de Vitest de arriba (sin step_defs/pytest-bdd, misma adaptación de `US-2.2.6`)

**Todos los tests pasando:** ✅ 134/134 frontend (suite completa)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/lib/cuentas-api.ts` (extendido)
- `frontend/src/pages/CuentaDetalle.tsx` (nuevo)
- `frontend/src/pages/ResetearPassword.tsx` (nuevo)
- `frontend/src/pages/CuentaReseteada.tsx` (nuevo)
- `frontend/src/pages/_placeholders.tsx` (reducido)
- `frontend/src/router.tsx` (modificado)

### Tests
- `tests/features/inc2/US-2.2.7-detalle-cuenta-reseteo.feature` (nuevo)
- `frontend/src/lib/cuentas-api.test.ts` (extendido)
- `frontend/src/pages/CuentaDetalle.test.tsx` (nuevo)
- `frontend/src/pages/ResetearPassword.test.tsx` (nuevo)
- `frontend/src/pages/CuentaReseteada.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.2.7.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc2/US-2.2.7-context.md`
- `docs/plans/inc2/US-2.2.7-plan.md`
- `docs/reports/inc2/US-2.2.7-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.7-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Ver el detalle de una cuenta bloqueada — muestra una alerta indicando el bloqueo
- [x] Resetear contraseña exitosamente — ejecuta el reseteo, navega a confirmación, la cuenta
  deja de aparecer bloqueada
- [x] Cancelar el reseteo — vuelve al detalle sin ejecutar ningún cambio

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.8` — Cualquier usuario cambia su propia contraseña (UI, Issue #103)
- [ ] `US-2.2.9` — Login refleja el estado de cuenta bloqueada (UI, Issue #104) — cierra la
  Iteración 2 completa

---

## Lecciones Aprendidas

- ✅ Agrupar tres pantallas (detalle, formulario de reseteo, confirmación) en una sola US,
  mismo criterio que `US-2.1.11`, mantuvo el flujo completo revisable de punta a punta sin
  fragmentar el review.
- 💡 `ResetearPassword.tsx` resuelve el nombre de la cuenta con su propio `obtenerCuenta()` en
  vez de recibirlo por `location.state` desde `CuentaDetalle` — permite entrar directo a
  `/cuentas/:id/resetear-password` (deep link, recarga de página) sin perder el nombre para la
  pantalla de confirmación.
- ⚠️ El test de integración preexistente `router.test.tsx` para `/cuentas/:usuarioId` verificaba
  el placeholder de `US-2.2.6` con el fetch mock genérico (`[]`); al reemplazar la pantalla real
  hubo que actualizarlo con un mock de `CuentaDetalleResponse` completo — un recordatorio de que
  los tests de integración de rutas quedan acoplados al contrato de datos de la pantalla que
  navegan, no solo a la ruta.
- ⚠️ Se confirmó el mismo test flaky preexistente detectado en `US-2.2.6`
  (`NuevaPreguntaOpcionMultiple.test.tsx`, timeout bajo carga con la suite completa + coverage,
  pasa en aislamiento) — no relacionado con esta US, no se corrigió (fuera de alcance).

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-20
