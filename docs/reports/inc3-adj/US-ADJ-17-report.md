# Reporte de Implementación: US-ADJ-17

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-17 - Value Object `MetadatosPregunta` (Data Clump/Primitive
  Obsession, Banco de Preguntas)
- **Puntos estimados:** 8
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-03
- **Origen:** `DesignReviewer src/` — 3 archivos concentraban 41/159 (26%) de los warnings del
  proyecto con la misma causa raíz (Data Clump/Primitive Obsession)

---

## Decisión de diseño (no explícita en la spec — aprobada por Víctor antes de Fase 4/5/7)

La spec no precisaba si el resto del código de lectura (routers, gateway — 42 sitios) debía
pasar a leer `pregunta.metadatos.texto`. Se decidió: la entidad almacena `metadatos:
MetadatosPregunta` (resuelve el Data Clump real, medido en constructores/métodos), pero expone
`texto`/`unidad_tematica`/`tema`/`dificultad`/`importancia` como `@property` de solo lectura
que delegan a `self.metadatos.*`. Esto evitó tocar 42 sitios de lectura no listados en la
tabla "Artefactos a modificar" de la spec, manteniendo acotado el trabajo de `US-ADJ-18`.

---

## Componentes Implementados

### Value Object nuevo
- ✅ `src/banco_preguntas/entities/metadatos_pregunta.py`: `MetadatosPregunta`
  (`dataclass(frozen=True)`), con factory `desde_valores_persistidos()` (conversión
  `str → Dificultad/Importancia`, agregado durante Fase 7 — ver Hallazgos)

### Entities
- ✅ `pregunta_plantilla.py`: `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`
  con campo único `metadatos`, properties de compatibilidad de lectura, `crear()`/`editar()`
  reciben `metadatos: MetadatosPregunta`

### Use Cases (3 archivos)
- ✅ `cargar_pregunta_opcion_multiple.py`, `cargar_pregunta_verdadero_falso.py`,
  `editar_pregunta.py`: `execute()` recibe `metadatos: MetadatosPregunta`

### Controller
- ✅ `preguntas_controller.py`: 3 métodos públicos reciben `metadatos: MetadatosPregunta`

### Router
- ✅ `preguntas_router.py`: 3 call-sites arman `MetadatosPregunta` desde `body` antes de
  invocar al controller — response building sin cambios (vía properties)

### Gateway
- ✅ `pregunta_repository.py`: `_a_entidad` usa `MetadatosPregunta.desde_valores_persistidos()`
  — `guardar`/`actualizar` sin cambios

### Tests actualizados (11 archivos, ~36 sitios — misma cobertura, nueva firma)
- ✅ `test_pregunta_plantilla.py`, `test_cargar_pregunta_opcion_multiple_use_case.py`,
  `test_cargar_pregunta_verdadero_falso_use_case.py`, `test_editar_pregunta_use_case.py`,
  `test_eliminar_pregunta_use_case.py`, `test_preguntas_controller.py`,
  `test_bancos_controller.py`, `test_filtrar_banco_use_case.py`,
  `test_pregunta_repository_integration.py`, `test_preguntas_api_integration.py`,
  `test_filtrar_banco_integration.py`

---

## Hallazgo durante Fase 7 (corregido en la misma US)

Agregar `MetadatosPregunta` como dependencia nueva de `SQLAlchemyPreguntaRepository` empujó su
CBO de 10 a 11/10 (CRITICAL) — mismo patrón de CRITICAL detectado recién en pre-push visto
antes en `US-2.1.2`/`2.1.5`/`2.1.6`/`3.1.3`/`3.2.1`. Corregido con
`MetadatosPregunta.desde_valores_persistidos()` (factory method que centraliza la conversión
`str → Dificultad/Importancia`), evitando que la gateway importe esos dos tipos directamente.
CBO vuelve a 10/10.

---

## Métricas de Calidad

| Métrica | Valor | Estado |
|---------|-------|--------|
| `pytest` completo | 739/739 tests | ✅ (mismo conteo que antes) |
| `mypy src/` | 0 errores, 190 archivos | ✅ |
| `designreviewer src/` — blocking issues | 0 (1 transitorio, corregido) | ✅ |
| `designreviewer src/` — warnings totales | 159 → 129 | ✅ |
| `pregunta_plantilla.py` / `preguntas_controller.py` — issues | 0 (antes: 14 + 12 = 26) | ✅ |

Fuente: `quality/reports/inc3-adj/US-ADJ-17-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests

Sin tests nuevos ni eliminados — 36 sitios de construcción (`.crear()`/`.editar()`/`execute()`)
actualizados a la nueva firma en 11 archivos. 739/739 tests del proyecto en verde.

Sin BDD — refactorización sin cambio de comportamiento observable (Fase 0).

---

## Archivos Creados/Modificados

### Código de producción (8 archivos)
- `src/banco_preguntas/entities/metadatos_pregunta.py` (nuevo)
- `src/banco_preguntas/entities/pregunta_plantilla.py`
- `src/banco_preguntas/use_cases/{cargar_pregunta_opcion_multiple,cargar_pregunta_verdadero_falso,editar_pregunta}.py`
- `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`
- `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
- `src/banco_preguntas/frameworks/api/preguntas_router.py`

### Tests (11 archivos)
- Ver sección "Componentes Implementados"

### Documentación
- `docs/plans/inc3-adj/US-ADJ-17-context.md`
- `docs/plans/inc3-adj/US-ADJ-17-plan.md`
- `docs/reports/inc3-adj/US-ADJ-17-report.md` (este archivo)
- `quality/reports/inc3-adj/US-ADJ-17-quality.json`
- `CHANGELOG.md` (entrada en `[Unreleased] → Changed`)

---

## Criterios de Aceptación

- [x] Cargar una pregunta de opción múltiple sigue funcionando igual (mismo JSON de request/response)
- [x] Editar una pregunta sigue funcionando igual
- [x] `designreviewer src/` confirma la reducción: `pregunta_plantilla.py` y
  `preguntas_controller.py` sin issues de `PrimitiveObsessionAnalyzer`/`DataClumpsAnalyzer`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Continuar el Incremento 3-ADJ con `US-ADJ-18` (refactor `SQLAlchemyPreguntaRepository`
  — Feature Envy/Ley de Demeter/Long Method, ahora con `MetadatosPregunta` ya disponible) y
  `US-ADJ-19` (2 pendientes de 8)

---

## Lecciones Aprendidas

- 💡 Contar sitios reales de lectura vs. construcción (excluyendo imports del grep) antes de
  tocar código evitó sobreestimar el alcance: de 105 matches inflados a 42 lecturas + 36
  construcciones reales.
- 💡 `@property` de compatibilidad en la entidad resolvió el code smell real (medido en
  constructores/métodos) sin ampliar el blast radius a archivos no listados en la spec.
- ⚠️ Agregar una dependencia nueva a una clase ya en el umbral de CBO la empuja a CRITICAL —
  mismo patrón visto en 5 US anteriores. Un factory method en el VO evitó la duplicación de
  imports en la gateway.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-03
