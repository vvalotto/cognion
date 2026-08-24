# Reporte de Implementación: US-2.1.13

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.13 - Docente elimina una pregunta desde la UI, con
  confirmación previa
- **Puntos estimados:** 2
- **Tiempo real:** ~2 min de trabajo activo del agente (fases 0-9, ver
  `.claude/tracking/US-2.1.13-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-17

---

## Alcance

Frontend puro, sin cambios de backend — consume `DELETE /preguntas/{id}` tal como quedó en
`US-2.1.6`. Para mostrar el texto de la pregunta a eliminar reutiliza
`GET /bancos/{id}/preguntas` (`US-2.1.7`, vía `filtrarBanco()`) — mismo criterio de "sin
cambios de backend" que `US-2.1.12`.

---

## Componentes Implementados

### Frontend
- ✅ **`EliminarPregunta.tsx`** (nuevo, `frontend/src/pages/EliminarPregunta.tsx`) — resuelve
  `materia` vía `listarMaterias()` y la pregunta a eliminar buscándola por `preguntaId` en el
  resultado de `filtrarBanco(bancoId)`; muestra su texto y una aclaración explícita de que es
  baja lógica (INV-BP-04, no afecta sesiones pasadas); botón "Sí, eliminar" llama
  `eliminarPregunta()` (ya existente desde `US-2.1.8`) y vuelve al banco; "Cancelar" vuelve sin
  llamar al backend; maneja el caso de pregunta inexistente con un mensaje simple, mismo
  criterio que `EditarPregunta.tsx`
- ✅ **`router.tsx`** — nueva ruta
  `/materias/:materiaId/banco/preguntas/:preguntaId/eliminar`
- ✅ **`Banco.tsx`** — habilita el botón "Eliminar" de la tabla (deshabilitado desde `US-2.1.10`
  con `title="Disponible en US-2.1.13"`), ahora navega a la pantalla de confirmación

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `EliminarPregunta.tsx` (statements/branches/functions) | 96.87% / 77.77% / 100% | ≥ 80% (statements) | ✅ |
| Coverage `Banco.tsx` (statements/branches/functions) | 95.65% / 89.28% / 90% | ≥ 80% (statements) | ✅ |
| Coverage global frontend (statements) | 92.51% | ≥ 80% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.13-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios (4 tests nuevos, Vitest, `EliminarPregunta.test.tsx`)**
- Muestra el texto de la pregunta y la aclaración de baja lógica
- Confirmar eliminación ejecuta la baja lógica y vuelve al banco
- Cancelar vuelve al banco sin llamar al backend
- Pregunta inexistente muestra un mensaje en vez de la confirmación

**Unitarios adicionales (1 test nuevo, `Banco.test.tsx`)**
- El botón "Eliminar" de una fila navega a la confirmación de eliminación de esa pregunta

**Integración (1 test nuevo, `router.test.tsx`)**
- Ruta `.../preguntas/:id/eliminar` renderiza la confirmación real con sesión de docente

**BDD (2 escenarios frontend)**
- `tests/features/inc2/US-2.1.13-eliminar-pregunta.feature` — validados por mapeo directo a los
  tests de Vitest de arriba (sin step_defs/pytest-bdd, misma adaptación de `US-2.1.9`–`US-2.1.12`)

**Todos los tests pasando:** ✅ 103/103 frontend (suite completa)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/pages/EliminarPregunta.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado)
- `frontend/src/pages/Banco.tsx` (modificado — botón "Eliminar" habilitado)

### Tests
- `tests/features/inc2/US-2.1.13-eliminar-pregunta.feature` (nuevo)
- `frontend/src/pages/EliminarPregunta.test.tsx` (nuevo)
- `frontend/src/pages/Banco.test.tsx` (modificado)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.1.13.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc2/US-2.1.13-context.md`
- `docs/plans/inc2/US-2.1.13-plan.md`
- `docs/reports/inc2/US-2.1.13-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.13-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Confirmar eliminación — el sistema ejecuta la baja lógica y vuelve al banco filtrado, la
  pregunta ya no aparece en la tabla
- [x] Cancelar eliminación — el sistema vuelve al banco filtrado sin cambios

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Cierra completa la Iteración 1 del Incremento 2 (`US-2.1.10` a `US-2.1.13`), backend y
  frontend juntos.
- [ ] Evaluar cierre de baseline BL-003 — mismo criterio que `BL-002` (la Baseline no cierra
  backend-only, y esta iteración ya está completa en ambas capas).
- [ ] Modelar la Iteración 2 (RF-03, gestión de cuentas por administrador) — wireframes nuevos,
  según `docs/plans/inc2/inc2-candidatas.md` §Iteración 2.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-17
