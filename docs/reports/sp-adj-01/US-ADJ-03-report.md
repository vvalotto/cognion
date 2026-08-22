# Reporte de Implementación: US-ADJ-03

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-03 - Paginar el listado del banco de preguntas
- **Puntos estimados:** 5
- **Tiempo real (tracker):** 81 min (Fases 0 a 8)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-22
- **Tipo:** feature backend + frontend — segunda US de la iteración de ajuste conjunta
  `SP-ADJ-01` (`US-ADJ-01`/`US-ADJ-03`/`US-ADJ-04`/`US-ADJ-05`)

---

## Decisión de diseño (detectada en Fase 2, no cubierta por la spec original)

`GET /bancos/{id}/preguntas` lo consumen 5 pantallas, no solo `Banco.tsx`:
`EditarPregunta.tsx`/`EliminarPregunta.tsx` buscan una pregunta por id entre *todas* las del
banco, y `NuevaPreguntaOpcionMultiple/VerdaderoFalso.tsx` derivan sugerencias de unidad/tema
de *todas*. La spec original proponía paginar por defecto (página 1 de 20) — eso hubiera roto
esas 4 pantallas en bancos de más de 20 preguntas, exactamente el escenario que motiva esta
US (71 preguntas).

**Decisión confirmada con Víctor:** paginación **opt-in**. `pagina`/`tamanio_pagina` son
opcionales en el puerto y en el endpoint; si el cliente no los manda, se devuelven todas las
preguntas que matchean los filtros (comportamiento previo, sin truncar). Solo `Banco.tsx`
pasa esos parámetros. El contrato de respuesta pasa a ser siempre `{ preguntas, total }`
(antes lista plana) — las otras 4 pantallas solo necesitaron leer `.preguntas` en vez de la
lista directa.

---

## Componentes Implementados

### Backend (`src/banco_preguntas/`)

- ✅ `entities/pregunta_plantilla.py` — `fecha_creacion: datetime` en ambos aggregates,
  fijado en `crear()` vía `default_factory`, inmutable en `editar()`
- ✅ `entities/resultado_paginado_preguntas.py` (nuevo) — `ResultadoPaginadoPreguntas`
  (`preguntas`, `total`)
- ✅ `entities/ports/pregunta_repository_port.py` — `filtrar()` gana `pagina`/`tamanio_pagina`
  opcionales, retorna `ResultadoPaginadoPreguntas`
- ✅ `interface_adapters/gateways/pregunta_repository.py` — `ORDER BY fecha_creacion, id`
  (desempate estable) siempre; `LIMIT`/`OFFSET` solo si se piden ambos parámetros; query de
  `total` separada
- ✅ `frameworks/db/models.py` — columna `fecha_creacion` en `PreguntaPlantillaModel`
- ✅ `migrations/versions/8867d9e26bc0_pregunta_plantilla_fecha_creacion.py` — backfill vía
  `server_default=func.now()`, sin `UPDATE` manual
- ✅ `use_cases/filtrar_banco.py`, `use_cases/listar_materias.py` (ajustado al nuevo retorno)
- ✅ `interface_adapters/controllers/bancos_controller.py`,
  `frameworks/api/schemas.py` (`PreguntasPaginadasResponse`),
  `frameworks/api/bancos_router.py` — query params `pagina`/`tamanio_pagina` opcionales

### Frontend

- ✅ `components/ui/pagination.tsx` (nuevo, reusable — pensado para que `US-ADJ-05` lo reuse
  en el listado de cuentas)
- ✅ `lib/banco-preguntas-api.ts` — `filtrarBanco()` acepta `PaginacionBanco` opcional,
  retorna `PreguntasPaginadas`
- ✅ `pages/Banco.tsx` — estado de página, reset a 1 al cambiar cualquier filtro, controles de
  paginación debajo de la tabla
- ✅ `pages/EditarPregunta.tsx`, `EliminarPregunta.tsx`, `NuevaPreguntaOpcionMultiple.tsx`,
  `NuevaPreguntaVerdaderoFalso.tsx` — ajustados a `.preguntas` del nuevo contrato, sin cambio
  de comportamiento

---

## Métricas de Calidad

| Métrica | Backend | Frontend | Umbral |
|---|---|---|---|
| pylint | 9.16/10 | — | ≥ 8.0 |
| CC máx | Grado A/B (sin excepciones) | — | ≤ 10 |
| MI mín | 48.77 | — | ≥ 20 |
| Coverage | 100% (`src/banco_preguntas`) | 92.04% global | ≥ 95% / ≥80% ref. |
| oxlint | — | 0 errores | 0 errores |
| `tsc --noEmit` | — | 0 errores | 0 errores |

