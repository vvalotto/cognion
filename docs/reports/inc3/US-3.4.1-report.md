# Reporte de Implementación: US-3.4.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.4.1 - Infraestructura de frontend de Actividad Evaluativa
- **Puntos estimados:** 3
- **Tiempo real:** ~9.2 min (fases 0-8, ver `docs/plans/inc3/US-3.4.1-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-30

---

## Componentes Implementados

### Cliente API del dominio
- ✅ **`actividad-evaluativa-api.ts`** (nuevo, `frontend/src/lib/actividad-evaluativa-api.ts`)
  - Reutiliza `apiFetch`/`ApiError` (`api-client.ts`, `US-1.1.6`) — sin duplicar el manejo de
    JWT/401/403
  - 9 funciones tipadas: `crearActividad`, `modificarPeriodoDisponibilidad`, `cerrarActividad`,
    `iniciarEvaluacion`, `registrarRespuesta`, `suspenderEvaluacion`, `reanudarEvaluacion`,
    `finalizarEvaluacion`, `obtenerRevision`
  - Mapeo explícito snake_case (schemas Pydantic del backend) ↔ camelCase (convención TS del
    frontend) — mismo criterio que `banco-preguntas-api.ts` (`US-2.1.8`), sin acoplar el
    frontend a los nombres de `src/actividad_evaluativa/frameworks/api/schemas.py`

### Placeholder de pantalla
- ✅ **`ActividadEvaluativaPlaceholder`** (`frontend/src/pages/_placeholders.tsx`) — destino
  temporal de todas las rutas nuevas hasta que `US-3.4.2` a `US-3.4.7` las reemplacen (mismo
  criterio que `BancoPreguntasPlaceholder`, `US-2.1.8`)

### Routing
- ✅ **10 rutas nuevas** (`frontend/src/router.tsx`):
  - 6 bajo `/actividad-evaluativa/*`, `RequireRole rol="docente"`:
    `/actividad-evaluativa/materias`, `.../materias/:materiaId/actividades`,
    `.../materias/:materiaId/actividades/nueva`, `.../actividades/:actividadId`,
    `.../actividades/:actividadId/extender-plazo`, `.../actividades/:actividadId/cerrar`
  - 4 bajo `/mis-actividades/*`, `RequireRole rol="estudiante"` (**primer uso de ese rol** en
    `RequireRole` — hasta ahora solo se había usado con `administrador`/`docente`):
    `/mis-actividades/materias`, `.../materias/:materiaId/actividades`,
    `.../actividades/:actividadId/rendir`, `.../evaluaciones/:evaluacionId/revision`

---

## Sin gap de backend

A diferencia de `US-2.1.8` (que excluyó `listarMaterias` por falta de `GET /materias`), esta US
no encontró gaps: los 9 endpoints consumidos por `US-3.4.2` a `US-3.4.7` ya existían tal cual en
`actividades_router.py`/`evaluaciones_router.py`/`revision_router.py` (Iteraciones 1-3 del
Incremento 3), verificado leyendo los routers directamente antes de escribir el cliente API. El
gap de backend real de la Iteración 4 (falta de `GET` de listado/detalle de actividades) queda
fuera del alcance de esta US — cada US de pantalla que lo necesite lo resuelve en su propio
alcance, ya documentado en `inc3-candidatas.md` desde el 2026-08-28.

---

## Métricas de Calidad

| Métrica | Valor | Umbral (referencia) | Estado |
|---------|-------|----------------------|--------|
| oxlint | 0 errores (3 warnings preexistentes) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 178/178 passed | 100% pasan | ✅ |
| Coverage `actividad-evaluativa-api.ts` | 100% stmts/lines | ≥80% | ✅ |
| Coverage global frontend | 92.37% stmts, 94.01% lines, 84.41% branches | — | ✅ |

Fuente: `quality/reports/inc3/US-3.4.1-quality.json`. Stack frontend — no aplican pylint/CC/MI
(gates Python), adaptación documentada en `docs/plans/inc3/US-3.4.1-context.md` (mismo criterio
que `US-2.1.8`/`US-1.1.6`/`US-1.1.9`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (9 tests nuevos)
- `actividad-evaluativa-api.test.ts` — las 9 funciones del cliente, verificando método HTTP,
  URL, body enviado (mapeado a snake_case) y mapeo de la respuesta a camelCase

### Tests de Integración (4 tests nuevos)
- `router.test.tsx` (describe `"router (integración)"`) — 2 rutas representativas de cada
  bloque (docente/estudiante): "Acceso denegado" con rol distinto del requerido, render del
  placeholder con el rol correcto

### Escenarios BDD (3 escenarios)
- `tests/features/inc3/US-3.4.1-infra-frontend-actividad-evaluativa.feature`
  - Ruta de docente protegida por rol
  - Ruta de estudiante protegida por rol
  - Cliente API disponible
- Validados contra los tests Vitest existentes (sin step_defs — mismo criterio frontend que
  `US-2.1.8`/`US-1.1.6`/`US-1.1.9`)

**Todos los tests pasando:** ✅ 178/178 (suite completa del frontend, sin regresiones)

---

## Archivos Creados/Modificados

### Código de producción
- `frontend/src/lib/actividad-evaluativa-api.ts` (nuevo)
- `frontend/src/pages/_placeholders.tsx` (modificado — `ActividadEvaluativaPlaceholder`)
- `frontend/src/router.tsx` (modificado — 10 rutas nuevas)

### Tests
- `tests/features/inc3/US-3.4.1-infra-frontend-actividad-evaluativa.feature` (nuevo)
- `frontend/src/lib/actividad-evaluativa-api.test.ts` (nuevo)
- `frontend/src/router.test.tsx` (modificado — 4 tests nuevos)

### Documentación
- `docs/plans/inc3/US-3.4.1-context.md`
- `docs/plans/inc3/US-3.4.1-plan.md`
- `docs/reports/inc3/US-3.4.1-report.md` (este archivo)
- `quality/reports/inc3/US-3.4.1-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Rutas del BC registradas en `router.tsx`: `RequireRole rol="docente"` para
      `/actividad-evaluativa/*`, `RequireRole rol="estudiante"` para `/mis-actividades/*`
- [x] `actividad-evaluativa-api.ts` expone funciones tipadas para cada endpoint consumido por
      `US-3.4.2` a `US-3.4.7` — sin exclusiones, los 9 ya existían
- [x] Reutiliza el manejo de JWT/401/403 de `api-client.ts`, sin duplicarlo
- [x] Sin pantallas visibles todavía — placeholder hasta que las US siguientes las reemplacen

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #170 con los SHAs de los commits de esta US
- [ ] Continuar con `US-3.4.2` (Docente ve sus materias y el listado de actividades de una
      materia) — primera pantalla real, lado docente
- [ ] Lado estudiante (`US-3.4.5`→`3.4.6`→`3.4.7`) puede avanzar en paralelo, ambos solo
      dependen de esta US

---

## Lecciones Aprendidas

- ✅ Verificar los routers backend directamente en Fase 2 (en vez de confiar en la tabla de
  candidatas) confirmó que no había gap de backend en esta US — a diferencia de `US-2.1.8`,
  donde el gap se detectó recién ahí. La misma disciplina de verificación puede ahorrar sorpresas
  en `US-3.4.2`/`US-3.4.4`/`US-3.4.5`, donde `inc3-candidatas.md` sí anticipa gaps.
- ✅ Mapear explícitamente snake_case↔camelCase en el cliente API mantiene el frontend con
  convenciones TS idiomáticas sin acoplarse a los nombres de los schemas Pydantic del backend.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-30
