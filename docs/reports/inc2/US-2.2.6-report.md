# Reporte de Implementación: US-2.2.6

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.6 - Administrador ve y filtra el listado de cuentas (UI)
- **Puntos estimados:** 3
- **Tiempo real:** ~22 min (fases 0-7, ver `docs/plans/inc2/US-2.2.6-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-20

---

## Alcance

Frontend puro, sin cambios de backend — consume `GET /usuarios?rol=&estado=&busqueda=` tal
como quedó en `US-2.2.2`.

---

## Componentes Implementados

### Frontend
- ✅ **`cuentas-api.ts`** (nuevo, `frontend/src/lib/cuentas-api.ts`) — `listarCuentas(filtros)`,
  reutiliza el tipo `Rol` ya existente en `@/lib/session.ts` en vez de duplicarlo
- ✅ **`Cuentas.tsx`** (nuevo, `frontend/src/pages/Cuentas.tsx`) — tabla + filtros de rol/
  estado/búsqueda (`<select>` nativo + texto libre), refresca al cambiar cualquier filtro
  (mismo patrón `Banco.tsx`), fila navega a `/cuentas/{id}`, "+ Nueva cuenta" enlaza el alta
  de Docente ya existente (`US-1.1.9`, sin pantalla ni endpoint nuevo)
- ✅ **`CuentaDetallePlaceholder`** (`frontend/src/pages/_placeholders.tsx`, extendido) —
  placeholder de `/cuentas/:usuarioId` hasta que `US-2.2.7` lo reemplace
- ✅ **`router.tsx`** — rutas `/cuentas` y `/cuentas/:usuarioId` nuevas, protegidas con
  `RequireRole rol="administrador"`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `Cuentas.tsx` (statements/branches/functions) | 96% / 92.85% / 91.66% | ≥ 80% | ✅ |
| Coverage `cuentas-api.ts` (statements) | 100% | ≥ 80% | ✅ |

Fuente: `quality/reports/inc2/US-2.2.6-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios/Integración (13 tests nuevos, Vitest)**
- `cuentas-api.test.ts` (4 tests) — GET sin query string sin filtros, arma el query string
  solo con filtros presentes, omite los no provistos, devuelve la lista tal cual la envía el
  backend
- `Cuentas.test.tsx` (6 tests) — listado sin filtros, filtrar por rol+estado combinados,
  filtro sin resultados sin mensaje de error, "Limpiar filtros", navegación al detalle,
  navegación a "+ Nueva cuenta"
- `router.test.tsx` (3 tests nuevos) — `/cuentas` acceso denegado con rol distinto de
  administrador, `/cuentas` renderiza el listado real con sesión de administrador,
  `/cuentas/:usuarioId` renderiza el placeholder

**BDD (2 escenarios frontend)**
- `tests/features/inc2/US-2.2.6-listado-filtro-cuentas.feature` — validados por mapeo directo
  a los tests de Vitest de arriba (sin step_defs/pytest-bdd, misma adaptación de `US-2.1.9`/
  `US-2.1.10`)

**Todos los tests pasando:** ✅ 119/119 frontend (suite completa)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/lib/cuentas-api.ts` (nuevo)
- `frontend/src/pages/Cuentas.tsx` (nuevo)
- `frontend/src/pages/_placeholders.tsx` (extendido)
- `frontend/src/router.tsx` (modificado)

### Tests
- `tests/features/inc2/US-2.2.6-listado-filtro-cuentas.feature` (nuevo)
- `frontend/src/lib/cuentas-api.test.ts` (nuevo)
- `frontend/src/pages/Cuentas.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.2.6.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc2/US-2.2.6-context.md`
- `docs/plans/inc2/US-2.2.6-plan.md`
- `docs/reports/inc2/US-2.2.6-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.6-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Filtrar por rol y estado — la tabla muestra solo las cuentas que matchean ambos filtros
- [x] Navegar al detalle — hacer clic en una fila navega a `/cuentas/{id}`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.7` — Administrador ve el detalle de una cuenta y resetea/desbloquea (reemplaza
  `CuentaDetallePlaceholder`, Issue #102)
- [ ] `US-2.2.8` — Cualquier usuario cambia su propia contraseña (UI, Issue #103)
- [ ] `US-2.2.9` — Login refleja el estado de cuenta bloqueada (UI, Issue #104)

---

## Lecciones Aprendidas

- ✅ Reutilizar el tipo `Rol` de `@/lib/session.ts` en vez de redefinirlo en `cuentas-api.ts`
  evitó una duplicación silenciosa — el mismo tipo ya circulaba por `RequireRole` y `Login.tsx`.
- 💡 Para US frontend puras que consumen un endpoint ya filtrable, un único `useEffect` que
  reacciona a los tres filtros (mismo patrón `Banco.tsx`) es suficiente sin debounce — el
  volumen de datos de este BC (decenas de cuentas) no lo justifica.
- ⚠️ Al testear un flujo con dos `selectOptions` seguidos (cada uno dispara su propio fetch por
  el `useEffect`), hay que mockear una respuesta de fetch por cada disparo intermedio, no solo
  la final — un mock faltante produce un `Unhandled Rejection` silencioso que Vitest reporta
  aparte de los resultados de test.
- ⚠️ Se detectó un test flaky preexistente (`NuevaPreguntaOpcionMultiple.test.tsx`, timeout
  bajo carga con la suite completa, pasa en aislamiento) — no relacionado con esta US, no se
  corrigió (fuera de alcance).

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-20
