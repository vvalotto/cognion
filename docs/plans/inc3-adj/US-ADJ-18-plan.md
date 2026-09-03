# Plan de Implementación: US-ADJ-18 - Refactor `SQLAlchemyPreguntaRepository`

**Patrón:** Clean Architecture BC-first
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-18-tracking.json`).
Fases 1/4/6 omitidas (sin BDD, sin tests unitarios nuevos — solo integración existente). Fase
3 incluyó dos iteraciones de diseño (métodos por tipo → CRITICAL de WMC → funciones de módulo)
antes de llegar al diseño final. Tiempo real sin comparación contra estimación humana
(`PRIN-001`).

## Lecciones Aprendidas

- ⚠️ **La sugerencia literal de la spec (extraer mapeadores como métodos privados) generó un
  CRITICAL nuevo** (`WMCAnalyzer`, 22→27/25) que la spec no podía anticipar sin medir: cada
  método nuevo suma complejidad base al WMC de la clase, incluso siendo trivial — extraer
  métodos ayuda a `LongMethodAnalyzer` pero perjudica a `WMCAnalyzer`, una tensión real entre
  dos analyzers del mismo `DesignReviewer`.
- 💡 **Solución real: funciones de módulo en vez de métodos.** `WMCAnalyzer` y
  `FeatureEnvyAnalyzer` solo recorren `ast.ClassDef` — una función privada a nivel de módulo
  (prefijo `_`) queda invisible a ambos analyzers sin perder legibilidad ni el patrón "un
  mapeador corto por tipo concreto". Resultado: 0 issues en el código tocado (mejor que el
  objetivo `≤2` de la spec) y WMC más bajo que el original (15 vs. 22).
- 💡 Medir con `radon cc -s -j` directamente (no solo `designreviewer`) permitió iterar rápido
  sobre el diseño sin esperar la corrida completa del analyzer en cada intento.

## Componentes a Implementar

### 1. `entities/metadatos_pregunta.py` + `entities/pregunta_plantilla.py`
- [x] `MetadatosPregunta.dificultad_valor`/`.importancia_valor` (`.value` ya resuelto)
- [x] `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`: properties
  `dificultad_valor`/`importancia_valor` de compatibilidad (delegan a `metadatos.*`, mismo
  patrón que `US-ADJ-17`) — la gateway queda en `pregunta.dificultad_valor`, profundidad 1
  (antes: `pregunta.dificultad.value`, profundidad 2)

### 2. `interface_adapters/gateways/pregunta_repository.py` — mapeadores como funciones de módulo

**Cambio de diseño respecto al plan original**, decidido durante Fase 3 al medir con `radon`/
`designreviewer` (no solo aplicando la sugerencia literal de la spec): 4 mapeadores privados
como *métodos* de la clase (según pedía la spec) subieron el WMC de la clase de 22 a 27/25
(CRITICAL nuevo — cada método nuevo suma complejidad base al WMC, aunque sea trivial).
Consolidar en 2 métodos (uno por tipo, con `isinstance`/`tipo` interno) bajó el WMC a 25 pero
esos 2 métodos volvieron a superar el umbral de `LongMethodAnalyzer`. La solución real: mover
los mapeadores a **funciones de módulo** (no métodos) — `WMCAnalyzer` y `FeatureEnvyAnalyzer`
solo analizan métodos dentro de `ast.ClassDef`, así que funciones de módulo privadas (`_foo`)
quedan completamente fuera de ambos cómputos, sin perder legibilidad ni el patrón "un
mapeador corto por tipo concreto" que pedía la spec.

- [x] `_modelo_desde_verdadero_falso(pregunta)` / `_modelo_desde_opcion_multiple(pregunta)` —
  funciones de módulo, no métodos
- [x] `_entidad_desde_modelo_verdadero_falso(modelo, metadatos)` /
  `_entidad_desde_modelo_opcion_multiple(modelo, metadatos)` — ídem
- [x] `_a_entidad(modelo)` — también función de módulo (antes `@staticmethod`, sin uso de
  `self`, no había motivo real para que fuera método)
- [x] `_aplicar_pregunta_a_modelo(modelo, pregunta)` — función de módulo, reemplaza los 6
  campos comunes + el `if isinstance` de `respuesta_correcta`/`opciones` que antes vivían
  inline en `actualizar()`
- [x] `guardar()`: `if isinstance(...)` decide qué función de módulo llamar, ~9 líneas
- [x] `obtener_por_id()`/`filtrar()`: llaman `_a_entidad(modelo)` (función de módulo, sin `self.`)
- [x] `actualizar()`: `modelo = await self._session.get(...)`, `_aplicar_pregunta_a_modelo(modelo, pregunta)`,
  `await self._session.commit()` — 5 líneas, sin ningún acceso directo a campos de `pregunta`

`filtrar` (7 parámetros, 42 líneas, Ley de Demeter en `activa.is_`) queda sin tocar — fuera de
alcance de esta US, lo dice la spec explícitamente.

## Verificación

- [x] Tests de integración de `banco_preguntas` en verde, mismas aserciones (118/118,
  comportamiento persistido idéntico)
- [x] `pytest` completo del proyecto en verde (739/739), mismo conteo de tests
- [x] `designreviewer src/ --config pyproject.toml`: `pregunta_repository.py` queda con **0
  issues fuera de `filtrar`** (mejor que el objetivo de la spec, "≤2 issues" contando el de
  `filtrar`) — `LongMethodAnalyzer`/`FeatureEnvyAnalyzer`/`LawOfDemeterAnalyzer` sobre
  `dificultad`/`importancia` en cero; solo quedan los 3 issues de `filtrar` (out of scope):
  `LongMethodAnalyzer` (42 líneas), `LongParameterListAnalyzer` (7 parámetros),
  `LawOfDemeterAnalyzer` (`activa.is_`)
- [x] `mypy src/` sin errores nuevos (43 archivos de `banco_preguntas`)
- [x] 0 CRITICAL (WMC de la clase: 22 → 15, mejor que el original)

**Estado:** 11/11 tareas completadas, gates en verde
