# Plan de Implementación: US-3.1.3 - Estudiante inicia su evaluación (set aleatorio fijo)

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Actividad Evaluativa
**Estado:** ✅ COMPLETADO — 2026-08-26

## Métricas de Tiempo

Tracking real vía `tracker_cli.py` (`.claude/tracking/US-3.1.3-tracking.json`), sin comparación
contra estimaciones humanas (PRIN-001) — ~20 min efectivos hasta el cierre de Fase 7, 13/13
tareas de Fase 3 completadas.

| Fase | Segundos |
|---|---|
| 0 Validación de Contexto | 45 |
| 1 Escenarios BDD | 37 |
| 2 Plan de Implementación | 219 |
| 3 Implementación | 298 |
| 4 Tests Unitarios | 93 |
| 5 Tests de Integración | 130 |
| 6 Validación BDD | 179 |
| 7 Quality Gates | 162 |

## Lecciones Aprendidas

- 💡 El event store solo indexa por `(aggregate_type, aggregate_id)` — sin read model todavío
  para consultar `Evaluacion` por su clave natural `(actividad_id, estudiante_id)`. Derivar
  `Evaluacion.id` determinísticamente (`uuid5`) resolvió la idempotencia de INV-AE-06 sin
  ensanchar ningún puerto ni adelantar el read model de `US-3.2.4` — mismo criterio de "no
  ensanchar puertos existentes" que ya se venía aplicando desde `US-2.1.9`.
- 💡 Primera vez que este BC necesita **leer** su propio event store (`US-3.1.1`/`US-3.1.2`
  solo escribían). El replay de `Evaluacion` quedó como un método `reconstruir(eventos)` puro
  en `entities/`, reutilizable por `US-3.2.*`. El de `ActividadEvaluativaPeriodoAbierto` se
  parseó inline en el Use Case (solo tiene un evento posible hasta `US-3.3.1`) — sin agregar un
  método genérico que ningún otro llamador necesita todavía.
- ✅ `docente_headers()`/`admin_headers()` (fixtures ya existentes) emiten JWT con un
  `usuario_id` aleatorio sin fila real en BD — suficiente para endpoints que solo chequean el
  rol del claim. `EstudianteConsultaPort` sí valida existencia real contra BC Identidad, así que
  los tests de integración/BDD de esta US necesitaron crear un `Usuario` real (+ `Comision`) por
  cada estudiante — no se pudo reutilizar el patrón liviano de `docente_headers`.
- 🐛 El `.feature` generado en Fase 1 tenía un step partido en dos líneas (Gherkin no soporta
  continuación de línea en un step) — no lo detectó la revisión humana de Fase 1, recién se vio
  al ejecutar Fase 6. Corregido ahí mismo, evidencia de que vale la pena correr pytest-bdd apenas
  se aprueba el `.feature`, no solo al final.
- ✅ `codeguard` detectó una línea de import >100 caracteres en `src/app.py` (import nuevo del
  router) — mismo tipo de hallazgo que en `US-3.1.2` (docstrings largos), confirma que el límite
  real del proyecto es 100, no el default genérico.

## Decisiones de diseño a confirmar antes de codear

