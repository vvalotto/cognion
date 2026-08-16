# Reporte de Implementación: US-2.1.10

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.10 - Docente ve y filtra el banco de preguntas de una materia
- **Puntos estimados:** 3
- **Tiempo real:** ~17 min (fases 0-7, ver `docs/plans/inc2/US-2.1.10-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-16

---

## Alcance

Frontend puro, sin cambios de backend — consume `GET /bancos/{id}/preguntas` tal como quedó en
`US-2.1.7`, y `GET /materias` (`US-2.1.9`) para resolver `materiaId → nombre/bancoId` sin
agregar un endpoint dedicado.

---

## Componentes Implementados

### Frontend
- ✅ **`Banco.tsx`** (nuevo, `frontend/src/pages/Banco.tsx`) — tabla + barra de filtros
  (unidad/tema texto libre, dificultad/importancia `<select>` nativo), refresca al cambiar
  cualquier filtro, acciones "Editar"/"+ Nueva pregunta" hacia las rutas placeholder de
  `US-2.1.8` (las reemplazan `US-2.1.11`–`US-2.1.13`), "Eliminar" deshabilitado (ruta de
  confirmación todavía no existe)
- ✅ **`router.tsx`** — reemplaza el placeholder `BancoPreguntasPlaceholder` de
  `/materias/:materiaId/banco` por la pantalla real

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `Banco.tsx` (statements/branches/functions) | 95.55% / 89.28% / 89.47% | ≥ 80% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.10-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios/Integración (7 tests nuevos, Vitest)**
- `Banco.test.tsx` — banco sin filtros, filtrar por dificultad, filtro sin resultados, filtrar
  por unidad temática, "Limpiar filtros", navegación a "Editar", navegación a "+ Nueva pregunta"
- `router.test.tsx` (modificado) — `/materias/:id/banco` renderiza la pantalla real con sesión
  de docente; ruta retirada de la lista de placeholders parametrizada

**BDD (3 escenarios frontend)**
- `tests/features/inc2/US-2.1.10-listado-filtro-banco.feature` — validados por mapeo directo a
  los tests de Vitest de arriba (sin step_defs/pytest-bdd, misma adaptación de `US-2.1.9`)

**Todos los tests pasando:** ✅ 80/80 frontend (suite completa)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/pages/Banco.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado)

### Tests
- `tests/features/inc2/US-2.1.10-listado-filtro-banco.feature` (nuevo)
- `frontend/src/pages/Banco.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.1.10.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc2/US-2.1.10-context.md`
- `docs/plans/inc2/US-2.1.10-plan.md`
- `docs/reports/inc2/US-2.1.10-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.10-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Ver el banco sin filtros — muestra todas las preguntas activas de la materia
- [x] Filtrar por dificultad — la tabla se actualiza con la nueva consulta
- [x] Filtro sin resultados — tabla vacía, sin mensaje de error

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-2.1.11` (Docente carga una pregunta eligiendo su tipo) — reemplaza el
  placeholder de "+ Nueva pregunta"
- [ ] Implementar `US-2.1.12` (editar) y `US-2.1.13` (eliminar, con confirmación) — reemplazan
  los placeholders de "Editar" y habilitan el botón "Eliminar" deshabilitado en esta US

---

## Lecciones Aprendidas

- ✅ Reutilizar `listarMaterias()` (`US-2.1.9`) para resolver `materiaId → nombre/bancoId`
  evitó agregar un endpoint nuevo.
- ⚠️ El botón "Eliminar" por fila quedó deshabilitado (no navega) porque la ruta de
  confirmación la crea recién `US-2.1.13` — desvío documentado respecto del plan original.
- ⚠️ Las columnas de dificultad/importancia se muestran como texto simple, no como "tag por
  color" del wireframe §2.3 — no hay convención de color de tags definida en el proyecto
  todavía; ajuste visual menor pendiente, no bloqueante.
- ✅ `fireEvent.change` en vez de `userEvent.type` para los filtros de texto evitó disparar una
  consulta HTTP por cada tecla, que agotaba los mocks de `fetch` en los tests.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-16
