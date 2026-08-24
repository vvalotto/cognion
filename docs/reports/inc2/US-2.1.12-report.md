# Reporte de Implementación: US-2.1.12

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.12 - Docente edita una pregunta existente desde la UI
- **Puntos estimados:** 3
- **Tiempo real:** ~40 min (fases 0-9, ver `.claude/tracking/US-2.1.12-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-16

---

## Alcance

Frontend puro, sin cambios de backend — consume `PUT /preguntas/{id}` tal como quedó en
`US-2.1.5`. Para obtener la pregunta a editar reutiliza `GET /bancos/{id}/preguntas`
(`US-2.1.7`, vía `filtrarBanco()`) — no existe endpoint `GET /preguntas/{id}` dedicado, mismo
criterio de "sin cambios de backend" de la spec.

---

## Componentes Implementados

### Frontend
- ✅ **`EditarPregunta.tsx`** (nuevo, `frontend/src/pages/EditarPregunta.tsx`) — resuelve
  `materia` vía `listarMaterias()` y la pregunta a editar buscándola por `preguntaId` en el
  resultado de `filtrarBanco(bancoId)`; determina el tipo concreto (`"opciones" in pregunta`,
  mismo helper que `Banco.tsx`) y renderiza el formulario correspondiente prellenado, sin
  selector de tipo (fijo, no editable); botón "Guardar cambios" llama `editarPregunta()`
  (ya existente desde `US-2.1.8`) y vuelve al banco; "Cancelar" vuelve sin guardar; maneja
  el caso de pregunta inexistente con un mensaje simple en vez de una pantalla dedicada
  (mismo criterio de simplicidad del wireframe §4)
- ✅ **`router.tsx`** — reemplaza el placeholder de
  `/materias/:materiaId/banco/preguntas/:preguntaId/editar` (dejado por `US-2.1.8`) por la
  pantalla real
- ✅ **`_placeholders.tsx`** — se eliminó `BancoPreguntasPlaceholder`, sin referencias tras esta
  US (confirmado con el usuario en Fase 3)

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `EditarPregunta.tsx` (statements/branches/functions) | 90.52% / 85.18% / 92.1% | ≥ 80% (statements) | ✅ |

Fuente: `quality/reports/inc2/US-2.1.12-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios (8 tests nuevos, Vitest, `EditarPregunta.test.tsx`)**
- Prellena el formulario de Opción Múltiple con los valores actuales
- Edición exitosa de Opción Múltiple persiste los cambios y vuelve al banco
- Rechazo de cliente por opciones inválidas bloquea el envío sin llamar al backend
- Prellena el formulario de Verdadero/Falso con la respuesta actual
- Pregunta inexistente muestra un mensaje en vez del formulario
- Edición exitosa de Verdadero/Falso persiste los cambios y vuelve al banco
- Editar el texto de una opción y agregar/quitar opciones en Opción Múltiple
- "Cancelar" vuelve al banco sin llamar al backend

**Integración (1 test nuevo, reemplaza el test parametrizado de placeholder, `router.test.tsx`)**
- Ruta `.../preguntas/:id/editar` renderiza el formulario de edición real con sesión de docente

**BDD (2 escenarios frontend)**
- `tests/features/inc2/US-2.1.12-editar-pregunta.feature` — validados por mapeo directo a los
  tests de Vitest de arriba (sin step_defs/pytest-bdd, misma adaptación de `US-2.1.9`–`US-2.1.11`)

**Todos los tests pasando:** ✅ 97/97 frontend (suite completa)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/pages/EditarPregunta.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado)
- `frontend/src/pages/_placeholders.tsx` (modificado — `BancoPreguntasPlaceholder` eliminado)

### Tests
- `tests/features/inc2/US-2.1.12-editar-pregunta.feature` (nuevo)
- `frontend/src/pages/EditarPregunta.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.1.12.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc2/US-2.1.12-context.md`
- `docs/plans/inc2/US-2.1.12-plan.md`
- `docs/reports/inc2/US-2.1.12-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.12-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Edición exitosa — el sistema persiste los cambios y vuelve al banco filtrado mostrando el
  texto actualizado
- [x] Rechazo de cliente por opciones inválidas — bloquea el envío con mensaje de validación

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-2.1.13` (Docente elimina una pregunta con confirmación previa) — habilita
  el botón "Eliminar", deshabilitado desde `US-2.1.10`; cierra la Iteración 1 del Incremento 2
- [ ] Al cerrar `US-2.1.13`: evaluar cierre de baseline BL-003 (mismo criterio que `BL-002` —
  la Baseline no cierra backend-only, y esta iteración ya está completa en ambas capas)

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-16
