# Plan de Implementación: US-2.1.5 - Docente edita una pregunta existente

**Patrón:** Clean Architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion / BC Banco de Preguntas
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-12

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Contexto y verificación | 41 s |
| 1 — Escenarios BDD | 43 s |
| 2 — Plan de implementación | 6 min 3 s |
| 3 — Implementación guiada | 11 min 58 s |
| 4 — Tests unitarios | 1 min 56 s |
| 5 — Tests de integración | 4 min 4 s |
| 6 — Validación BDD | 1 min 39 s |
| 7 — Quality gates | 4 min 44 s |

Nota PRIN-001: tiempos reales de ejecución del agente, no comparables contra estimación humana en puntos de historia.

## Nota de diseño (a confirmar)

La spec no lista una excepción para `pregunta_id` inexistente (solo cubre `activa = false` vía
`PreguntaInactiva`). Se agrega `PreguntaNoExiste` siguiendo el mismo patrón que `BancoNoExiste`
(`US-2.1.3`/`US-2.1.4`) — sin esto, `EditarPregunta` sobre un id inválido no tendría forma de
fallar de manera controlada. No está en los criterios Gherkin de la US, pero es una precondición
implícita del mismo tipo. Se marca aquí para que quede visible antes de codear.

## Componentes a Implementar

### 1. Entities
- [x] `src/banco_preguntas/entities/errors.py`
  - Agregar `PreguntaNoExiste` (paralela a `BancoNoExiste`)
  - Agregar `PreguntaInactiva` (invariante de la spec: no se edita una pregunta con `activa = false`)
- [x] `src/banco_preguntas/entities/eventos.py`
  - Agregar `PreguntaEditada(pregunta_id, banco_id, ocurrido_en)`
- [x] `src/banco_preguntas/entities/pregunta_plantilla.py`
  - `PreguntaPlantillaOpcionMultiple.editar(texto, opciones, unidad_tematica, tema, dificultad, importancia)`
    — reaplica INV-BP-02/03 (extrae la validación de `crear` a un helper compartido `_validar_opciones`
    para no duplicarla), levanta `PreguntaInactiva` si `not self.activa`, muta los campos in-place
  - `PreguntaPlantillaVerdaderoFalso.editar(texto, respuesta_correcta, unidad_tematica, tema, dificultad, importancia)`
    — sin invariantes adicionales, levanta `PreguntaInactiva` si `not self.activa`, muta los campos in-place

### 2. Ports
- [x] `src/banco_preguntas/entities/ports/pregunta_repository_port.py`
  - `obtener_por_id(pregunta_id) -> PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso | None`
  - `actualizar(pregunta) -> None` (distinto de `guardar`, que es alta — evita ambigüedad de upsert)

### 3. Use Cases
- [x] `src/banco_preguntas/use_cases/editar_pregunta.py`
  - `EditarPreguntaUseCase(pregunta_repositorio)`
  - `execute(pregunta_id, texto, unidad_tematica, tema, dificultad, importancia, opciones=None, respuesta_correcta=None)`
    - Obtiene la pregunta por id; `PreguntaNoExiste` si no existe
    - Delega en `pregunta.editar(...)` (dispatch por tipo concreto vía `isinstance`, sin lógica de
      negocio en el use case — invariantes y `PreguntaInactiva` viven en la entidad)
    - Persiste con `actualizar`, emite `PreguntaEditada`

### 4. Interface Adapters
- [x] `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`
  - Método `editar_pregunta(...)`, recibe `EditarPreguntaUseCase` por constructor (tercer use case)
- [x] `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
  - `obtener_por_id`: `session.get(PreguntaPlantillaModel, pregunta_id)`, mapea al aggregate según `tipo`
  - `actualizar`: recupera el modelo existente y sobrescribe sus columnas (sin insertar fila nueva)

### 5. Frameworks
- [x] `src/banco_preguntas/frameworks/api/schemas.py`
  - `EditarPreguntaRequest` (texto, unidad_tematica, tema, dificultad, importancia, `opciones: list[OpcionSchema] | None`, `respuesta_correcta: bool | None`)
- [x] `src/banco_preguntas/frameworks/api/preguntas_router.py`
  - `PUT /preguntas/{pregunta_id}`, rol `docente`
  - 200 con `PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse` según el tipo real
  - 404 si `PreguntaNoExiste`, 422 si `OpcionesInvalidas`, 409 si `PreguntaInactiva`
- [x] `src/banco_preguntas/frameworks/dependencies.py`
  - `get_preguntas_controller` instancia también `EditarPreguntaUseCase`

### 6. Integración
- [x] Actualizar fakes/tests existentes de `PreguntasController` al nuevo constructor de 3 use cases
  (mismo ajuste que hizo `US-2.1.4` al pasar de 1 a 2)

**Estado:** 10/10 tareas completadas
