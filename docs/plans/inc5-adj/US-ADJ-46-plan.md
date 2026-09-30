# Plan de Implementación: US-ADJ-46 - Docente consulta el ranking de preguntas más falladas

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Analytics)
**Estado:** ✅ COMPLETADO — 2026-09-14
**Tiempo real (tracking):** ~30 min (Fases 0 a 7), 3/3 tareas completadas
**Quality gates:** APROBADO (pylint 9.82/10, CC máx 9, MI mín 50.52, coverage 100%) —
`quality/reports/inc5-adj/US-ADJ-46-quality.json`
**Tests:** 1169/1169 (unit + integration + BDD) en verde

## Lecciones aprendidas

- ⚠️ El sexto Use Case agregado al `AnalyticsController` disparó CRITICAL de CBO (13/10) —
  detectado corriendo `designreviewer` localmente *antes* de commitear (no esperando al
  pre-push), lo que permitió corregirlo en la misma tarea sin un ciclo extra de commits. Se
  separó en `AnalyticsController` (desempeño individual) y `AnalyticsInformesController` nuevo
  (informes agregados de comisión/materia) — mismo criterio de Incremento 2.
- 💡 Correr `designreviewer src/analytics/ --config pyproject.toml` localmente después de cada
  tarea que agrega un Use Case a un controller ya cargado evita el ciclo de "commit → push →
  falla del hook → nuevo commit" — recomendado para `US-ADJ-47` también, que agrega un 5° Use
  Case a algún controller.
- ✅ Extraer el agregado a función de módulo desde el diseño inicial (lección de `US-ADJ-45`)
  evitó cualquier CC CRITICAL en `ObtenerRankingPreguntasFalladasUseCase` esta vez.

## Decisión de diseño previa

Reusa exactamente `listar_respuestas_vigentes_de_materia` (`US-4.1.1`/`US-4.2.4`) — mismo
insumo que `ObtenerTasaErrorPorTemaUseCase`, cambiando la clave de agrupación de
`(unidad_tematica, tema)` a `pregunta_id`. `MetadatoPreguntaResumen` gana `enunciado` (mapea al
campo `texto` de `PreguntaPlantillaModel` — nombres distintos, mismo dato) sin nuevo método de
puerto, mismo criterio documentado en la spec.

**Lección aplicada de `US-ADJ-45`:** el agregado (agrupar por `pregunta_id` + calcular tasa +
ordenar) se diseña desde el arranque como función de módulo separada de `execute()`, para no
repetir el CC CRITICAL detectado recién en Fase 7 la vez pasada.

## Componentes a Implementar

### 1. Port y Adapter (ampliación mínima)
- [x] `src/analytics/entities/ports/pregunta_metadato_consulta_port.py` — `MetadatoPreguntaResumen`
  gana el campo `enunciado: str` (sin nuevo método — mismo `obtener_metadatos`)
- [x] `src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py` — trae
  `modelo.texto` como `enunciado` en la misma consulta por lote
- [x] Actualizar los `Fake*(PreguntaMetadatoConsultaPort)`/instancias de `MetadatoPreguntaResumen`
  existentes en `tests/unit/` que construyen el DTO directo (agregar `enunciado=...`)

### 2. Use Case
- [x] `src/analytics/use_cases/obtener_ranking_preguntas_falladas.py` (nuevo) —
  `RankingPreguntaFallada` (dataclass: `pregunta_id`, `enunciado`, `unidad_tematica`, `tema`,
  `cantidad_presentaciones`, `cantidad_fallos`, `tasa_error`),
  `ObtenerRankingPreguntasFalladasUseCase` — agrupación por `pregunta_id` en función de módulo
  separada (`_agrupar_por_pregunta`), orden por `tasa_error` descendente en `execute()`

### 3. Controller, DI, Schemas y Router
- [x] Controller — CBO CRITICAL (13/10) detectado al correr DesignReviewer localmente antes de
  commitear. Corregido separando `AnalyticsController` (desempeño individual, 2 Use Case) de
  un `AnalyticsInformesController` nuevo (informes agregados de comisión/materia, 4 Use Case:
  `tasa_error_por_tema`, `desempeno_por_comision`, `evolucion_temporal_comision`,
  `ranking_preguntas_falladas`) — mismo criterio de separación por responsabilidad ya aplicado
  en Incremento 2
- [x] `src/analytics/frameworks/dependencies.py` — `get_analytics_informes_controller` nuevo,
  cablea los 4 Use Case agregados
- [x] `src/analytics/frameworks/api/schemas.py` — `RankingPreguntaFalladaResponse`
- [x] `src/analytics/frameworks/api/analytics_router.py` —
  `GET /materias/{materia_id}/ranking-preguntas-falladas?comision_id=` (rol `docente`), mapea
  `ComisionNoPerteneceAMateria` → 422 (mismo patrón que `obtener_tasa_error_por_tema`)

**Estado:** 0/8 tareas completadas
