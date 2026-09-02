# Incremento 3-ADJ — Adecuación Técnica — US candidatas

> Estado documental: **Especificadas, ninguna implementada todavía.**
> Incremento técnico no planificado originalmente en `docs/rf/PLAN_v1.md` — inserción fuera de
> la secuencia numérica 0-7 (decisión de Víctor, 2026-09-02: no renumerar los Incrementos 4-7
> ya mapeados a RF). Milestone GitHub:
> [Incremento 3-ADJ — Adecuación Técnica](https://github.com/vvalotto/cognion/milestone/10).
>
> Origen: deuda de tooling/arquitectura que las retros de `BL-002`, `BL-003` y `BL-004` vienen
> señalando sin resolver (recalibración de `ArchitectAnalyst`), más los hallazgos propios de
> esta sesión (cobertura de branches del frontend, y una revisión puntual de
> `DesignReviewer src/` para identificar los clusters de deuda técnica más concentrados).
>
> Ninguna de estas US-IEDD tiene RF asociado — mismo criterio que `US-1.1.0`/`US-2.1.2` (US
> técnicas sin fila propia en `docs/traceability/matrix.md`). No mueven ninguna fila de la
> matriz de trazabilidad.

---

## Investigación previa (por qué la lista es esta y no otra)

Antes de especificar, se investigó cada ítem contra el código real de la herramienta
(`quality_agents.architectanalyst`, instalada en `.venv/`) en vez de asumir que la
recalibración "obvia" iba a funcionar:

- **`analysis_depth=2`** (pensado para "arquitecturas hexagonales con namespace de app") se
  probó contra `src/` real: los críticos de "Zone of Pain" **subieron de 5 a 15** — parte cada
  BC en `entities`/`use_cases`/`interface_adapters`/`frameworks`, y las tres últimas capas de
  cada BC no tienen ninguna clase abstracta (los puertos `ABC` viven solo en `entities/ports/`),
  así que cada una da D=1.00 CRITICAL por separado. La causa raíz no es que falten
  abstracciones (los 18 puertos del proyecto ya son `ABC`) sino que cada BC es una hoja del
  grafo de dependencias por diseño (`Ca=0` siempre, por la regla de "sin imports directos entre
  BCs") — ninguna granularidad de análisis cambia esa proporción. **Decisión: aceptar como falso
  positivo permanente, sin tocar la config** (`US-ADJ-13`).
- **`coverage_report_path`**: se confirmó por qué `CoverageAnalyzer` nunca encontraba
  `coverage.json` — la ruta se resuelve relativa al primer `PATH` pasado al CLI (`src/`), no a
  la raíz del repo. Con `coverage_report_path = "../coverage.json"` el chequeo pasó a reportar
  98.9% correctamente (verificado). **Fix validado, no solo propuesto** (`US-ADJ-15`).
- **`[tool.architectanalyst.layers]`**: la config actual (`entities = ["src/*/entities"]`, etc.)
  no coincide con el schema real de la herramienta (que espera nombre-de-capa → lista de
  nombres-de-capa permitidos, no globs de rutas). Se probó corrigiendo el formato al documentado
  — **cero violaciones detectadas igual**. Para descartar "el proyecto está limpio" se forzó una
  regla imposible de cumplir (`frameworks = []`, cuando `frameworks/` siempre importa
  `entities`/`use_cases` para el composition root) — **seguía en cero**. Conclusión: el chequeo
  "siempre CRITICAL, no configurable" para violaciones de capas viene siendo un no-op silencioso
  desde que se configuró, con cualquier config probada (`US-ADJ-19`).
- **`DesignReviewer src/`** (159 warnings, 130h de deuda estimada): se agruparon por archivo en
  vez de especificar 159 ítems sueltos. Los 3 archivos con más issues concentrados
  (`pregunta_repository.py` 15, `pregunta_plantilla.py` 14, `preguntas_controller.py` 12 — 41 de
  159, ~26%) comparten una única causa raíz: el mismo Data Clump
  `{texto, unidad_tematica, tema, dificultad, importancia}` repetido en `entities`, `use_cases`
  (parámetros) y `interface_adapters`/`gateways` (persistencia) del Banco de Preguntas. Se separó
  en dos specs: el Value Object en sí (`US-ADJ-17`, resuelve la mayoría de los issues de los 3
  archivos) y el refactor específico del mapeo entidad↔modelo en el repositorio
  (`US-ADJ-18`, Feature Envy/Law of Demeter que el Value Object solo no resuelve). El resto de
  los 159 (~118, repartidos en ~35 archivos, sin cluster comparable) queda **explícitamente
  diferido, sin spec individual** — ver tabla al final.

---

## US candidatas

| US | Título | Capas afectadas | Origen concreto |
|---|---|---|---|
| **US-ADJ-13** | Documentar "Zone of Pain" de ArchitectAnalyst como falso positivo aceptado + limpiar claves inválidas de `[tool.architectanalyst]` | Documentación (`CLAUDE.md`, `pyproject.toml`) | Retro `BL-002`/`BL-003`/`BL-004`, investigación de esta sesión |
| **US-ADJ-14** | Reordenar `frontend/src/pages/` por BC | Frontend (solo movimiento de archivos + imports) | Conversación de esta sesión sobre estructura de frontend |
| **US-ADJ-15** | Fix de `coverage_report_path` en `[tool.architectanalyst]` | Documentación/config (`pyproject.toml`) | Investigación de esta sesión — fix verificado |
| **US-ADJ-16** | Subir cobertura de branches del frontend (77.89% → 80%) | Frontend (tests) | Retro `BL-004` |
| **US-ADJ-17** | Value Object `MetadatosPregunta` (Data Clump/Primitive Obsession, Banco de Preguntas) | Backend — `entities`/`use_cases`/`interface_adapters` de `banco_preguntas` | `DesignReviewer src/`, esta sesión |
| **US-ADJ-18** | Refactor `SQLAlchemyPreguntaRepository` (Feature Envy/Law of Demeter/Long Method) | Backend — `interface_adapters/gateways` de `banco_preguntas` | `DesignReviewer src/`, esta sesión |
| **US-ADJ-19** | `LayerViolationsAnalyzer` no detecta ninguna violación bajo ninguna config — reportar upstream, documentar como no confiable | Documentación (`CLAUDE.md`) + Issue upstream en `software_limpio` | Investigación de esta sesión |

Specs completas en `docs/specs/ajustes/US-ADJ-13.md` a `US-ADJ-19.md`.

---

## Backlog diferido — NO especificado individualmente

El resto de los 159 warnings de `DesignReviewer src/` (~118, tras descontar los 41 de
`US-ADJ-17`/`US-ADJ-18`) queda documentado por archivo, sin spec propia — especificar cada uno
sería desproporcionado para un proyecto unipersonal. Se retoma si algún archivo de esta lista
vuelve a aparecer concentrando issues nuevos en un incremento futuro (mismo criterio que motivó
juntar `US-ADJ-17`/`18` ahora).

| Archivo | Issues | Analyzers dominantes |
|---|---|---|
| `actividad_evaluativa/frameworks/api/evaluaciones_router.py` | 6 | LongMethod, LawOfDemeter |
| `actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py` | 5 | LongMethod, LongParameterList |
| `identidad/entities/usuario.py` | 5 | LongMethod, PrimitiveObsession |
| `identidad/interface_adapters/gateways/usuario_repository.py` | 5 | LawOfDemeter, LongMethod |
| `identidad/interface_adapters/gateways/cuenta_query_repository.py` | 5 | LawOfDemeter, LongMethod |
| `actividad_evaluativa/entities/evaluacion.py` | 4 | LongMethod, DataClumps |
| `actividad_evaluativa/frameworks/api/actividades_router.py` | 4 | LongParameterList |
| `identidad/frameworks/api/cuentas_router.py` | 4 | LongParameterList, PrimitiveObsession |
| Resto (~27 archivos) | 1-3 c/u | Variado, sin patrón repetido |

---

## Criterio de cierre de este incremento

No hay UAT (nada de esto es visible para un usuario final) — el criterio de cierre es: los 7
US-ADJ implementados, quality gates en verde (mismos de siempre: pytest/vitest, mypy, ruff,
oxlint, tsc, DesignReviewer 0 CRITICAL), y `ArchitectAnalyst`/`DesignReviewer` corridos de
nuevo al final para confirmar que los números mejoraron donde correspondía (`US-ADJ-16`,
`US-ADJ-17`, `US-ADJ-18`) y que `US-ADJ-13`/`15`/`19` quedaron correctamente documentados.
Baseline propia: a decidir con Víctor al cerrar (¿amerita `BL-005` o se pliega a la apertura
del Incremento 4?).
