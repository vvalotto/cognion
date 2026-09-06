# Reporte de Implementación: US-4.2.6

## Resumen Ejecutivo

- **Historia de Usuario:** US-4.2.6 - Docente ve "Desempeño por tema"
- **Puntos estimados:** 3
- **Tiempo real:** ~10 min de trabajo activo del agente (fases 0, 2, 3, 4, 7, 8, 9, ver
  `.claude/tracking/US-4.2.6-tracking.json`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-06

---

## Alcance

Frontend puro, sin cambios de backend — consume `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=`
(`US-4.2.4`, ya cerrado) y `GET /materias/{materia_id}/comisiones` (`US-4.2.2`, ya cerrado).
A diferencia de `US-4.2.5`, esta pantalla no reutiliza `DesempenoResumenDetalle.tsx` — el
wireframe (`wireframes-analytics.md` §3.1) define una forma propia (`.tema-row`: unidad + tema,
barra de progreso coloreada por severidad, % y conteo), sin resumen acumulado ni detalle por
evaluación. **Cierra completa la Iteración 2 del Incremento 4** (RF-16/RF-17, backend +
frontend juntos) — ambos RF pasan a Implementado, según el mismo criterio de
`inc2-candidatas.md`/`inc3-candidatas.md` (Validado espera al cierre de baseline con UAT).

---

## Componentes Implementados

### Frontend
- ✅ **`analytics-api.ts`** (modificado, `frontend/src/lib/analytics-api.ts`) — agrega el tipo
  `TasaErrorTemaResponse` y `obtenerTasaErrorPorTema(materiaId, comisionId?, signal?)`, mapeo
  snake_case→camelCase; `comisionId` opcional omite el query param cuando no viene (agrega toda
  la materia)
- ✅ **`DesempenoPorTema.tsx`** (nueva, `frontend/src/pages/analytics/`) — pantalla
  `#doc-desempeno-tema`: selector Materia (siempre, `listarMaterias()`) → Comisión (opcional,
  `listarComisionesPorMateria()`, default "Toda la materia"); listado de `(unidadTematica, tema)`
  ya ordenado por tasa de error descendente desde el backend, sin reordenar en cliente; función
  pura `severidad(tasaError)` (`>= 0.5` alta/rojo, `>= 0.2` media/ámbar, si no baja/verde,
  umbrales de UI, no de dominio); estado vacío sin listado; cambiar de Materia reinicia Comisión
  a `""` y reconsulta
- ✅ **`router.tsx`** — nueva ruta `/analytics/desempeno-por-tema`, protegida con
  `<RequireRole rol="docente">`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores, 5 warnings (todos preexistentes, ninguno nuevo) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `analytics-api.ts` (statements/branches/functions/lines) | 100% / 100% / 100% / 100% | ≥ 80% (statements) | ✅ |
| Coverage `DesempenoPorTema.tsx` (statements/branches/functions/lines) | 94% / 81.48% / 82.35% / 95.34% | ≥ 80% (statements) | ✅ |

Fuente: `quality/reports/inc4/US-4.2.6-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios (3 tests nuevos, `analytics-api.test.ts`)**
- `obtenerTasaErrorPorTema` sin `comisionId` mapea a camelCase y no agrega query param
- Agrega `comision_id` a la query cuando se pasa
- Mapea una lista vacía (materia sin evaluaciones finalizadas)

**Componente (6 tests nuevos, `DesempenoPorTema.test.tsx`)**
- Estado inicial: placeholder sin listado
- Elegir Materia consulta toda la materia (sin `comision_id`) y muestra el listado ordenado
- Elegir una Comisión puntual reconsulta con `comision_id`
- Color por severidad: alta (rojo) ≥50%, media (ámbar) 20-49%, baja (verde) <20%
- Materia sin evaluaciones finalizadas: estado vacío
- Cambiar de Materia reinicia Comisión a "Toda la materia" y reconsulta

**Todos los tests de esta US pasando:** ✅ 13/13 (2 archivos)

**Nota sobre la suite completa:** al correr `vitest run --coverage` con la suite completa (261
tests), se observaron fallas intermitentes por timeout en `NuevaPreguntaOpcionMultiple.test.tsx`
y `NuevaPreguntaVerdaderoFalso.test.tsx` — ninguno de los dos tocado por esta US, ambos pasan
siempre en ejecución aislada. Mismo flakiness preexistente del entorno ya documentado en
`US-4.2.5-quality.json` (contención de recursos al correr en paralelo con coverage habilitado).

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/lib/analytics-api.ts` (modificado)
- `frontend/src/pages/analytics/DesempenoPorTema.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado — import + ruta nueva)

### Tests
- `frontend/src/lib/analytics-api.test.ts` (modificado)
- `frontend/src/pages/analytics/DesempenoPorTema.test.tsx` (nuevo)

### Documentación
- `docs/specs/inc4/US-4.2.6.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc4/US-4.2.6-context.md`
- `docs/plans/inc4/US-4.2.6-plan.md`
- `docs/plans/inc4/inc4-candidatas.md` (marcado el cierre de esta US y de la Iteración 2)
- `docs/reports/inc4/US-4.2.6-report.md` (este archivo)
- `quality/reports/inc4/US-4.2.6-quality.json`

---

## Criterios de Aceptación

- [x] Materia completa por defecto: elegir una Materia con evaluaciones finalizadas muestra el
      listado ordenado por tasa de error descendente, agregado de toda la materia
- [x] Acotar a una comisión: elegir una Comisión puntual recalcula el listado solo con esas
      respuestas
- [x] Color por severidad: ≥50% rojo, 20-49% ámbar, <20% verde
- [x] Materia sin evaluaciones finalizadas: mensaje de estado vacío, sin listado
- [x] Acceso sin rol Docente: redirigido por `RequireRole`, no ve la pantalla (patrón ya
      cubierto por `RequireRole.test.tsx` — la pantalla no implementa RBAC propio)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] UAT de cierre de la Iteración 2 del Incremento 4 (backend + frontend juntos) —
      `docs/plans/inc4/inc4-candidatas.md`
- [ ] Tras la UAT: matriz de trazabilidad, RF-16/RF-17 a Implementado

---

## Lecciones Aprendidas

- 💡 A diferencia de `US-4.2.5`, no hubo componente visual para compartir con otra pantalla —
  forzar la reutilización de `DesempenoResumenDetalle.tsx` acá habría sido artificial (esa
  pantalla muestra resumen + detalle por evaluación de un estudiante; esta muestra un ranking
  de temas de una materia/comisión, forma completamente distinta). Confirma el criterio de
  extraer un componente compartido solo cuando dos pantallas ya muestran el mismo dato con la
  misma forma, no por anticipación.
- 💡 `tasa_error` llega del backend como fracción (0-1, no 0-100 como `porcentaje_acierto`) —
  detectado leyendo `obtener_tasa_error_por_tema.py` antes de escribir el cliente, evitó un bug
  de doble multiplicación por 100 en la barra de progreso.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-06
