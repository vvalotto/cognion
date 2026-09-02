# Reporte de Implementación: US-3.4.5

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.4.5 — Estudiante ve sus materias y las actividades disponibles
- **Puntos estimados:** 5
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-31
- **Spec:** `docs/specs/inc3/US-3.4.5.md`

Quinta US de la Iteración 4 del Incremento 3 (frontend, RF-11/RF-12) y primer punto de entrada
del Estudiante al frontend de Actividad Evaluativa. Agrega "Mis materias" y, dentro de cada
una, el listado de actividades visibles con un `Badge` de estado calculado desde la
perspectiva del Estudiante autenticado.

---

## Corrección detectada durante la implementación (Fase 3, contra el prototipo aprobado)

El plan de Fase 2 diseñó 4 estados de `Badge` (agregando `"cerrada_sin_rendir"` a los 3 de la
spec). Al llegar al frontend, el prototipo aprobado
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html` (`#est-actividades`)
resultó tener **solo 3 badges** — no existe uno propio para "cerrada sin rendir". Corregido con
Víctor (criterio ya establecido en el proyecto: el prototipo manda sobre el texto de la spec):
se eliminó `"cerrada_sin_rendir"` del backend ya escrito — una actividad cerrada sin evaluación
del Estudiante se muestra como `"pendiente"` (mismo criterio que `EnCurso`/`Suspendida` no
distinguidas); el 422 `FueraDePeriodo` al intentar iniciar (`US-3.4.6`) resuelve ese caso.

---

## Componentes Implementados

### BC Identidad

- ✅ **`require_estudiante`** (`frameworks/dependencies.py`, nuevo) — hasta esta US solo existía
  en Actividad Evaluativa; primer endpoint de Identidad gateado a rol `estudiante` distinto de
  login/registro/cambio de password
- ✅ **`ListarMateriasDelEstudianteUseCase`** (`use_cases/listar_materias_del_estudiante.py`,
  nuevo) — resuelve `Usuario.perfil.comision_id` → `Comision.materia_id` → `MateriaPort`
  (reutilizado de `US-2.1.2`, sin puerto nuevo)
- ✅ **`EstudianteController`** (nuevo) — adapta el use case a la respuesta HTTP
- ✅ **`GET /identidad/estudiante/materias`** (`frameworks/api/estudiante_router.py`, nuevo) —
  rol `estudiante`, usa `usuario_id` del JWT

### BC Actividad Evaluativa

- ✅ **`EvaluacionEstudianteQueryPort`** (`entities/ports/`, nuevo) —
  `existentes_finalizadas(evaluacion_ids) -> set[UUID]`. Separado y no ensanchando
  `EvaluacionActivaQueryPort` (`US-3.2.4`, propósito distinto: evaluaciones NO finalizadas) —
  mismo criterio de separación command/query que evitó el CRITICAL de CBO en
  `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.2.2`
- ✅ **`SQLAlchemyEvaluacionEstudianteQueryRepository`** (nuevo) — un único `SELECT DISTINCT
  aggregate_id ... WHERE event_type = 'EvaluacionFinalizada'`, sin replay completo (`Finalizada`
  es un estado terminal)
- ✅ **`ListarActividadesVisiblesUseCase`** (`use_cases/listar_actividades_visibles.py`, nuevo)
  — extiende `ListarActividadesUseCase` (`US-3.4.2`) calculando `Evaluacion.id_para()` por
  actividad y el `Badge` (`"pendiente" | "todavia_no_abrio" | "finalizada"`)
- ✅ **`ActividadesEstudianteController`** (nuevo) — separado de `ActividadesQueryController`
  (consulta docente), mismo criterio de separación por actor
- ✅ **`GET /actividades/mis-actividades`** (`frameworks/api/actividades_router.py`, nuevo) —
  rol `estudiante`, registrado antes de `/{actividad_id}` para no chocar con esa ruta

### Frontend

