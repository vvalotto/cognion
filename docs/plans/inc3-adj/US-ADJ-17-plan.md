# Plan de Implementación: US-ADJ-17 - Value Object `MetadatosPregunta`

**Patrón:** Clean Architecture BC-first
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-17-tracking.json`).
Fase 1/6 omitidas (sin BDD). Fase 3 incluyó exploración extensa previa (inventario real de 42
sitios de lectura vs. sitios de construcción) antes de decidir el diseño — presentado a Víctor
para aprobación antes de correr Fases 4/5/7. Tiempo real sin comparación contra estimación
humana (`PRIN-001`).

## Lecciones Aprendidas

- 💡 Para un refactor de Data Clump/Primitive Obsession con muchos sitios de *lectura* fuera
  del alcance declarado por la spec, agregar `@property` de compatibilidad en la entidad
  (delegando al VO) resuelve el code smell real (medido en constructores/métodos, no en
  lecturas) sin ampliar el blast radius a archivos no listados como artefactos a modificar.
- 💡 Antes de tocar código, contar los sitios reales de lectura vs. construcción
  (`grep` excluyendo imports) evitó sobreestimar el alcance — de 105 matches iniciales
  (inflados por rutas de import tipo `entities.dificultad`) a 42 lecturas reales + ~36
  construcciones reales.
- ⚠️ Agregar una dependencia nueva a una clase ya en el umbral de CBO (`SQLAlchemyPreguntaRepository`,
  que ya estaba en 10/10) la empuja a CRITICAL — mismo patrón visto en `US-2.1.2`/`2.1.5`/`2.1.6`/
  `3.1.3`/`3.2.1`. Resuelto con un factory method en el propio VO
  (`MetadatosPregunta.desde_valores_persistidos()`) que evita que la gateway necesite importar
  `Dificultad`/`Importancia` directamente.
- ⚠️ Un script de transformación línea a línea (JS/Node, sin AST) fue suficiente y más rápido
  que editar 36 sitios a mano en 11 archivos de test — pero requirió verificar manualmente cada
  archivo después (compilación + `pytest`) porque el patrón no cubre casos con formato
  distinto al observado.

## Decisión de diseño (ver `US-ADJ-17-context.md` para el detalle completo)

El aggregate pasa a almacenar `metadatos: MetadatosPregunta` (reemplaza los 5 campos sueltos),
con `@property` de solo lectura (`texto`, `unidad_tematica`, `tema`, `dificultad`,
`importancia`) que delegan a `self.metadatos.*` — esto resuelve el Data Clump/Primitive
Obsession real (constructores/métodos ya no reciben 5 parámetros sueltos) sin tocar los 42
sitios de **lectura** en `bancos_router.py`/`pregunta_repository.py` que la spec no listaba
como artefactos a modificar.

## Componentes a Implementar

### 1. Value Object nuevo
- [x] `src/banco_preguntas/entities/metadatos_pregunta.py`: `MetadatosPregunta`
  (`dataclass(frozen=True)`: `texto`, `unidad_tematica`, `tema`, `dificultad`, `importancia`)

### 2. Entities
- [x] `src/banco_preguntas/entities/pregunta_plantilla.py`: ambos aggregates con campo
  `metadatos: MetadatosPregunta` (reemplaza los 5 campos), properties de compatibilidad de
  lectura, `crear()`/`editar()` reciben `metadatos` en vez de 5 parámetros

### 3. Use Cases (3 archivos)
- [x] `cargar_pregunta_opcion_multiple.py`: `execute(banco_id, metadatos, opciones)`
- [x] `cargar_pregunta_verdadero_falso.py`: `execute(banco_id, metadatos, respuesta_correcta)`
- [x] `editar_pregunta.py`: `execute(pregunta_id, metadatos, opciones=None, respuesta_correcta=None)`

### 4. Controller
- [x] `preguntas_controller.py`: los 3 métodos públicos reciben `metadatos: MetadatosPregunta`
  en vez de 5 kwargs sueltos (mismo cambio que resuelve sus 12 issues de DesignReviewer)

### 5. Router (arma el VO, no lo desarma)
- [x] `preguntas_router.py`: los 3 call-sites que invocan al controller arman
  `MetadatosPregunta(...)` desde `body` antes de llamar — la construcción de la respuesta
  (`pregunta.texto`, etc.) no cambia, sigue funcionando vía las properties

### 6. Gateway
- [x] `pregunta_repository.py`: `_a_entidad` construye `MetadatosPregunta` desde la fila de
  BD antes de instanciar la entidad — `guardar`/`actualizar` no cambian (siguen leyendo
  `pregunta.texto`/`.dificultad.value` vía las properties, sin tocar columnas)

### 7. Tests actualizados (no agregados — misma cobertura, nueva firma)
- [x] `tests/unit/inc2/test_pregunta_plantilla.py`
- [x] `tests/unit/inc2/test_cargar_pregunta_opcion_multiple_use_case.py`
- [x] `tests/unit/inc2/test_cargar_pregunta_verdadero_falso_use_case.py`
- [x] `tests/unit/inc2/test_editar_pregunta_use_case.py`
- [x] `tests/unit/inc2/test_eliminar_pregunta_use_case.py` (solo fixtures `.crear()`)
- [x] `tests/unit/inc2/test_preguntas_controller.py`
- [x] `tests/unit/inc2/test_bancos_controller.py` (fixture)
- [x] `tests/unit/inc2/test_filtrar_banco_use_case.py` (fixtures)
- [x] `tests/integration/inc2/test_pregunta_repository_integration.py`
- [x] `tests/integration/inc2/test_preguntas_api_integration.py` (fixtures — el resto es HTTP,
  sin cambios de contrato)
- [x] `tests/integration/inc2/test_filtrar_banco_integration.py` (fixtures)

## Verificación (Fase 4/5 = actualización de tests existentes, no agregar nuevos; Fase 7 = gates)

- [x] `pytest` completo del proyecto en verde (739/739), mismo conteo que antes del refactor
- [x] `designreviewer src/ --config pyproject.toml`: `pregunta_plantilla.py` y
  `preguntas_controller.py` sin issues de `PrimitiveObsessionAnalyzer`/`DataClumpsAnalyzer` —
  no aparecen en el reporte (0 issues). Warnings totales bajan de 159 a 129.
- [x] `mypy src/` sin errores nuevos (190 archivos)
- [x] Ningún contrato HTTP cambia — schemas Pydantic sin tocar

**Hallazgo durante Fase 7 (corregido en la misma US):** agregar `MetadatosPregunta` como
dependencia nueva de `SQLAlchemyPreguntaRepository` empujó su CBO de 10 a 11/10 (CRITICAL) —
mismo patrón de CRITICAL detectado recién en pre-push ya visto varias veces en el proyecto
(`US-2.1.2`/`2.1.5`/`2.1.6`/`3.1.3`/`3.2.1`, etc.). Corregido moviendo la conversión
`str → Dificultad/Importancia` a un factory method `MetadatosPregunta.desde_valores_persistidos()`,
así la gateway deja de importar esos dos tipos directamente. CBO vuelve a 10/10, 0 CRITICAL
confirmado.

**Estado:** 7/7 tareas completadas, gates en verde
