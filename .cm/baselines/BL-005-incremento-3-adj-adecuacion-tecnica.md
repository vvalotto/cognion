# BL-005 — Incremento 3-ADJ, Adecuación Técnica

| Campo | Valor |
|-------|-------|
| Tipo | Incremento técnico (no planificado en `PLAN_v1.md` — insertado fuera de la secuencia 0-7) |
| Fecha apertura | 2026-09-02 |
| Fecha cierre | 2026-09-03 |
| Git tag inicial | — (continúa desde `v0.5.0`, `BL-004`) |
| Git tag cierre | Pendiente de decisión con Víctor (merge `develop → main` diferido, mismo criterio que `BL-001`/`BL-002`/`BL-003`) |
| Estado | ✅ Completado en `develop` — pendiente merge a `main` |
| DoD | Las 8 US-ADJ candidatas (`US-ADJ-13` a `20`) implementadas, quality gates en verde, `ArchitectAnalyst`/`DesignReviewer` corridos de nuevo confirmando mejoras donde correspondía (`docs/plans/inc3-adj/inc3-adj-candidatas.md` §"Criterio de cierre"). Sin UAT — deuda de tooling/arquitectura, nada visible para un usuario final. |

---

## Descripción

Incremento técnico insertado fuera de secuencia (decisión de Víctor, 2026-09-02: no renumerar
los Incrementos 4-7 ya mapeados a RF) inmediatamente después del cierre de `BL-004`. Origen:
deuda de tooling/arquitectura que las retros de `BL-002`, `BL-003` y `BL-004` venían señalando
sin resolver (recalibración de `ArchitectAnalyst`), más hallazgos de la sesión de cierre de
`BL-004` (cobertura de branches del frontend, revisión puntual de `DesignReviewer src/`, un
flake intermitente de CI detectado en el triage de PRs de Dependabot). Ninguna de las 8 US-ADJ
tiene RF asociado ni mueve fila de la matriz de trazabilidad (mismo criterio que
`US-1.1.0`/`US-2.1.2`).

- **`US-ADJ-13`** — "Zone of Pain" de `ArchitectAnalyst` documentado como falso positivo
  aceptado permanentemente + limpieza de claves inválidas de `[tool.architectanalyst]`.
- **`US-ADJ-14`** — `frontend/src/pages/` reordenado por Bounded Context (33 pantallas movidas
  a 4 subcarpetas), igual que la organización ya existente de `lib/` y de `src/<bc>/` en el
  backend.
- **`US-ADJ-15`** — fix de `coverage_report_path` en `[tool.architectanalyst]`:
  `CoverageAnalyzer` pasa de warning ("archivo no encontrado") a reportar el porcentaje real
  de cobertura.
- **`US-ADJ-16`** — cobertura de branches del frontend por encima del umbral global (80%): 3
  tests de teclado en `NuevaPreguntaTipo.test.tsx` cierran el gap real medido (79.66% → 80.12%).
- **`US-ADJ-17`** — Value Object `MetadatosPregunta` (Data Clump/Primitive Obsession, Banco de
  Preguntas): `pregunta_plantilla.py`/`preguntas_controller.py` bajan de 26 issues combinados a
  0. Decisión de diseño no explícita en la spec (aprobada con Víctor): properties de
  compatibilidad de lectura en la entidad, evitando tocar 42 sitios de lectura fuera del
  alcance declarado.
- **`US-ADJ-18`** — refactor `SQLAlchemyPreguntaRepository` (Feature Envy/Ley de
  Demeter/Long Method): 15 → 3 issues (los 3 restantes son de `filtrar()`, fuera de alcance).
  Hallazgo de diseño: extraer mapeadores como métodos (como pedía la spec) disparaba un
  CRITICAL nuevo de `WMCAnalyzer` — resuelto moviéndolos a funciones de módulo, invisibles a
  `WMCAnalyzer`/`FeatureEnvyAnalyzer`.
