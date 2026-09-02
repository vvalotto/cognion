# Plan de Implementación: US-3.2.1 - Estudiante confirma una respuesta (persistencia atómica)

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Actividad Evaluativa
**Estado:** ✅ COMPLETADO — 2026-08-27

## Métricas de Tiempo

Tracking real vía `tracker_cli.py` (`.claude/tracking/US-3.2.1-tracking.json`), sin comparación
contra estimaciones humanas (PRIN-001) — ~19 min efectivos hasta el cierre de Fase 7, 9/9 tareas
de Fase 3 completadas. La Fase 5 (Tests de Integración) no quedó registrada en el tracker —
se arrancó a escribir los tests directamente sin ejecutar `start-phase 5` antes; el trabajo en
sí se hizo completo (8 tests de integración, todos en verde) y no requirió reabrir ninguna fase
anterior.

| Fase | Segundos |
|---|---|
| 0 Validación de Contexto | 49 |
| 1 Escenarios BDD | 61 |
| 2 Plan de Implementación | 92 |
| 3 Implementación | 365 |
| 4 Tests Unitarios | 142 |
| 5 Tests de Integración | (no registrado — ver nota arriba) |
| 6 Validación BDD | 287 |
| 7 Quality Gates | 177 |

## Lecciones Aprendidas

- 💡 `Evaluacion.reconstruir` pasó de leer solo `eventos[0]` a un replay real acumulando
  `Respuesta` desde `eventos[1:]` — primer caso del BC donde un aggregate necesita reproducir
  más de un evento de su propio stream. El cambio quedó contenido en un único método, sin tocar
  la forma en que `US-3.1.3` ya lo usaba.
- 💡 Separar `validar_para_registrar_respuesta` (valida invariantes + calcula `numero_intento`)
  de la construcción de la `Respuesta` en sí evitó una vuelta rara de "construir con
  `es_correcta` provisorio y reconstruir con el real" — el Use Case es quien conoce
  `es_correcta` (consulta a Banco de Preguntas), la Entity no necesita saberlo para validar.
- 🐛 Dos de los 8 escenarios BDD (`Rechazo sobre evaluación suspendida`/`finalizada`) no se
  pudieron implementar end-to-end vía HTTP porque `SuspenderEvaluacion`/`FinalizarEvaluacion`
  todavía no existen (llegan con `US-3.2.2`/`US-3.2.3`) — se implementaron a nivel de dominio
  (`Evaluacion.validar_para_registrar_respuesta` directo), detectado recién al escribir los
  steps en Fase 6, no en Fase 1 al redactar el `.feature`. Vale la pena chequear en Fase 1 si
  todos los `Given` de un escenario son alcanzables con lo que la Iteración ya tiene construido.
- 🐛 El escenario "Rechazo fuera del período vigente" tampoco es alcanzable con una actividad
  ya cerrada desde el vamos (`IniciarEvaluacion` la rechazaría antes de llegar a
  `RegistrarRespuesta`) — se resolvió con una ventana de vigencia muy corta (~1.5s) y un `sleep`
  real antes de confirmar la respuesta, en vez de necesitar el endpoint de modificación de
  período de `US-3.3.1` (Iteración 3, todavía no implementado).
- ✅ El mismo patrón de CRITICAL de CBO de Incremento 2 no se repitió: `EvaluacionesController`
  con 2 Use Cases inyectados quedó lejos del umbral — DesignReviewer en pre-push (a correr antes
  del PR) es quien confirma esto en definitiva, mismo criterio que `US-3.1.2`/`US-3.1.3`.
- ✅ `codeguard` detectó una línea >100 caracteres en `entities/errors.py` (docstring de
  `EvaluacionNoExiste`) — tercera vez que aparece este mismo tipo de hallazgo en el BC
  (`US-3.1.2`, `US-3.1.3`), confirma que el límite real del proyecto es 100, no el default
  genérico de la herramienta.

## Decisiones de diseño a confirmar antes de codear

1. **`Evaluacion.reconstruir` pasa de "un solo evento" a replay real.** Hasta `US-3.1.3` el
   stream de `Evaluacion` solo podía tener `EvaluacionIniciada` (el primer y único evento).
   Esta US agrega `RespuestaRegistrada` como evento repetible del mismo stream — `reconstruir`
   deja de leer solo `eventos[0]` y pasa a: tomar el primer evento (`EvaluacionIniciada`) para
   los campos base, y aplicar cada evento siguiente (`RespuestaRegistrada`) agregando una
   `Respuesta` a `respuestas`. Es un cambio en un método ya existente, no un artefacto nuevo —
   no está en la tabla de la spec, pero es inevitable para que `US-3.2.1` pueda leer el estado
   acumulado de una `Evaluacion` con respuestas previas (INV-AE-08, contar intentos).
