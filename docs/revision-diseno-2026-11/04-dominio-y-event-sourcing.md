# 04 · Modelo de dominio y event sourcing

> Pregunta: ¿los agregados, los eventos y los invariantes están bien diseñados?

## Qué se miró

- El agregado [`ActividadEvaluativaEnVivo`](../../src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py), `ParticipacionEnVivo` y `Evaluacion`.
- El puerto y la implementación del event store ([`sqlalchemy_event_store.py`](../../src/actividad_evaluativa/frameworks/event_store/sqlalchemy_event_store.py)).
- El caso de uso [`responder_pregunta_en_vivo.py`](../../src/actividad_evaluativa/use_cases/responder_pregunta_en_vivo.py) completo.
- Conteos en `entities/` y `use_cases/`: armado y lectura de payloads, `dict[str, Any]`, `isinstance`, `datetime.now`, `uuid4`.

## Fortalezas

- **Agregados chicos y con frontera pensada.** La sesión no crece con los alumnos: las respuestas viven en `ParticipacionEnVivo`, un stream por estudiante. Eso es lo que permite el p95 de 79 ms medido.
- **Invariantes con nombre.** Cada regla tiene identificador (`INV-AEV-07`, `INV-BP-01`) citado en el código y en el modelo del contexto. Es trazabilidad real entre diseño y código.
- **Concurrencia optimista bien entendida.** El event store valida `expected_sequence_number` y además se apoya en un índice único; su docstring explica por qué el chequeo solo no alcanza. El doble envío de una respuesta se resuelve con ese mecanismo.
- **Lógica pura donde corresponde.** El puntaje (`calcular_puntaje`) es una función sin dependencias.

## Hallazgos

### DM-01 · El evento no es la fuente del cambio de estado

- **Vara:** Decisión · **Severidad:** Alta · **Confianza:** Verificado · **Esfuerzo:** L
- **Evidencia:**
  - El agregado muta su estado con un método (`iniciar()`, `responder()`); después el caso de uso construye el evento y arma su payload a mano (función `_payload` en `responder_pregunta_en_vivo.py`).
  - Hay 18 archivos de `use_cases/` de Actividad Evaluativa que arman payloads y ninguno en `entities/`.
  - La lectura está en otro lado: `reconstruir` y `_aplicar_evento`, en `entities/`, acceden a `payload[...]` 34 veces.
- **Por qué importa:** el mismo esquema se escribe en una capa y se lee en otra, sin un tipo que las una. Nada garantiza que reproducir los eventos dé el mismo estado que produjo la mutación original. Ese es el invariante central de event sourcing y hoy depende de la disciplina de quien escribe cada caso de uso.
- **Recomendación:**
  1. Que cada evento de dominio sepa serializarse y deserializarse (`a_payload()` y `desde_payload()` en `entities/`).
  2. Que el agregado emita sus eventos y se los aplique a sí mismo, con el mismo `_aplicar_evento` que usa `reconstruir`.
  3. Un test por evento: crear, serializar, reconstruir y comparar.

### DM-02 · Los eventos no tienen versión de esquema

