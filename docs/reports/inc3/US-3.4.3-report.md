# Reporte de Implementación: US-3.4.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.4.3 - Docente crea una nueva actividad de período abierto
- **Puntos estimados:** 3
- **Tiempo real:** ~10 min (fases 0-9, tracker `US-3.4.3-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-30

---

## Componentes Implementados

### Pantalla nueva
- ✅ **`NuevaActividad.tsx`** (nuevo, `frontend/src/pages/NuevaActividad.tsx`)
  - Resuelve la materia vía `listarMaterias()` + `find` (mismo patrón que `Actividades.tsx`/
    `NuevaPreguntaOpcionMultiple.tsx`)
  - Formulario con 4 campos: apertura, cierre (`datetime-local`), cantidad de preguntas,
    intentos permitidos (`number`) — sin campo de título, fiel al prototipo
    `#doc-nueva-actividad` (la materia es implícita por la navegación)
  - Hint dinámico con `materia.cantidadPreguntasActivas` (dato ya expuesto por
    `listarMaterias()` desde `US-2.1.9` — sin endpoint nuevo)
  - Validación de cliente: `fechaApertura < fechaCierre` (INV-AE-02) e intentos ≥ 1
    (INV-AE-03) antes de llamar al backend
  - `crearActividad()` (`actividad-evaluativa-api.ts`, `US-3.4.1`) — sin cambios en el cliente
  - Errores 422 (`PreguntasInsuficientes`, `PeriodoInvalido`, `CantidadIntentosInvalida`)
    mostrados inline con `err.message`

### Routing
- ✅ **`router.tsx`** — reemplaza `<ActividadEvaluativaPlaceholder />` por `<NuevaActividad />`
  en la ruta ya cableada `/actividad-evaluativa/materias/:materiaId/actividades/nueva`
  (`RequireRole rol="docente"`, `US-3.4.1`). Sin rutas nuevas.

---

## Sin cambios de backend

`POST /actividades` existe desde `US-3.1.2` sin modificaciones — esta US es frontend puro,
confirmado leyendo `actividades_router.py`/`schemas.py` en Fase 2 antes de escribir el plan.

---

## Métricas de Calidad

| Métrica | Valor | Umbral (referencia) | Estado |
|---------|-------|----------------------|--------|
| oxlint | 0 errores (3 warnings preexistentes) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 188/188 passed | 100% pasan | ✅ |
| Coverage `NuevaActividad.tsx` | 90.24% stmts, 92.1% lines, 76.19% branches | ≥80% | ✅ |
| Coverage global frontend | 91.51% stmts, 93.17% lines, 81.61% branches | ≥80% | ✅ |

Fuente: `quality/reports/inc3/US-3.4.3-quality.json`. Stack frontend — no aplican pylint/CC/MI
(gates Python), mismo criterio que `US-3.4.1`/`US-3.4.2`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (5 tests nuevos)
- `NuevaActividad.test.tsx`:
  - Creación exitosa: envío correcto, navegación al listado
  - Rechazo de cliente por período inválido: sin llamada al backend
  - Rechazo del servidor (422 `PreguntasInsuficientes`): error inline
  - Hint de preguntas activas del banco
  - Cancelar vuelve al listado sin llamar al backend

### Tests de Integración
- Ninguno nuevo — la ruta ya estaba protegida y testeada desde `US-3.4.1`
  (`router.test.tsx`), y el render real de la pantalla lo cubre `NuevaActividad.test.tsx`.

### Escenarios BDD (3 escenarios)
- `tests/features/inc3/US-3.4.3-nueva-actividad.feature`
  - Creación exitosa
  - Rechazo de cliente por período inválido
  - Rechazo del servidor por preguntas insuficientes
- Validados 1:1 contra los tests Vitest de `NuevaActividad.test.tsx` (sin step_defs — mismo
  criterio frontend que `US-3.4.1`/`US-3.4.2`)

**Todos los tests pasando:** ✅ 188/188 (suite completa del frontend, sin regresiones)

---

## Archivos Creados/Modificados

### Código de producción
- `frontend/src/pages/NuevaActividad.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado — reemplazo de placeholder)

### Tests
- `tests/features/inc3/US-3.4.3-nueva-actividad.feature` (nuevo)
- `frontend/src/pages/NuevaActividad.test.tsx` (nuevo, 5 tests)

### Documentación
- `docs/plans/US-3.4.3-context.md`
- `docs/plans/inc3/US-3.4.3-plan.md`
- `docs/reports/inc3/US-3.4.3-report.md` (este archivo)
- `quality/reports/inc3/US-3.4.3-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Creación exitosa: crea la actividad y vuelve al listado, mostrando la nueva
- [x] Validación de cliente (`fecha_apertura < fecha_cierre`, intentos ≥ 1) antes de enviar
- [x] Rechazo del servidor (`PreguntasInsuficientes`, `PeriodoInvalido`,
      `CantidadIntentosInvalida`) mostrado inline
- [x] `cantidad_preguntas` no se valida contra el banco en el cliente — solo hint informativo

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cerrar Issue #172 con los SHAs de los commits de esta US
- [ ] Continuar con `US-3.4.4` (siguiente pantalla de la Iteración 4 lado docente,
      `docs/plans/inc3/inc3-candidatas.md`)

---

## Lecciones Aprendidas

- ✅ El prototipo aprobado (`#doc-nueva-actividad`) no incluye campo de título — se respetó tal
  cual en vez de inferirlo de la pantalla de listado, evitando ensanchar el alcance de la spec.
  El fallback ya existente en `Actividades.tsx` (`tituloDeActividad()`, `US-3.4.2`) resuelve la
  presentación para actividades sin título.
- ✅ Reusar `materia.cantidadPreguntasActivas` (ya expuesto por `listarMaterias()` desde
  `US-2.1.9`) evitó cualquier necesidad de endpoint o gap de backend para el hint del
  prototipo.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-30