- **`US-ADJ-19`** — `LayerViolationsAnalyzer` documentado como no confiable + causa raíz real
  encontrada en `DependencyGraphBuilder` (Issue upstream
  [`software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77)). Ampliación de
  alcance aprobada por Víctor: **corrige la explicación técnica de `US-ADJ-13`** — el "Zone of
  Pain" no se debe a que cada BC sea hoja del grafo por diseño arquitectónico, sino a que el
  mismo bug deja `Ca=Ce=0` para *todo* el proyecto. La aceptación del falso positivo se
  mantiene, cambia la causa raíz documentada.
- **`US-ADJ-20`** (agregada durante la sesión, fuera de la lista original de 7 — detectada en
  el triage de PRs de Dependabot) — `AbortController` en los `useEffect`/submit de 21
  componentes de frontend, elimina la condición de carrera pre-existente detrás de un
  `unhandled rejection` intermitente en CI.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D35 | `docs/plans/inc3-adj/inc3-adj-candidatas.md` | Documento | Investigación previa + las 8 US candidatas del incremento técnico |
| CI-D36 | `docs/specs/ajustes/US-ADJ-13.md` a `US-ADJ-20.md` | Documento | Specs de las 8 US-ADJ |
| CI-D37 | `docs/plans/inc3-adj/US-ADJ-13-context.md` a `US-ADJ-20-plan.md` (16 archivos), `docs/reports/inc3-adj/US-ADJ-13-report.md` a `US-ADJ-20-report.md` (8 archivos) | Documento | Contexto, plan y reporte de cierre de cada una de las 8 US-ADJ |
| CI-C16 | `src/banco_preguntas/entities/metadatos_pregunta.py` (nuevo), `entities/pregunta_plantilla.py`, `use_cases/{cargar_pregunta_opcion_multiple,cargar_pregunta_verdadero_falso,editar_pregunta}.py`, `interface_adapters/controllers/preguntas_controller.py`, `interface_adapters/gateways/pregunta_repository.py`, `frameworks/api/preguntas_router.py` | Código de backend | Value Object `MetadatosPregunta` + refactor de la gateway (`US-ADJ-17`/`18`) |
| CI-F11 | `frontend/src/pages/{identidad,cuentas,banco-preguntas,actividad-evaluativa}/` (33 pantallas movidas), `frontend/src/lib/*-api.ts` (+`signal` opcional), `frontend/src/pages/**/*.tsx` (21 componentes con `AbortController`) | Código de frontend | Reordenamiento por BC (`US-ADJ-14`) + fix de condición de carrera (`US-ADJ-20`) |
| CI-T06 | `pyproject.toml`: `[tool.architectanalyst]`/`[tool.architectanalyst.layers]` | Herramienta | Config de calidad corregida (`US-ADJ-13`/`15`/`19`) |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 739 passed
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (190 archivos)
- `pylint src/`: 9.59/10 (antes de este incremento: 9.50/10)
- Cobertura (`pytest --cov=src`): 98.9%

**Frontend:**
- `vitest run --coverage --no-file-parallelism`: 232/232 tests, 41 archivos
- Cobertura: 90.65% statements / **80.12% branches** (antes: 77.89%, por debajo del umbral —
  ahora por encima) / 86.44% functions / 92.94% lines
- `oxlint`: 0 errores, 4 warnings preexistentes (sin cambios, no introducidos en este
  incremento)
- `tsc -b --noEmit`: 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml` (consolidado, estado final del incremento): 0
  CRITICAL, **118 advertencias** (antes: 159 al abrir el incremento), 88.4h de deuda técnica
  estimada (0h bloqueante)
- `architectanalyst src/ --sprint-id BL-005 --config pyproject.toml`: 5 críticos (mismo "Zone
  of Pain" ya documentado — `identidad`, `settings`, `shared`, `banco_preguntas`,
  `actividad_evaluativa` —, causa raíz corregida por `US-ADJ-19`), 7 warnings, 118 infos,
  `should_block: false`. `CoverageAnalyzer` en `info` con 98.9% real (antes: warning, archivo
  no encontrado)

**Sin UAT** — deuda de tooling/arquitectura, nada visible para un usuario final (criterio
explícito del incremento).

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Merge `develop → main` y tag diferidos otra vez | Mismo ítem abierto que `BL-001` a `BL-004` — no hay Docker en el entorno de desarrollo local. A confirmar con Víctor al cerrar esta baseline. |
| Baseline propia (`BL-005`) en vez de plegarse a la apertura del Incremento 4 | Decisión de Víctor al cerrar `US-ADJ-19` (última de las 8) — mismo criterio de trazabilidad que los incrementos anteriores, aunque este no tenga RF asociado. |
| `US-ADJ-17`: properties de compatibilidad en vez de propagar `.metadatos.` a todo el código de lectura | Decisión de diseño no explícita en la spec, aprobada con Víctor antes de correr Fases 4/5/7 — evita ampliar el blast radius a 42 sitios de lectura no listados como artefactos a modificar. |
| `US-ADJ-18`: mapeadores como funciones de módulo, no métodos | Seguir la spec literalmente (métodos privados) disparaba un CRITICAL nuevo de `WMCAnalyzer` — descubierto midiendo con `radon`, no anticipado por la spec. |
| `US-ADJ-19` ampliada para corregir `US-ADJ-13` | La investigación llegó a la causa raíz real en el código de la herramienta (bug de `DependencyGraphBuilder`), que contradice la explicación técnica que había quedado documentada en `US-ADJ-13` ("cada BC es hoja del grafo por diseño arquitectónico"). Aprobado por Víctor antes de implementar. |
| `US-ADJ-20` agregada fuera de la lista original de 7 | Detectada durante el triage de PRs de Dependabot en la misma sesión — mismo criterio que `US-ADJ-09`/`10`/`11`/`12` en `BL-004` (hallazgo que toca `src/`/`frontend/`, track formal, resuelto en la misma sesión). |

---

## Retrospectiva

### ¿Qué funcionó?

- Medir el estado real antes de tocar código (`US-ADJ-15`, `US-ADJ-16`) evitó trabajo de más
  en dos US: el gap de cobertura de branches ya no era el 77.89%→80% original (`US-ADJ-20` lo
  había subido incidentalmente a 79.66%), y el fix de `coverage_report_path` se verificó con
  datos reales (98.9%), no solo "el archivo se encuentra".
- Detenerse a preguntar antes de implementar decisiones de diseño no explícitas en la spec
  (`US-ADJ-17`: properties de compatibilidad; `US-ADJ-19`: ampliar el alcance para corregir
  `US-ADJ-13`) evitó tanto un blast radius innecesario como dejar una conclusión incorrecta
  documentada sin corregir.
- El patrón "medir con la herramienta base (`radon`) antes de confiar en la sugerencia literal
  de una spec" (`US-ADJ-18`) permitió iterar sobre el diseño real de un refactor sin esperar la
  corrida completa de `designreviewer` en cada intento, y evitó introducir un CRITICAL nuevo.

### ¿Qué fue más difícil de lo esperado?

- La sugerencia literal de `US-ADJ-18` (extraer mapeadores como métodos) resultó
  contraproducente sin que la spec pudiera anticiparlo — reveló una tensión real entre
  `LongMethodAnalyzer` (favorece dividir métodos) y `WMCAnalyzer` (penaliza más métodos por
  clase) que ninguna de las specs de `DesignReviewer` documenta explícitamente.
- La investigación de `US-ADJ-19` reveló que una conclusión ya cerrada y aceptada (`US-ADJ-13`)
  estaba mal fundamentada — un recordatorio de que aceptar un falso positivo de una herramienta
  sin llegar a su causa raíz real puede dejar una explicación plausible pero incorrecta
  documentada indefinidamente.
- Al medir las métricas de cierre corriendo `pytest`/`vitest`/`radon`/`designreviewer` en
  paralelo (mismo entorno, alta carga), una corrida de `pytest` completa dio 75 fallos y 14
  errores — reproducido limpio en la corrida siguiente, sin nada en paralelo, 739/739 en verde.
  Mismo patrón de flakiness por carga de máquina ya documentado en `US-ADJ-20`/`HITO-8`, esta
  vez en el gate de cierre de baseline en vez de en CI.

### ¿Qué ajustar en el próximo incremento?

- Resolver la decisión de infraestructura/Docker — cada baseline que se acumula sin ella hace
  más costoso el eventual `merge → main` con 5 tags pendientes de una sola vez.
- Backlog diferido de `DesignReviewer` (~118 warnings restantes, sin cluster comparable a los
  ya resueltos) queda documentado en `docs/plans/inc3-adj/inc3-adj-candidatas.md` §"Backlog
  diferido" — retomar si algún archivo de esa lista vuelve a concentrar issues nuevos.
- El Issue upstream [`software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77)
  queda abierto sin ETA — cuando se resuelva, correr `architectanalyst` de nuevo para confirmar
  si `LayerViolationsAnalyzer` empieza a detectar violaciones reales (o falsos positivos
  nuevos que también haya que evaluar).

---

*Creado: 2026-09-03*
