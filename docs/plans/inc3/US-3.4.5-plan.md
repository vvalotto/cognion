# Plan de Implementación: US-3.4.5 — Estudiante ve sus materias y las actividades disponibles

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-31

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 26s |
| 1 — Escenarios BDD | 32s |
| 2 — Plan de Implementación | 33min 41s |
| 3 — Implementación Guiada por Tareas | 17min 32s |
| 4 — Tests Unitarios | 2min 31s |
| 5 — Tests de Integración | 7min 24s |
| 6 — Validación BDD | 4min 44s |
| 7 — Quality Gates | 28min 31s |
| **Total** | **97min 35s** |

## Lecciones Aprendidas

- ⚠️ Contradicción real detectada entre el plan aprobado en Fase 2 (4 estados de Badge) y el
  prototipo HTML aprobado (3 estados) — el plan se diseñó sobre el texto de la spec sin
  chequear el prototipo primero. Corregido con Víctor antes de tocar frontend; el backend ya
  escrito con el 4to estado se revirtió sin costo (todavía no tenía tests). Confirma el
  criterio ya documentado en memoria del proyecto: el prototipo manda sobre el texto escrito.
- ⚠️ Un `Edit` propio cortó a la mitad la clase `LoginResponse` en `schemas.py` (el campo
  `expira_en` quedó huérfano en la clase nueva) porque el `Read` previo truncó el archivo justo
  antes de ese campo. Detectado por `mypy` en la verificación de Fase 3, no en el momento de
  editar — leer rangos completos de clase antes de anclar un `old_string` de Edit, no cortar en
  el medio de un bloque sin haber visto dónde termina.
- 💡 `vulture`/`codespell` no estaban instalados pese a que `codeguard --analysis-type full`
  los requiere para los 9 checks — quedaban "not installed" contando como error silencioso.
  Agregados como dev dependencies del proyecto (`uv add --dev`).
- 💡 Reutilizar el patrón de test de integración existente (`_crear_estudiante` con
  `materia_id` aleatorio) no alcanza para esta US — el endpoint nuevo resuelve la materia via
  `MateriaPort`, necesita un id real de materia creada por API. Se agregó una variante del
  helper (`crear_estudiante_de_materia`) en vez de forzar el existente.

## Decisión de diseño (Fase 2)

`existe_finalizada` **no** se agrega a `EvaluacionActivaQueryPort` (`US-3.2.4`) — ese puerto
tiene un propósito específico ("evaluaciones NO finalizadas" para el `VerificadorDeVencimientos`)
y ensancharlo repetiría el problema de CBO ya visto en `US-2.1.2`/`US-2.1.5`/`US-2.1.6`. Se crea
un puerto de consulta nuevo y separado, `EvaluacionEstudianteQueryPort`, con un único método:

```python
async def existentes_finalizadas(self, evaluacion_ids: list[UUID]) -> set[UUID]: ...
```

Implementación: `Evaluacion.id_para(actividad_id, estudiante_id)` (ya usado por
`IniciarEvaluacionUseCase`) es determinístico — no hace falta replay completo del aggregate para
saber si está `Finalizada`; alcanza con una consulta `SELECT DISTINCT aggregate_id FROM events
WHERE aggregate_id IN (...) AND event_type = 'EvaluacionFinalizada'` (un estado terminal no
puede revertirse). Batch por materia, no N+1.

**Corrección post-implementación (contradicción detectada contra el prototipo aprobado):** el
diseño original de esta sección proponía un 4to estado `"cerrada_sin_rendir"`. El prototipo
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html` (`#est-actividades`) solo
define **3 badges** — no hay uno para "cerrada sin rendir" en la grilla. Corregido con Víctor:
el estado por-estudiante ("Badge") se calcula en el use case combinando:
- `evaluacion_id` finalizado → `"finalizada"`
- sin evaluación + `fecha_apertura` futura → `"todavia_no_abrio"`
- cualquier otro caso (vigente, cerrada sin rendir, o evaluación `EnCurso`/`Suspendida`) →
  `"pendiente"` — mismo criterio que el invariante de la spec: `EnCurso` y `Suspendida` no se
  distinguen en esta grilla, y una actividad cerrada sin evaluación tampoco tiene badge propio
  (el 422 de `FueraDePeriodo` al intentar iniciar, `US-3.4.6`, resuelve ese caso recién ahí).

`"todavia_no_abrio"` navega a la pantalla nueva `FueraDePeriodo.tsx`; `"pendiente"` navega al
placeholder existente de `.../actividades/:actividadId/rendir` (`US-3.4.6` lo reemplaza después);
`"finalizada"` navega al placeholder existente de `.../evaluaciones/:evaluacionId/revision`
(`US-3.4.7` lo reemplaza después) — requiere resolver el `evaluacion_id` de esa evaluación
finalizada, así que el use case devuelve también ese id cuando el estado es `"finalizada"`.

## Componentes a Implementar

### 1. BC Identidad — "mis materias"

- [x] `src/identidad/frameworks/dependencies.py`
  - Agregar `require_estudiante = require_rol([TipoPerfil.ESTUDIANTE], get_current_user)`
    (mismo patrón que `require_docente`/`require_administrador`; hoy solo existe en Actividad
    Evaluativa)