- **Vara:** Decisión · **Severidad:** Alta · **Confianza:** Verificado · **Esfuerzo:** S (agregar el campo), M (política de migración)
- **Evidencia:** no hay columna ni campo de versión en `EventoModel` ni en el event store. El agregado ya muestra el síntoma: `payload.get("unidad_tematica") or None` y `payload.get("tema") or None` son lecturas defensivas para eventos escritos antes de que existieran esos campos.
- **Por qué importa:** el store es append-only y los eventos son para siempre. Cada cambio de payload deja una lectura defensiva permanente en el agregado y otra en Analytics ([AC-03](03-acoplamiento-entre-contextos.md#ac-03--analytics-lee-los-eventos-crudos-de-actividad-evaluativa-y-los-recorre-completos)). Sin versión, tampoco se puede saber qué forma tiene un evento viejo.
- **Recomendación:** agregar `schema_version` a cada evento ahora, cuando todavía hay una sola instalación y pocos datos, y definir en `ADR-002` cómo se actualiza un evento viejo al leerlo.

### DM-03 · Los agregados conocen el registro de persistencia

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** se resuelve con DM-01
- **Evidencia:** tres agregados importan `EventoAlmacenado` desde `entities/ports/event_store_port.py` (por ejemplo `evaluacion.py:19` y `actividad_evaluativa_periodo_abierto.py:15`) y reciben listas de ese tipo en `reconstruir`.
- **Por qué importa:** `EventoAlmacenado` tiene `sequence_number` y un payload sin tipo: es la forma en que el almacén guarda, no un concepto del dominio. El import no viola la regla de capas (el puerto está en `entities/`), pero el modelo quedó atado al formato de su persistencia.
- **Recomendación:** con DM-01, `reconstruir` recibe eventos de dominio tipados y la traducción desde `EventoAlmacenado` queda en un solo lugar.

### DM-04 · La transacción termina dentro de `append`

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** se resuelve con IM-03
- **Evidencia:** `SQLAlchemyEventStore.append` hace `commit()`. La proyección del ranking se escribe antes, sin confirmar, y queda confirmada por ese mismo commit; `_persistir` documenta el contrato y llama a `descartar_pendientes()` si falla.
- **Por qué importa:** la atomicidad entre evento y proyección depende del orden de dos llamadas y de que ambos objetos compartan la sesión. Funciona, pero es un contrato implícito. Un caso de uso que necesite escribir en dos streams no puede hacerlo de forma atómica.
- **Recomendación:** ver [IM-03](05-implementacion-por-capa.md#im-03--la-transacción-vive-en-el-repositorio-no-en-el-caso-de-uso).

### DM-05 · El tipo de pregunta se resuelve con primitivos y `isinstance`

- **Vara:** Decisión · **Severidad:** Alta (compromete el escenario de mantenibilidad) · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - La respuesta del alumno es `contenido: dict[str, Any]`, con forma distinta según el tipo de pregunta. Hay 32 usos de `dict[str, Any]` en `entities/` y `use_cases/`.
  - `_opcion_de` (en el caso de uso) deduce el tipo por la presencia de la clave `"opcion_indice"`.
  - La corrección está en el adaptador de Actividad Evaluativa, con tres `isinstance` sobre `PreguntaPlantillaOpcionMultiple`. Todo lo que no es opción múltiple se trata como verdadero/falso.
- **Por qué importa:** `RNF_v1.md` pide agregar un tipo de pregunta en un día sin tocar sesiones, puntaje ni analytics. Hoy un tipo nuevo toca Banco, el adaptador de Actividad Evaluativa (tres métodos), el caso de uso de respuesta en vivo, el histograma y el frontend. Y el `else` implícito lo corregiría en silencio como verdadero/falso.
- **Recomendación:**
  1. Que `PreguntaPlantilla` corrija: un método `corregir(respuesta) -> bool` por tipo, en Banco de Preguntas.
  2. Un value object `RespuestaDada` por tipo en lugar del diccionario.
  3. Exponer la corrección por la interfaz pública de Banco ([AC-01](03-acoplamiento-entre-contextos.md#ac-01--ningún-contexto-publica-una-interfaz-el-consumidor-se-acopla-a-sus-internos)).
  4. Hacer la prueba del escenario: agregar un tercer tipo en una rama descartable y contar archivos y horas.

### DM-06 · El tiempo y los identificadores no se inyectan

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - En `entities/`: 12 llamadas a `datetime.now` y 12 a `uuid4`. En `use_cases/`: 21 y 2.
  - Hay dos relojes por evento: `ocurrido_en` dentro del payload y `occurred_at`, que el event store calcula con su propio `datetime.now(UTC)`.
- **Por qué importa:** el puntaje en vivo depende del tiempo de respuesta. Con el reloj tomado en línea, los tests de esas reglas dependen del reloj real o de parches. Dos marcas de tiempo distintas para el mismo hecho complican el diagnóstico posterior.
- **Recomendación:** el patrón correcto ya existe en `validar_para_responder(pregunta_id, ahora)`: pasar el instante como parámetro. Generalizarlo con un puerto `Reloj` en `shared/` y usar una sola marca de tiempo por evento.

### DM-07 · Event sourcing quedó a mitad de camino

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** decisión, sin código
- **Evidencia:** DM-01, DM-02 y DM-03 juntos. Se usa el event store para registrar y para reconstruir, pero no hay eventos tipados, versiones ni proyecciones generales (salvo las de la sesión en vivo).
- **Por qué importa:** se paga el costo de event sourcing (reconstrucción, Analytics leyendo streams, concurrencia por secuencia) y se obtiene parte del beneficio. La decisión de `ADR-002` es defendible por el escenario de confiabilidad (cero pérdida de respuestas) y por el diagnóstico posterior a un incidente, pero la implementación actual es más un registro de eventos que un modelo guiado por eventos.
- **Recomendación:** decidir de forma explícita y dejarlo en `ADR-002`: completar el patrón (DM-01 y DM-02) o declararlo "registro de eventos con reconstrucción" y aceptar sus límites. La primera opción es la recomendada si `RF-18` sigue en el alcance.

## Juicio

El modelo táctico es bueno: agregados chicos, invariantes nombrados, concurrencia bien resuelta. La debilidad está en el tratamiento de los eventos como diccionarios sin tipo ni versión, que hoy conocen tres lugares distintos (casos de uso, agregados y Analytics). Es la deuda que más conviene pagar pronto, porque crece con cada evento guardado.