2. **`expected_sequence_number` de `append` = `len(eventos_evaluacion)` cargado, no `0`.**
   `US-3.1.3` siempre apendeaba sobre un stream vacío (`0`). Esta US necesita la cantidad real
   de eventos ya persistidos del stream (`EvaluacionIniciada` + `RespuestaRegistrada` previas)
   para que la concurrencia optimista (`ADR-002`, INV-AE-09) rechace un doble submit del mismo
   estudiante reintentando la misma confirmación.
3. **`evaluar_correccion` no expone tipos de Banco de Preguntas fuera de su BC.** El puerto
   recibe `contenido: dict` (la forma ya validada por el schema Pydantic del endpoint) y
   devuelve `bool` — el adapter in-process es el único lugar que conoce
   `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`. Comparación: opción
   múltiple compara `contenido["opcion_indice"]` contra la posición del `Opcion` con
   `es_correcta=True` en `pregunta.opciones`; verdadero/falso compara `contenido["valor"]`
   contra `pregunta.respuesta_correcta`.
4. **`obtener_por_id` devolviendo `None` es defensivo, no un caso de negocio esperado.**
   INV-AE-07 ya garantiza que `pregunta_id` pertenece al set `preguntas_asignadas`, sampleado
   desde preguntas que existían al `IniciarEvaluacion`. Si igual devuelve `None` (ej. la
   pregunta fue borrada físicamente, que el proyecto no hace — solo baja lógica), se relanza
   `PreguntaNoAsignada` en vez de agregar un error nuevo solo para un caso que no debería
   ocurrir en la práctica — avisar si preferís tratarlo distinto.
5. **`numero_intento` se calcula contando `respuestas` ya cargadas por `pregunta_id`, no un
   contador separado.** `len([r for r in evaluacion.respuestas if r.pregunta_id == pregunta_id]) + 1`
   — sin estado adicional, consistente con INV-AE-08 (mismo conteo que valida el límite).
6. **`EvaluacionesController` recibe un segundo Use Case por constructor** (mismo patrón que
   `PreguntasController`/`CuentasController` en Incremento 2) — con 2 dependencias todavía lejos
   del umbral de CBO que disparó el patrón recurrente de CRITICAL en pre-push.

## Componentes a Implementar

### 1. Entities

- [x] `src/actividad_evaluativa/entities/evaluacion.py`
  - `Respuesta` (dataclass, Entity — `id` propio): `id: UUID`, `pregunta_id: UUID`,
    `numero_intento: int`, `contenido: dict`, `es_correcta: bool`, `confirmada_en: datetime`.
  - `Evaluacion` gana el campo `respuestas: list[Respuesta] = field(default_factory=list)`.
  - `validar_para_registrar_respuesta(pregunta_id, cantidad_intentos_permitidos) -> int`
    (método de instancia, ajustado en Fase 3 — más simple que el `staticmethod` originalmente
    previsto) — valida INV-AE-07 (pertenencia al set), INV-AE-08 (intentos no agotados) e
    INV-AE-12 (`estado == EN_CURSO`) sobre el `Evaluacion` ya cargado, y devuelve el
    `numero_intento` de la nueva `Respuesta`. No construye la `Respuesta` en sí — eso lo hace
    el Use Case, que es quien conoce `es_correcta` (consulta a Banco de Preguntas, INV-AE-10).
  - `reconstruir(eventos)` reescrito (decisión 1): primer evento arma los campos base
    (idéntico a antes), eventos siguientes de tipo `RespuestaRegistrada` se mapean a `Respuesta`
    y se acumulan en `respuestas`.

- [x] `src/actividad_evaluativa/entities/eventos.py` (agrega al existente)
  - `RespuestaRegistrada`: `respuesta_id: UUID`, `evaluacion_id: UUID`, `pregunta_id: UUID`,
    `numero_intento: int`, `contenido: dict`, `es_correcta: bool`, `ocurrido_en: datetime`.

- [x] `src/actividad_evaluativa/entities/errors.py` (agrega al existente)
  - `EvaluacionNoExiste(evaluacion_id)`.
  - `PreguntaNoAsignada(evaluacion_id, pregunta_id)`.
  - `IntentosAgotados(pregunta_id, cantidad_intentos_permitidos)`.
  - `EvaluacionSuspendida(evaluacion_id)`.
  - `EvaluacionYaFinalizada(evaluacion_id)`.

- [x] `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` (agrega al existente)
  - Nuevo método abstracto `async def evaluar_correccion(self, pregunta_id: UUID, contenido: dict) -> bool`.

### 2. Use Cases