- ✅ **`identidad-estudiante-api.ts`** (nuevo) — `listarMisMaterias()`
- ✅ **`actividad-evaluativa-api.ts`** (extendido) — `listarActividadesVisibles()`,
  `ActividadVisibleResponse`, `EstadoVisible`
- ✅ **`MisMaterias.tsx`** (nueva) — reemplaza el placeholder de `/mis-actividades/materias`;
  `Badge` resumen ("N pendiente" / "Sin actividades disponibles") derivado en el cliente
  contando `"pendiente"` por materia (el backend no expone ese conteo, aceptable a esta escala)
- ✅ **`MisActividades.tsx`** (nueva) — reemplaza el placeholder de
  `/mis-actividades/materias/:materiaId/actividades`; navega según el `Badge`
- ✅ **`FueraDePeriodo.tsx`** (nueva) — ruta nueva `/mis-actividades/:actividadId/fuera-de-periodo`;
  recibe título/`fechaApertura` por `navigate(..., {state})` desde `MisActividades` (no hay
  endpoint de detalle de actividad accesible a `estudiante`)
- ✅ **`badge.tsx`** (extendido) — 3 variantes nuevas: `visible-pendiente`,
  `visible-todavia-no-abrio`, `visible-finalizada`
- ✅ **`router.tsx`** — reemplaza 2 placeholders de `US-3.4.1` + agrega la ruta de
  fuera-de-período

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (archivos tocados) | 9.81/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 5 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (promedio archivos tocados) | 83.2 | > 20 | ✅ |
| Cobertura (`src/identidad` + `src/actividad_evaluativa`, excluye `frameworks/*`) | 99% | ≥ 95% | ✅ |
| mypy (`src/` completo) | 0 errores | 0 errores | ✅ |
| Frontend — oxlint | 0 errores | 0 errores | ✅ |
| Frontend — `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Frontend — cobertura pantallas nuevas | 89-92% (100% en `FueraDePeriodo.tsx`) | — | ✅ |

**Estado General:** ✅ APROBADO — `quality/reports/inc3/US-3.4.5-quality.json`

### Detalle de CodeGuard

> Reporte generado con `--analysis-type full`. `vulture`/`codespell` no estaban instalados en
> el entorno — agregados como dev dependencies (`uv add --dev vulture codespell`) para obtener
> los 9 checks reales en vez de placeholders "not installed". El único error real
> (`DeadCode`) es un falso positivo de vulture sobre el parámetro de un método abstracto sin
> cuerpo; los 179 warnings de `DeadCode` y 14 de `Spelling` son ruido esperable de vulture sobre
> clases Pydantic/funciones de router FastAPI (nunca "llamadas" directamente, invisibles a un
> analizador estático). El check `Pylint` de codeguard tuvo timeout intermitente (>10s) sobre
> 1-2 archivos en corridas sucesivas — mismo patrón de flakiness ya documentado para `Types`
> (`software_limpio#70`); el pylint standalone (sin límite de tiempo) corrió limpio: 9.81/10.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 13 |
| PEP8 | 0 | 2 | 11 |
| Complexity | 0 | 0 | 13 |
| DeadCode | 1 (falso positivo vulture) | 179 (ruido vulture sobre schemas/routers) | 1 |
| Maintainability | 0 | 0 | 13 |
| Pylint | 1 (timeout intermitente) | 0 | 12 |
| Spelling | 0 | 14 | 7 |
| Types | 0 | 0 | 13 |
| UnusedImports | 0 | 0 | 13 |

Fuente: `quality/reports/inc3/US-3.4.5-codeguard.json`.

---

## Tests Implementados

### Tests Unitarios (11 tests nuevos)

- ✅ `test_listar_materias_del_estudiante_use_case.py` (4 tests) — materia resuelta, y rechazo
  de `UsuarioNoExiste`/`ComisionNoExiste`/`MateriaNoExiste`
- ✅ `test_estudiante_controller.py` (1 test) — delegación al use case
- ✅ `test_listar_actividades_visibles_use_case.py` (5 tests) — pendiente, todavía no abrió,
  finalizada, cerrada-sin-rendir se muestra como pendiente, lista vacía