Fuente: `quality/reports/sp-adj-01/US-ADJ-03-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

- **Backend unit:** `test_filtrar_banco_use_case.py` (+2 casos de paginación),
  `test_bancos_controller.py` (+1 caso), `test_listar_materias_use_case.py` (sin cambios de
  API, verificado sin regresión)
- **Backend integración:** `test_filtrar_banco_integration.py` (+3 casos: orden estable,
  `LIMIT`/`OFFSET`, página fuera de rango; ajustados los existentes a `{preguntas, total}`)
- **Backend BDD:** `tests/step_defs/sp_adj_01/test_us_adj_03_steps.py` (nuevo, 4 escenarios
  con `pytest-bdd` real) + `test_us_2_1_7_steps.py` corregido (contrato de respuesta cambiado)
- **Frontend:** `Banco.test.tsx` (+4 casos de paginación), `banco-preguntas-api.test.ts`,
  `EditarPregunta.test.tsx`, `EliminarPregunta.test.tsx`, `NuevaPreguntaOpcionMultiple.test.tsx`,
  `NuevaPreguntaVerdaderoFalso.test.tsx`, `router.test.tsx` — todos ajustados al nuevo
  contrato de respuesta

### Escenarios BDD (4 escenarios, `tests/features/sp-adj-01/US-ADJ-03-paginar-banco-preguntas.feature`)

- ✅ Banco con más de una página de resultados
- ✅ Cambiar de página
- ✅ Cambiar un filtro reinicia la paginación
- ✅ Banco con una sola página

**Todos los tests pasando:** ✅ 368 backend (300 unit/integración + 68 BDD), 156 frontend

---

## Verificación Visual

Recorrido en navegador real (Chrome vía claude-in-chrome) con 25 preguntas reales cargadas
vía API: página 1 muestra 20 preguntas con controles "Anterior" (deshabilitado), "1"/"2",
"Siguiente" (habilitado); clic en "Siguiente" muestra las 5 restantes con "Anterior"
habilitado y "Siguiente" deshabilitado; aplicar el filtro "Dificultad: Medio" vuelve
correctamente a la página 1. Sin hallazgos.

---

## Archivos Creados/Modificados

### Nuevos
- `src/banco_preguntas/entities/resultado_paginado_preguntas.py`
- `migrations/versions/8867d9e26bc0_pregunta_plantilla_fecha_creacion.py`
- `frontend/src/components/ui/pagination.tsx`
- `tests/features/sp-adj-01/US-ADJ-03-paginar-banco-preguntas.feature`
- `tests/step_defs/sp_adj_01/test_us_adj_03_steps.py`
- `docs/plans/sp-adj-01/US-ADJ-03-context.md`, `US-ADJ-03-plan.md`
- `docs/reports/sp-adj-01/US-ADJ-03-report.md` (este archivo)
- `quality/reports/sp-adj-01/US-ADJ-03-quality.json`

### Modificados
- `src/banco_preguntas/entities/pregunta_plantilla.py`,
  `entities/ports/pregunta_repository_port.py`,
  `interface_adapters/gateways/pregunta_repository.py`, `frameworks/db/models.py`,
  `use_cases/filtrar_banco.py`, `use_cases/listar_materias.py`,
  `interface_adapters/controllers/bancos_controller.py`, `frameworks/api/schemas.py`,
  `frameworks/api/bancos_router.py`
- `frontend/src/lib/banco-preguntas-api.ts`, `pages/Banco.tsx`, `pages/EditarPregunta.tsx`,
  `pages/EliminarPregunta.tsx`, `pages/NuevaPreguntaOpcionMultiple.tsx`,
  `pages/NuevaPreguntaVerdaderoFalso.tsx`
- Tests: `tests/unit/inc2/_fakes.py`, `test_filtrar_banco_use_case.py`,
  `test_bancos_controller.py`, `tests/integration/inc2/test_filtrar_banco_integration.py`,
  `tests/step_defs/inc2/test_us_2_1_7_steps.py`,
  `frontend/src/pages/Banco.test.tsx`, `EditarPregunta.test.tsx`, `EliminarPregunta.test.tsx`,
  `NuevaPreguntaOpcionMultiple.test.tsx`, `NuevaPreguntaVerdaderoFalso.test.tsx`,
  `frontend/src/router.test.tsx`, `frontend/src/lib/banco-preguntas-api.test.ts`
- `docs/design/ux/wireframes-banco-preguntas.md` (gate UX), `CLAUDE.md`, `CHANGELOG.md`

---

## Criterios de Aceptación

- [x] `GET /bancos/{id}/preguntas` acepta `pagina`/`tamanio_pagina` opcionales, orden estable
  por `fecha_creacion`
- [x] Página fuera de rango devuelve lista vacía, no error
- [x] Cambiar cualquier filtro reinicia la paginación a la página 1
- [x] Preguntas cargadas antes de esta US migradas con backfill (timestamp de la migración)
- [x] Ningún criterio de aceptación de `US-2.1.7`/`US-2.1.10` ni de las 4 pantallas que
  reusan `filtrarBanco()` cambió

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-ADJ-05` (paginación del listado de cuentas) — reutiliza `components/ui/pagination.tsx`
  introducido en esta US
- [ ] `US-ADJ-04` (estilo visual de Cuentas/Contraseñas) — sin dependencia de esta US, puede
  implementarse en paralelo o después
- [ ] Cierre de la iteración de ajuste conjunta `SP-ADJ-01` y evaluación de cierre de
  baseline `BL-003`

---

## Lecciones Aprendidas

- ⚠️ Una spec de ajuste escrita antes de revisar todos los call-sites de un endpoint
  compartido puede introducir una regresión funcional real (la paginación forzada hubiera
  roto 4 pantallas) — vale la pena, en Fase 2, listar explícitamente quién más consume el
  endpoint que se está por cambiar, no solo la pantalla que motiva el cambio
- ✅ El patrón de columna con `server_default=func.now()` para backfill (ya usado en
  `usuario_creado_en`) se reutilizó sin fricción para `fecha_creacion`
- 💡 Separar la query de conteo (`total`) de la query paginada mantiene el gateway simple y
  evita duplicar lógica de filtros entre ambas

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-22
