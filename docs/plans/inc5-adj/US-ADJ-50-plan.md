# Plan de Implementación: US-ADJ-50 - Docente ve el ranking de "Preguntas más falladas"

**Patrón:** Frontend puro (React + TypeScript) — sin cambios de backend, mismo patrón que
`US-ADJ-48`/`US-ADJ-49`/`US-4.2.5`/`US-4.2.6`
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-14
**Tiempo real (tracker):** ~28 min (Fases 0-8, sin BDD ni tests de integración/backend por ser US frontend puro)

## Componentes a Implementar

### 1. Cliente API
- [ ] `frontend/src/lib/analytics-api.ts`
  - Interface `RankingPreguntaFalladaResponse` (camelCase): `preguntaId`, `enunciado`,
    `unidadTematica`, `tema`, `cantidadPresentaciones`, `cantidadFallos`, `tasaError`
  - Interface interna `RankingPreguntaFalladaApiResponse` (snake_case, shape real del backend
    `US-ADJ-46`: `pregunta_id`, `enunciado`, `unidad_tematica`, `tema`,
    `cantidad_presentaciones`, `cantidad_fallos`, `tasa_error`)
  - Función `mapearRankingPreguntaFallada(...)`
  - Función `obtenerRankingPreguntasFalladas(materiaId, comisionId?, signal?)` — `GET
    /analytics/materias/{materiaId}/ranking-preguntas-falladas?comision_id=` (mismo patrón de
    query opcional que `obtenerTasaErrorPorTema`)

### 2. Pantalla
- [ ] `frontend/src/pages/analytics/RankingPreguntasFalladas.tsx`
  - Mismo esqueleto que `DesempenoPorTema.tsx`: selector Materia (`listarMaterias`, obligatorio)
    → selector Comisión (`listarComisionesPorMateria`, opcional, default "Toda la materia",
    se resetea al cambiar de Materia)
  - Listado `.ranking-row` numerado (posición = índice + 1 en la lista ya ordenada por el
    backend, puramente de presentación — no viaja en la respuesta)
  - Por fila: número de posición, enunciado (truncado a una línea con `truncate`/
    `line-clamp-1`), unidad/tema, cantidad de presentaciones, % de tasa de error con el mismo
    código de color de severidad que `DesempenoPorTema.tsx` (≥50% rojo, 20-49% ámbar, <20%
    verde) — reutilizar las mismas constantes `COLOR_TEXTO`/`severidad()` con la misma firma,
    duplicadas localmente (no hay componente compartido entre `US-4.2.6` y esta, mismo criterio
    documentado en la spec)
  - Estado vacío: mensaje sin listado cuando el ranking devuelve `[]`
  - `Breadcrumb`: `[{ label: "Analytics" }, { label: "Preguntas más falladas" }]`

### 3. Integración
- [ ] `frontend/src/router.tsx`
  - Import `RankingPreguntasFalladas`
  - Ruta `/analytics/ranking-preguntas-falladas`, protegida con `<RequireRole rol="docente">`
    (mismo bloque que `/analytics/desempeno-por-tema`)
- [ ] `frontend/src/components/AppNav.tsx`
  - Entrada "Preguntas más falladas" → `/analytics/ranking-preguntas-falladas` en el array de
    items del rol `docente`, después de "Desempeño por tema"

**Estado:** 3/3 tareas completadas

## Resultado

- 7 tests Vitest nuevos (`RankingPreguntasFalladas.test.tsx`), 100% en verde.
- Test existente `AppNav.test.tsx` actualizado ("Docente ve sus 6 ítems" → "7 ítems") tras
  agregar la entrada de navegación.
- Suite completa del frontend: 487/487 en verde (`npm run test`), `npm run build` (`tsc -b` +
  `vite build`) sin errores, `oxlint` 0 errores.
- Cobertura global de branches: 81.86% (umbral `US-ADJ-16`: ≥80%).
- Reporte de quality gates: `quality/reports/inc5-adj/US-ADJ-50-quality.json`.
- Hallazgo operativo (no de esta US): bajo `vitest run --coverage`, 5 tests preexistentes no
  relacionados (`ResetearPassword`, `NuevaPreguntaOpcionMultiple`, `NuevaPreguntaVerdaderoFalso`,
  `AutoregistroDocente`, `CambiarPassword`) mostraron timeouts intermitentes de 5000ms por carga
  de la instrumentación — confirmados en verde tanto de forma aislada como en una segunda
  corrida completa con coverage. Mismo patrón de flake ya documentado para
  `NuevaPreguntaOpcionMultiple.test.tsx` en `US-ADJ-24`.