- ✅ `test_actividades_estudiante_controller.py` (1 test) — delegación al use case

100% de cobertura en los 4 componentes nuevos con lógica de negocio propia.

### Tests de Integración (6 tests nuevos)

- ✅ `test_estudiante_materias_actividades_api_integration.py` —
  `TestEstudianteMateriasAPIIntegration` (materia real, 401 sin auth, 403 rol docente) y
  `TestActividadesVisiblesAPIIntegration` (pendiente, todavía no abrió, finalizada — flujo
  completo iniciar+finalizar evaluación real)

### Escenarios BDD (5 escenarios)

- ✅ `US-3.4.5-mis-materias-actividades.feature`
  - Ver materias de mi comisión
  - Actividad pendiente de responder
  - Actividad que todavía no abrió
  - Actividad ya finalizada por el Estudiante
  - Materia sin actividades visibles

### Tests de Frontend (10 tests nuevos)

- ✅ `MisMaterias.test.tsx` (3 tests) — "N pendiente", "Sin actividades disponibles", navegación
- ✅ `MisActividades.test.tsx` (4 tests) — los 3 badges y su navegación, listado vacío
- ✅ `FueraDePeriodo.test.tsx` (3 tests) — con navigation state, sin state, nota de "cierre"
- ✅ `router.test.tsx` — actualizado: la aserción sobre el placeholder de
  `/mis-actividades/materias` ahora verifica el heading real de `MisMaterias`

**Todos los tests pasando:** ✅ 575/575 unit backend, 227/227 integration backend, 138/138 BDD
— todas sin regresiones. 211/211 frontend sin regresiones (1 timeout intermitente preexistente
en `NuevaPreguntaOpcionMultiple.test.tsx` bajo `--coverage`, no reproduce en aislamiento, no
toca archivos de esta US).

---

## Archivos Creados/Modificados

### Código de Producción — Nuevo

- `src/identidad/use_cases/listar_materias_del_estudiante.py`
- `src/identidad/interface_adapters/controllers/estudiante_controller.py`
- `src/identidad/frameworks/api/estudiante_router.py`
- `src/actividad_evaluativa/entities/ports/evaluacion_estudiante_query_port.py`
- `src/actividad_evaluativa/frameworks/adapters/evaluacion_estudiante_query_repository.py`
- `src/actividad_evaluativa/use_cases/listar_actividades_visibles.py`
- `src/actividad_evaluativa/interface_adapters/controllers/actividades_estudiante_controller.py`
- `frontend/src/lib/identidad-estudiante-api.ts`
- `frontend/src/pages/MisMaterias.tsx`, `MisActividades.tsx`, `FueraDePeriodo.tsx`

### Código de Producción — Modificado

- `src/identidad/frameworks/dependencies.py`, `frameworks/api/schemas.py`
- `src/actividad_evaluativa/frameworks/api/actividades_router.py`, `frameworks/api/schemas.py`,
  `frameworks/dependencies.py`
- `src/app.py`
- `frontend/src/lib/actividad-evaluativa-api.ts`, `router.tsx`, `components/ui/badge.tsx`

### Tests

- `tests/unit/inc3/test_listar_materias_del_estudiante_use_case.py` (nuevo)
- `tests/unit/inc3/test_estudiante_controller.py` (nuevo)
- `tests/unit/inc3/test_listar_actividades_visibles_use_case.py` (nuevo)
- `tests/unit/inc3/test_actividades_estudiante_controller.py` (nuevo)
- `tests/integration/inc3/test_estudiante_materias_actividades_api_integration.py` (nuevo)
- `tests/features/inc3/US-3.4.5-mis-materias-actividades.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_4_5_steps.py` (nuevo)
- `tests/step_defs/inc3/_auth_headers.py` (modificado — `crear_estudiante_de_materia`)
- `frontend/src/pages/MisMaterias.test.tsx`, `MisActividades.test.tsx`,
  `FueraDePeriodo.test.tsx` (nuevos)
- `frontend/src/router.test.tsx` (modificado)