- [x] `src/actividad_evaluativa/use_cases/registrar_respuesta.py` (nuevo)
  - `RegistrarRespuestaUseCase(pregunta_consulta: PreguntaConsultaPort, event_store: EventStorePort)`
  - `async def execute(evaluacion_id, estudiante_id, pregunta_id, contenido) -> Respuesta`:
    1. Carga el stream `"Evaluacion"` de `evaluacion_id`; `EvaluacionNoExiste` si viene vacío.
    2. Reconstruye `Evaluacion` (`reconstruir`, decisión 1); `EvaluacionNoExiste` también si
       `evaluacion.estudiante_id != estudiante_id` (no es del estudiante autenticado — mismo
       código de error que "no existe", no se filtra si la evaluación es de otro).
    3. Carga el stream `"ActividadEvaluativaPeriodoAbierto"` de `evaluacion.actividad_id`
       (siempre existe — invariante de integridad ya garantizada desde `US-3.1.3`) y valida
       `FueraDePeriodo` igual que `IniciarEvaluacionUseCase` (mismo cálculo, período vigente).
    4. `Evaluacion.registrar_respuesta(...)` valida INV-AE-07/08/12 y levanta
       `PreguntaNoAsignada`/`IntentosAgotados`/`EvaluacionSuspendida`/`EvaluacionYaFinalizada`
       según corresponda (decisión 3 del `IntentosAgotados`: se calcula antes de pedir la
       corrección, para no consultar Banco de Preguntas si la respuesta se va a rechazar).
    5. `es_correcta = await self._pregunta_consulta.evaluar_correccion(pregunta_id, contenido)`
       (INV-AE-10, se calcula recién acá, con la pregunta ya validada como asignada).
    6. Arma `RespuestaRegistrada`, `event_store.append("Evaluacion", evaluacion_id, len(eventos_evaluacion), [...])`
       (decisión 2 — protege contra doble submit).
    7. Devuelve la `Respuesta` creada.

### 3. Interface Adapters

- [x] `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py`
  (agrega al existente)
  - Constructor gana `registrar_respuesta: RegistrarRespuestaUseCase` (decisión 6).
  - Método nuevo `registrar_respuesta(evaluacion_id, estudiante_id, pregunta_id, contenido)` —
    delega tal cual al Use Case, mismo patrón que `iniciar_evaluacion`.

### 4. Frameworks

- [x] `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py`
  (agrega al existente)
  - `evaluar_correccion(pregunta_id, contenido)`: `pregunta = await self._pregunta_repositorio.obtener_por_id(pregunta_id)`;
    `PreguntaNoAsignada` defensivo si `None` (decisión 4); si
    `isinstance(pregunta, PreguntaPlantillaOpcionMultiple)` compara `contenido["opcion_indice"]`
    contra el índice del `Opcion` correcto; si `PreguntaPlantillaVerdaderoFalso` compara
    `contenido["valor"] == pregunta.respuesta_correcta` (decisión 3).

- [x] `src/actividad_evaluativa/frameworks/api/schemas.py` (agrega al existente)
  - `RegistrarRespuestaRequest`: `pregunta_id: UUID`, `contenido: dict[str, Any]`.
  - `RespuestaResponse`: `id`, `pregunta_id`, `numero_intento`, `confirmada_en` — **sin**
    `es_correcta` ni `contenido` en la respuesta (hot spot "sin feedback inmediato", el
    estudiante no debe poder inferir si acertó desde la respuesta HTTP).

- [x] `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` (agrega al existente)
  - `POST /evaluaciones/{evaluacion_id}/respuestas`, `dependencies` exige rol estudiante;
    `estudiante_id` sale del JWT. `try/except`: `EvaluacionNoExiste`/`PreguntaNoAsignada` → 404,
    `IntentosAgotados`/`EvaluacionSuspendida`/`EvaluacionYaFinalizada`/`FueraDePeriodo` → 422.
    Devuelve `RespuestaResponse`, `status_code=201` (a diferencia de `POST /evaluaciones`, cada
    llamada exitosa crea una `Respuesta` nueva — no es idempotente).

- [x] `src/actividad_evaluativa/frameworks/dependencies.py` (agrega al existente)
  - `get_evaluaciones_controller(session)` arma también `RegistrarRespuestaUseCase` con el
    mismo `PreguntaConsultaPortInProcess`/`SQLAlchemyEventStore` ya instanciados para
    `IniciarEvaluacionUseCase`, e inyecta ambos Use Cases en `EvaluacionesController`.

### 5. Integración

- [x] Ninguna — el router ya está registrado en `src/app.py` desde `US-3.1.3`; esta US solo
  agrega un endpoint al `APIRouter` existente.

**Estado:** 9/9 tareas completadas