- [x] `src/identidad/use_cases/listar_materias_del_estudiante.py`
  - `ListarMateriasDelEstudianteUseCase.execute(estudiante_id: UUID) -> list[MateriaEstudianteResumen]`
  - Resuelve `Usuario.perfil.comision_id` → `Comision.materia_id` → `MateriaPort.obtener()`
    (reutiliza el puerto de `US-2.1.2`, sin puerto nuevo)
- [x] `src/identidad/interface_adapters/controllers/estudiante_controller.py`
  - `EstudianteController.listar_mis_materias(estudiante_id)` — adapta el resultado del use case
    a la respuesta HTTP
- [x] `src/identidad/frameworks/api/estudiante_router.py`
  - `GET /identidad/estudiante/materias` — rol `estudiante` (`require_estudiante`), usa el
    `usuario_id` del token vía `get_current_user`
- [x] Registrar `estudiante_router` en el composition root de Identidad y en el entrypoint de la
  app (donde ya se incluyen `comisiones_router`, etc.)

### 2. BC Actividad Evaluativa — "actividades visibles con estado"

- [x] `src/actividad_evaluativa/entities/ports/evaluacion_estudiante_query_port.py`
  - `EvaluacionEstudianteQueryPort.existentes_finalizadas(evaluacion_ids: list[UUID]) -> set[UUID]`
- [x] `src/actividad_evaluativa/frameworks/adapters/evaluacion_estudiante_query_repository.py`
  - `SQLAlchemyEvaluacionEstudianteQueryRepository` — implementa el puerto anterior sobre la
    tabla `events`
- [x] `src/actividad_evaluativa/use_cases/listar_actividades_visibles.py`
  - `ListarActividadesVisiblesUseCase.execute(materia_id, estudiante_id) -> list[ActividadVisible]`
  - Reutiliza `ActividadQueryPort.listar_por_materia` (`US-3.4.2`) para la base, calcula
    `evaluacion_id` por actividad, consulta el puerto nuevo en batch, aplica la lógica de estado
    de la sección "Decisión de diseño"
- [x] `src/actividad_evaluativa/interface_adapters/controllers/actividades_estudiante_controller.py`
  - `ActividadesEstudianteController` — separado del controller de consulta existente del lado
    docente, mismo criterio de separación command/query que evitó el CRITICAL de CBO en
    `US-2.1.7`/`US-2.2.2`
- [x] `src/actividad_evaluativa/frameworks/api/actividades_router.py`
  - `GET /actividades/mis-actividades?materia_id={id}`, rol `estudiante` (`require_estudiante`,
    ya existente en este BC) — registrada antes de `/{actividad_id}` para no chocar con esa ruta
- [x] Registrar en el composition root de Actividad Evaluativa

### 3. Frontend

- [x] `frontend/src/lib/identidad-estudiante-api.ts` (nuevo, cliente API tipado)
  - `listarMisMaterias(): Promise<MateriaEstudianteResponse[]>`
- [x] `frontend/src/lib/actividad-evaluativa-api.ts`
  - Agregado `listarActividadesVisibles(materiaId): Promise<ActividadVisibleResponse[]>` +
    tipo `EstadoVisible = "pendiente" | "todavia_no_abrio" | "finalizada"` (3 estados, corregido
    contra el prototipo — ver "Corrección post-implementación")
- [x] `frontend/src/pages/MisMaterias.tsx` (nueva — reemplaza el placeholder de
  `/mis-actividades/materias`)
  - Tarjeta por materia con `Badge` resumen ("N pendiente" / "Sin actividades disponibles")
- [x] `frontend/src/pages/MisActividades.tsx` (nueva — reemplaza el placeholder de
  `/mis-actividades/materias/:materiaId/actividades`)
  - Tarjeta por actividad con `Badge` de estado; navega según el estado (ver Decisión de diseño)
- [x] `frontend/src/pages/FueraDePeriodo.tsx` (nueva)
  - Estado "todavía no abrió" (`#est-fuera-periodo`); recibe título/fecha por navigation state
    desde `MisActividades` (no hay endpoint de detalle de actividad accesible a `estudiante`)

### 4. Integración

- [x] `frontend/src/router.tsx`
  - Reemplazado `ActividadEvaluativaPlaceholder` por `MisMaterias`/`MisActividades` en las 2
    rutas ya existentes desde `US-3.4.1`
  - Agregada ruta nueva `/mis-actividades/:actividadId/fuera-de-periodo` → `FueraDePeriodo`
    (rol `estudiante`, mismo patrón `RequireRole`)
- [x] `frontend/src/components/ui/badge.tsx` — 3 variantes nuevas (`visible-pendiente`,
  `visible-todavia-no-abrio`, `visible-finalizada`)

### 5. Tests frontend (Fase 7, agregado no previsto en el plan original)

- [x] `frontend/src/pages/MisMaterias.test.tsx`, `MisActividades.test.tsx`,
  `FueraDePeriodo.test.tsx` — 10 tests nuevos (Vitest + Testing Library)
- [x] `frontend/src/router.test.tsx` — actualizado: la aserción sobre el placeholder de
  `/mis-actividades/materias` ahora verifica el heading real de `MisMaterias`

**Estado:** 19/19 tareas completadas