### Documentación / Infra

- `docs/specs/inc3/US-3.4.5.md` (preexistente, redactada antes de esta ejecución)
- `docs/plans/inc3/US-3.4.5-context.md`, `US-3.4.5-plan.md`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)
- `docs/reports/inc3/US-3.4.5-report.md` (este archivo)
- `quality/reports/inc3/US-3.4.5-quality.json`, `US-3.4.5-codeguard.json`, `US-3.4.5-pylint.json`,
  `US-3.4.5-cc.json`, `US-3.4.5-coverage.json`
- `pyproject.toml`/`uv.lock` — `vulture`, `codespell` agregados como dev dependencies

---

## Decisiones de diseño

1. **Puerto nuevo `EvaluacionEstudianteQueryPort`, no ensanchar `EvaluacionActivaQueryPort`** —
   propósitos distintos (evaluaciones finalizadas vs. no finalizadas), mismo criterio
   command/query que ya evitó CRITICAL de CBO en varias US previas.
2. **`existentes_finalizadas` verifica solo la existencia del evento `EvaluacionFinalizada`**,
   sin reconstruir el aggregate — `Finalizada` es terminal, evita replay innecesario en un
   endpoint de listado.
3. **3 estados de Badge, no 4** — corregido contra el prototipo aprobado (ver sección de
   corrección arriba); "cerrada sin rendir" no tiene badge propio en la grilla.
4. **`FueraDePeriodo.tsx` recibe datos por navigation state**, no por un fetch propio — no hay
   endpoint de detalle de actividad accesible al rol `estudiante`.
5. **Controller separado (`ActividadesEstudianteController`) en vez de sumar un método al
   controller de consulta docente** — mismo criterio de separación por actor que
   `BancosController` (`US-2.1.7`).

---

## Criterios de Aceptación (spec `docs/specs/inc3/US-3.4.5.md`)

- [x] El Estudiante ve una tarjeta por materia de su comisión
- [x] Una actividad dentro de su período vigente, sin evaluación finalizada, se ve con Badge
      "Pendiente de responder"
- [x] Una actividad con `fecha_apertura` futura se ve con Badge "Todavía no abrió"
- [x] Una actividad donde el Estudiante ya tiene una Evaluación Finalizada se ve con Badge
      "Finalizada — ver revisión"

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Continuar con `US-3.4.6` (Estudiante rinde su evaluación — responde, pausa y reanuda) —
      reemplaza el placeholder de `/mis-actividades/actividades/:actividadId/rendir`
- [ ] `US-3.4.7` (Estudiante finaliza su evaluación y ve la revisión completa) — reemplaza el
      placeholder de `/mis-actividades/evaluaciones/:evaluacionId/revision`

---

## Lecciones Aprendidas

- ⚠️ Diseñar el plan de Fase 2 mirando solo el texto de la spec, sin abrir primero el
  prototipo HTML aprobado, produjo un 4to estado de Badge que no existe en el diseño real —
  confirma el criterio ya documentado en memoria del proyecto: siempre chequear el prototipo
  antes de fijar contratos de API que dependan de estados de UI.
- ⚠️ Un `Edit` con `old_string` que hacía match parcial de una clase (`LoginResponse`) sin haber
  visto su última línea (`expira_en`) la cortó a la mitad. Antes de anclar un `old_string` sobre
  el final de una clase, confirmar que el `Read` previo mostró la clase completa, no solo hasta
  donde alcanzó el `limit`.
- 💡 `vulture`/`codespell` ausentes del entorno hacían que `codeguard --analysis-type full`
  reportara "not installed" como error silencioso en vez de un hallazgo real — agregarlos como
  dev dependencies deja el gate de Fase 7 con señal real en vez de ruido de infraestructura.
- 💡 El patrón de test de integración con `Comision.materia_id` aleatorio (suficiente para
  `IniciarEvaluacion`) no sirve para un endpoint que resuelve la materia vía `MateriaPort` —
  necesitó una variante del helper con una materia real creada por API.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-31
