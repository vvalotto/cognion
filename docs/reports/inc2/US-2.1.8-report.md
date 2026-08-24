# Reporte de Implementación: US-2.1.8

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.8 - Infraestructura de frontend del Banco de Preguntas
- **Puntos estimados:** 3
- **Tiempo real:** ~14 min (fases 0-8, ver `docs/plans/inc2/US-2.1.8-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-14

---

## Componentes Implementados

### Cliente API del dominio
- ✅ **`banco-preguntas-api.ts`** (nuevo, `frontend/src/lib/banco-preguntas-api.ts`)
  - Reutiliza `apiFetch`/`ApiError` (`api-client.ts`, `US-1.1.6`) — sin duplicar el manejo de
    JWT/401/403
  - 6 funciones tipadas: `crearMateria`, `filtrarBanco`, `cargarPreguntaOpcionMultiple`,
    `cargarPreguntaVerdaderoFalso`, `editarPregunta`, `eliminarPregunta`
  - Mapeo explícito snake_case (schemas Pydantic del backend) ↔ camelCase (convención TS del
    frontend) — decisión de diseño para no acoplar el frontend a los nombres de los schemas
    de `src/banco_preguntas/frameworks/api/schemas.py`

### Placeholder de pantalla
- ✅ **`BancoPreguntasPlaceholder`** (`frontend/src/pages/_placeholders.tsx`) — destino
  temporal de todas las rutas nuevas hasta que `US-2.1.9` a `US-2.1.13` las reemplacen (mismo
  criterio que `InicioPlaceholder`, `US-1.1.6`)

### Routing
- ✅ **7 rutas nuevas** (`frontend/src/router.tsx`), todas protegidas con
  `RequireRole rol="docente"` (mismo guard que `US-1.1.9`):
  - `/materias`, `/materias/nueva`
  - `/materias/:materiaId/banco`
  - `/materias/:materiaId/banco/preguntas/nueva`
  - `/materias/:materiaId/banco/preguntas/nueva/opcion-multiple`
  - `/materias/:materiaId/banco/preguntas/nueva/verdadero-falso`
  - `/materias/:materiaId/banco/preguntas/:preguntaId/editar`

---

## Gap detectado (ajuste de alcance)

El backend no expone `GET /materias` (listado) — solo `POST /materias` (`US-2.1.1`). La spec
de `US-2.1.9` asumía que ya existía. Detectado en Fase 2 (planificación), antes de escribir
código. Decisión de Víctor: **excluir `listarMaterias` del alcance de esta US**.
`US-2.1.9` queda bloqueada hasta que ese endpoint backend se implemente.

---

## Métricas de Calidad

| Métrica | Valor | Umbral (referencia) | Estado |
|---------|-------|----------------------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 65/65 passed | 100% pasan | ✅ |
| Coverage `banco-preguntas-api.ts` | 100% stmts/lines, 94.28% branches | ≥80% | ✅ |
| Coverage global frontend | 94.7% stmts, 91.25% branches | — | ✅ |

Fuente: `quality/reports/inc2/US-2.1.8-quality.json`. Stack frontend — no aplican pylint/CC/MI
(gates Python), adaptación documentada en `docs/plans/inc2/US-2.1.8-context.md` (mismo
criterio que `US-1.1.6`/`US-1.1.9`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (12 tests nuevos)
- `banco-preguntas-api.test.ts` — las 6 funciones del cliente, incluyendo mapeo
  snake_case↔camelCase, construcción de query string de `filtrarBanco` (con y sin filtros,
  cada filtro individual), y el branch de `opciones` en `editarPregunta`

### Tests de Integración (7 tests nuevos)
- `router.test.tsx` (describe `"router (integración)"`) — las 7 rutas nuevas: redirección a
  `/login` sin sesión, "Acceso denegado" con rol distinto de `docente`, render del placeholder
  con sesión de `docente` en cada una de las 7 rutas

### Escenarios BDD (2 escenarios)
- `tests/features/inc2/US-2.1.8-infra-frontend-banco.feature`
  - Ruta protegida por rol
  - Cliente API disponible
- Validados contra los tests Vitest existentes (sin step_defs — mismo criterio frontend que
  `US-1.1.6`/`US-1.1.9`)

**Todos los tests pasando:** ✅ 65/65 (suite completa del frontend)

---

## Archivos Creados/Modificados

### Código de producción
- `frontend/src/lib/banco-preguntas-api.ts` (nuevo)
- `frontend/src/pages/_placeholders.tsx` (modificado — `BancoPreguntasPlaceholder`)
- `frontend/src/router.tsx` (modificado — 7 rutas nuevas)

### Tests
- `tests/features/inc2/US-2.1.8-infra-frontend-banco.feature` (nuevo)
- `frontend/src/lib/banco-preguntas-api.test.ts` (nuevo)
- `frontend/src/router.test.tsx` (modificado — 7 tests nuevos)

### Documentación
- `docs/plans/inc2/US-2.1.8-context.md`
- `docs/plans/inc2/US-2.1.8-plan.md`
- `docs/reports/inc2/US-2.1.8-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.8-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Rutas del BC registradas en `router.tsx`, protegidas con `RequireRole(rol="docente")`
- [x] `banco-preguntas-api.ts` expone funciones tipadas para cada endpoint de la Iteración 1
      backend que existe (excepto `listarMaterias` — gap de backend documentado arriba)
- [x] Reutiliza el manejo de JWT/401/403 de `api-client.ts`, sin duplicarlo
- [x] Sin pantallas visibles todavía — placeholder hasta que las US siguientes las reemplacen

**Todos los criterios cumplidos (con el ajuste de alcance documentado):** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #49 con los SHAs de los commits de esta US
- [ ] Resolver el gap de `GET /materias` (backend) antes de poder implementar `US-2.1.9`
      completa
- [ ] `US-2.1.10` a `US-2.1.13` no dependen del gap — pueden avanzar en cuanto tengan al menos
      una materia/banco de prueba

---

## Lecciones Aprendidas

- ✅ Detectar en Fase 2 (planificación) que `GET /materias` no existe evitó descubrir el gap
  recién al implementar `US-2.1.9` — el checkpoint de plan sirvió para lo que está pensado.
- ✅ Mapear explícitamente snake_case↔camelCase en el cliente API mantiene el frontend con
  convenciones TS idiomáticas sin acoplarse a los nombres de los schemas Pydantic del backend.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-14
