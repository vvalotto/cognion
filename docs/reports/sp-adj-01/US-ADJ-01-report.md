# Reporte de Implementación: US-ADJ-01

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-01 - Alinear visualmente las pantallas de Banco de Preguntas
  con el prototipo aprobado
- **Puntos estimados:** 3
- **Tiempo real (tracker):** 55 min (Fases 0 a 8)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-22
- **Tipo:** refactor de presentación puro (frontend), sin cambios de comportamiento ni de
  backend — primera US de la iteración de ajuste conjunta `SP-ADJ-01` (`US-ADJ-01`/`US-ADJ-03`)

---

## Componentes Implementados

### Primitivas nuevas (`frontend/src/components/`)

- ✅ **`ui/card.tsx`** — `Card`/`CardContent`, contenedor con sombra + borde + radius (shadcn)
- ✅ **`ui/badge.tsx`** — `Badge` con `cva`: variantes `tipo-om`/`tipo-vf`/`nivel-alto`/
  `nivel-medio`/`nivel-bajo`
- ✅ **`ui/button.tsx`** (extendido) — variante nueva `destructive-solid`, sin tocar la
  variante `destructive` existente (usada por `ResetearPassword.tsx`, Identidad)
- ✅ **`Breadcrumb.tsx`** — componente propio liviano, no shadcn

### Pantallas re-vestidas (sin cambios de comportamiento)

- ✅ `pages/Materias.tsx` — breadcrumb, grid de `Card` por materia, card punteada "+ Nueva materia"
- ✅ `pages/NuevaMateria.tsx` — breadcrumb, formulario en `Card`
- ✅ `pages/Banco.tsx` — breadcrumb, filtros y tabla en `Card`, `Badge` en Tipo/Dificultad/
  Importancia, botón "Eliminar" con `destructive-solid`
- ✅ `pages/NuevaPreguntaTipo.tsx` — breadcrumb, cards de selección de tipo (`tipo-card`)
- ✅ `pages/NuevaPreguntaOpcionMultiple.tsx` — breadcrumb, formulario en `Card`, resaltado
  verde de la opción correcta
- ✅ `pages/NuevaPreguntaVerdaderoFalso.tsx` — breadcrumb, formulario en `Card`, toggle V/F
  con resaltado verde
- ✅ `pages/EditarPregunta.tsx` — mismo tratamiento que las pantallas de carga, según tipo
- ✅ `pages/EliminarPregunta.tsx` — alert ámbar (warning, no destructive), botón
  "Sí, eliminar" con `destructive-solid`

---

## Métricas de Calidad (adaptación frontend — sin pylint/CC/MI)

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores (2 advertencias preexistentes por patrón) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 150/150 pasando | 100% | ✅ |
| Cobertura global | 92.49% stmts / 84.85% branches / 91.3% funcs / 94.08% lines | ≥80% referencia | ✅ |

Fuente: `quality/reports/sp-adj-01/US-ADJ-01-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Ajustados por cambio de estructura DOM (sin cambiar comportamiento)

- `Materias.test.tsx` — selector de "+ Nueva materia" migrado a `getByRole` (texto partido en
  2 elementos)
- `Banco.test.tsx` — selector de "Ingeniería de Software" migrado a `getByRole("heading")`
  (el nombre ahora también aparece en el breadcrumb)

### Nuevos (validan los 3 escenarios BDD de la spec)

- `Materias.test.tsx` — breadcrumb + card "Nueva materia" con borde punteado
- `Banco.test.tsx` — tags de color por Tipo/Dificultad/Importancia + botón Eliminar sólido

### Escenarios BDD (3 escenarios, `tests/features/sp-adj-01/US-ADJ-01-estilo-visual-banco.feature`)

- ✅ Listado de materias con el estilo del prototipo
- ✅ Banco de preguntas con tags de color
- ✅ Sin regresión funcional

Validados con Vitest + React Testing Library — sin pytest-bdd, mismo criterio que `US-1.1.6`
a `US-2.2.9` para US frontend puras.

**Todos los tests pasando:** ✅ 150 passed, 0 failed

---

## Verificación Visual (requisito explícito de la spec)

Recorrido en navegador real (Chrome vía claude-in-chrome) contra
`docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`, con datos reales cargados
(materia + 2 preguntas vía API, limpiados al finalizar): Materias, Banco (con scroll
horizontal de la tabla), selección de tipo, formulario de Opción Múltiple (resaltado de
opción correcta) y confirmación de Eliminar. Sin hallazgos — coincide con el prototipo
aprobado.

---

## Archivos Creados/Modificados

### Nuevos
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/badge.tsx`
- `frontend/src/components/Breadcrumb.tsx`
- `docs/plans/sp-adj-01/US-ADJ-01-context.md`
- `docs/plans/sp-adj-01/US-ADJ-01-plan.md`
- `docs/reports/sp-adj-01/US-ADJ-01-report.md` (este archivo)
- `quality/reports/sp-adj-01/US-ADJ-01-quality.json`
- `tests/features/sp-adj-01/US-ADJ-01-estilo-visual-banco.feature`

### Modificados
- `frontend/src/components/ui/button.tsx` (variante `destructive-solid`)
- `frontend/src/pages/Materias.tsx`, `Materias.test.tsx`
- `frontend/src/pages/NuevaMateria.tsx`
- `frontend/src/pages/Banco.tsx`, `Banco.test.tsx`
- `frontend/src/pages/NuevaPreguntaTipo.tsx`
- `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx`
- `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx`
- `frontend/src/pages/EditarPregunta.tsx`
- `frontend/src/pages/EliminarPregunta.tsx`
- `CLAUDE.md`, `CHANGELOG.md`

---

## Criterios de Aceptación

- [x] Cada pantalla listada reproduce breadcrumb, cards con sombra, tags de color y botón
  "Eliminar" sólido, verificado visualmente en navegador real (no solo revisión de código)
- [x] Ningún criterio de aceptación funcional de `US-2.1.9` a `US-2.1.13` cambió
- [x] Suite de tests existente (Vitest + RTL) sigue en verde, con los selectors ajustados

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-ADJ-03` (paginación del banco de preguntas) — reutiliza el lenguaje visual de
  `Card`/`Badge` introducido en esta US para sus controles de paginación
- [ ] Cierre de la iteración de ajuste conjunta `SP-ADJ-01` y evaluación de cierre de
  baseline `BL-003`

---

## Lecciones Aprendidas

- ✅ Reutilizar el color `accent` (verde) existente para el resaltado de "correcta" evitó
  introducir tokens CSS nuevos — el prototipo ya usaba ese mismo verde para `success`
- ⚠️ Con `--coverage` habilitado, Vitest necesitó `testTimeout` mayor a 5000ms en tests con
  `userEvent` sobre formularios largos — no es una regresión de la implementación, es
  overhead de instrumentación
- 💡 `getByRole` con nombre accesible resiste mejor los cambios de estructura DOM que
  `getByText` con texto exacto cuando un elemento se divide en varios nodos hijos

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-22