1. **Identidad determinística del stream `Evaluacion`.** `EventStorePort.load` solo busca por
   `(aggregate_type, aggregate_id)` exacto — no hay query por payload ni read model todavía
   (llegan en Iteración 2, `US-3.2.4`). Para resolver la idempotencia de INV-AE-06
   (`IniciarEvaluacion` sobre un par `(actividad_id, estudiante_id)` que ya tiene `Evaluacion`)
   sin ensanchar `EventStorePort` ni crear un read model adelantado, `Evaluacion.id` se deriva
   determinísticamente con `uuid5(NAMESPACE, f"{actividad_id}:{estudiante_id}")`. Buscar ese id
   en el stream `"Evaluacion"` reemplaza cualquier consulta adicional: si ya tiene eventos, es
   la `Evaluacion` existente; si no, es alta nueva. Mismo criterio que la spec pide ("no
   ensanchar puertos existentes", ya aplicado en `US-2.1.9`).
2. **Dos errores no listados explícitamente en la tabla "Artefactos a modificar" de la spec**
   (que solo menciona agregar `FueraDePeriodo` a `errors.py`), pero sí exigidos por la
   descripción de comportamiento y por `BC-actividad-evaluativa-modelo.md` línea 178 (tabla de
   comandos, columna de errores de `IniciarEvaluacion`): `ActividadNoExiste` (el
   `actividad_id` no corresponde a ninguna `ActividadEvaluativaPeriodoAbierto`) y
   `EstudianteNoExiste` (el `estudiante_id` no existe o no tiene rol Estudiante en BC
   Identidad — chequeo vía el puerto nuevo `EstudianteConsultaPort` que la propia spec sí pide
   crear e implementar). Sin estos dos, el Use Case no tiene nada que hacer con lo que devuelve
   `EstudianteConsultaPort`, y un `actividad_id` inexistente rompería con un error no
   controlado en vez de un 404 de dominio. Se agregan por coherencia con el modelo aprobado —
   avisar si preferís omitirlos.
3. **Endpoint idempotente → 200 OK siempre**, tanto en la creación como en la reconexión (a
   diferencia de `POST /actividades`, que es `201` porque no es idempotente). Evita inventar un
   código de estado distinto para el camino de reconexión que la spec no pide distinguir.

## Componentes a Implementar

### 1. Entities

- [x] `src/actividad_evaluativa/entities/evaluacion.py`
  - `EstadoEvaluacion` (Enum str): `EN_CURSO = "EnCurso"`, `SUSPENDIDA = "Suspendida"`,
    `FINALIZADA = "Finalizada"` — los tres valores ya están en el modelo aprobado
    (`BC-actividad-evaluativa-modelo.md` §5); esta US solo produce `EN_CURSO`.
  - `PreguntaAsignada` (frozen dataclass, VO): `pregunta_id: UUID`, `orden: int`.
  - `Evaluacion` (dataclass): `id`, `actividad_id`, `estudiante_id`,
    `preguntas_asignadas: list[PreguntaAsignada]`, `estado: EstadoEvaluacion`,
    `iniciada_en: datetime`.
    - `staticmethod id_para(actividad_id, estudiante_id) -> UUID` — uuid5 determinístico
      (decisión 1).
    - `staticmethod crear(actividad_id, estudiante_id, preguntas_asignadas) -> Evaluacion` —
      arma con `id = id_para(...)`, `estado = EN_CURSO`, `iniciada_en = ahora()`. Sin
      validación propia — INV-AE-05/06 y `FueraDePeriodo` son responsabilidad del Use Case
      (necesitan el event store y `ActividadEvaluativaPeriodoAbierto`, no datos del aggregate
      en sí).

- [x] `src/actividad_evaluativa/entities/eventos.py` (agrega al existente)
  - `EvaluacionIniciada`: `evaluacion_id`, `actividad_id`, `estudiante_id`,
    `preguntas_asignadas: list[PreguntaAsignada]`, `ocurrido_en`.

- [x] `src/actividad_evaluativa/entities/errors.py` (agrega al existente)
  - `FueraDePeriodo(actividad_id, ahora, fecha_apertura, fecha_cierre)` — spec.
  - `ActividadNoExiste(actividad_id)` — decisión 2.
  - `EstudianteNoExiste(estudiante_id)` — decisión 2.

- [x] `src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py` (nuevo)
  - `EstudianteConsultaPort(ABC)` — `async def existe(self, estudiante_id: UUID) -> bool`:
    valida existencia y rol Estudiante en una sola operación (mismo nivel de abstracción que
    `MateriaConsultaPort.obtener`, pero acá no hace falta traer datos del estudiante, solo
    saber si es válido).

- [x] `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` (agrega al existente)
  - Nuevo método abstracto `async def listar_ids_activas_por_materia(self, materia_id: UUID) -> list[UUID]`
    — sampleo aleatorio (RF-12) necesita los ids concretos, no solo el conteo que ya provee
    `contar_activas_por_materia`.

### 2. Use Cases

- [x] `src/actividad_evaluativa/use_cases/iniciar_evaluacion.py`
  - `IniciarEvaluacionUseCase(estudiante_consulta, pregunta_consulta, event_store)`
  - `async def execute(actividad_id, estudiante_id) -> tuple[Evaluacion, bool]` (el `bool`
    indica si se creó en esta llamada o se retomó una existente — lo usa el Controller/Router
    solo para logging/response, no cambia el status code, decisión 3):
    1. `EstudianteNoExiste` si `not await estudiante_consulta.existe(estudiante_id)`.
    2. Carga el stream `"ActividadEvaluativaPeriodoAbierto"` de `actividad_id`; `ActividadNoExiste`
       si viene vacío. Reconstruye los campos relevantes leyendo el único evento
       `ActividadEvaluativaCreada` de su payload (no hace falta un mecanismo de replay
       genérico todavía — `PeriodoDisponibilidadModificado`/`ActividadEvaluativaCerrada` llegan
       recién en Iteración 3, `US-3.3.1`/`US-3.3.2`).
    3. `FueraDePeriodo` si `ahora` no está en `[fecha_apertura, fecha_cierre]` vigente.
    4. `evaluacion_id = Evaluacion.id_para(actividad_id, estudiante_id)`; carga el stream
       `"Evaluacion"` de ese id.
       - Si trae eventos: reconstruye `Evaluacion` desde el único `EvaluacionIniciada`
         existente (INV-AE-05, no vuelve a samplear) y devuelve `(evaluacion, False)`.
       - Si viene vacío: `random.sample(await pregunta_consulta.listar_ids_activas_por_materia(materia_id), cantidad_preguntas)`,
         arma `preguntas_asignadas` (orden = posición en el sample), crea la `Evaluacion` con
         `Evaluacion.crear(...)`, emite `EvaluacionIniciada`, hace `event_store.append("Evaluacion", evaluacion_id, 0, [...])`
         y devuelve `(evaluacion, True)`.

### 3. Interface Adapters

- [x] `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py`
  - `EvaluacionesController(iniciar_evaluacion: IniciarEvaluacionUseCase)` — delega
    `iniciar_evaluacion(actividad_id, estudiante_id)` al Use Case, mismo patrón que
    `ActividadesController`.

### 4. Frameworks

- [x] `src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py`
  - `EstudianteConsultaPortInProcess(session)` implementa `EstudianteConsultaPort` llamando a
    `SQLAlchemyUsuarioRepository(session).obtener_por_id(estudiante_id)` (BC Identidad) y
    comprobando `isinstance(usuario.perfil, Estudiante)` — mismo criterio de acoplamiento
    consciente documentado en `materia_consulta_port_in_process.py` (`ADR-006`).

- [x] `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
  (agrega al existente)
  - `listar_ids_activas_por_materia`: resuelve el `Banco` de la materia (igual que
    `contar_activas_por_materia`) y devuelve `[p.id for p in resultado.preguntas]` de
    `pregunta_repositorio.filtrar(banco.id)`.

- [x] `src/actividad_evaluativa/frameworks/api/schemas.py` (agrega al existente)
  - `IniciarEvaluacionRequest`: `actividad_id: UUID`.
  - `PreguntaAsignadaResponse`: `pregunta_id: UUID`, `orden: int`.
  - `EvaluacionResponse`: `id`, `actividad_id`, `estudiante_id`,
    `preguntas_asignadas: list[PreguntaAsignadaResponse]`, `estado: str`, `iniciada_en: datetime`.

- [x] `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` (nuevo)
  - `POST /evaluaciones`, `dependencies` exige rol estudiante; `estudiante_id` sale del JWT
    (`usuario.usuario_id`), no del body — el estudiante nunca inicia la evaluación de otro.
    `try/except`: `ActividadNoExiste`/`EstudianteNoExiste` → 404, `FueraDePeriodo` → 422.
    Devuelve `EvaluacionResponse`, `status_code=200` (decisión 3).

- [x] `src/actividad_evaluativa/frameworks/dependencies.py` (agrega al existente)
  - `require_estudiante = require_rol([TipoPerfil.ESTUDIANTE], get_current_user)`.
  - `get_evaluaciones_controller(session)` arma `EstudianteConsultaPortInProcess`,
    `PreguntaConsultaPortInProcess`, `SQLAlchemyEventStore` y
    `IniciarEvaluacionUseCase`, envueltos en `EvaluacionesController`.

### 5. Integración

- [x] `src/app.py` — importa `evaluaciones_router` y `app.include_router(evaluaciones_router)`,
  mismo lugar que `actividades_router`.

**Estado:** 13/13 tareas completadas
