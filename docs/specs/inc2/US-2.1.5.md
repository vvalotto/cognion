# US-2.1.5: Docente edita una pregunta existente

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `PreguntaPlantillaOpcionMultiple` / `PreguntaPlantillaVerdaderoFalso`
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **editar una pregunta ya cargada (texto, opciones o respuesta, metadatos)**
para **corregir errores o ajustar su clasificación sin tener que eliminarla y recrearla
(RF-05)**.

---

## Contexto del dominio

### Problema

Depende de `US-2.1.3`/`US-2.1.4` — no hay nada que editar sin preguntas ya cargadas. El tipo de
la pregunta (Opción Múltiple / Verdadero-Falso) no se puede cambiar en la edición — es fijo
desde la creación (`BC-banco-preguntas-modelo.md` §4).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Command | `EditarPregunta(pregunta_id, ...)` | Actualiza los campos editables según el tipo concreto de la pregunta |
| Domain Event | `PreguntaEditada` | Señala la edición |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- La `PreguntaPlantilla` (`pregunta_id`) existe y `activa = true`.

### Postcondicion

- Campos actualizados según el tipo concreto de la pregunta (texto, opciones/respuesta_correcta,
  metadatos).
- Evento `PreguntaEditada`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-BP-02 | Si es `PreguntaPlantillaOpcionMultiple`: exactamente una opción `es_correcta` tras la edición. |
| INV-BP-03 | Si es `PreguntaPlantillaOpcionMultiple`: mínimo 2 opciones tras la edición. |
| — | El tipo de la pregunta (Opción Múltiple / Verdadero-Falso) no es editable — cualquier intento de enviarlo se ignora o se rechaza según cómo lo module el endpoint, sin excepción de dominio nueva. |
| — | Una pregunta con `activa = false` no puede editarse — `PreguntaInactiva` si se intenta. |

---

## Criterios de aceptacion

```gherkin
Feature: Edición de pregunta (US-2.1.5)

  Scenario: Edición exitosa de opción múltiple
    Given una PreguntaPlantillaOpcionMultiple activa con 3 opciones
    When un Docente ejecuta EditarPregunta cambiando el texto y una opción
    Then el sistema persiste los cambios
    And se emite el evento PreguntaEditada

  Scenario: Rechazo por dejar la pregunta sin opción correcta
    Given una PreguntaPlantillaOpcionMultiple activa
    When un Docente ejecuta EditarPregunta desmarcando la única opción correcta sin marcar otra
    Then el sistema rechaza la operación con OpcionesInvalidas

  Scenario: Rechazo por editar una pregunta eliminada
    Given una PreguntaPlantilla con activa = false
    When un Docente intenta ejecutar EditarPregunta sobre ella
    Then el sistema rechaza la operación con PreguntaInactiva
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — método de edición en `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`
- [x] Use Cases — `EditarPreguntaUseCase`
- [x] Interface Adapters — controller, reutiliza `PreguntaRepositoryPort`
- [x] Frameworks — endpoint FastAPI `PUT /preguntas/{id}`
- [ ] Frontend — cubierto por `US-2.1.12`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#editar-pregunta`) se
especifica en `US-2.1.12`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/pregunta_plantilla.py` | Método `editar(...)` en cada subtipo, reaplica INV-BP-02/03 donde corresponda |
| `src/banco_preguntas/entities/eventos.py` | Agregar `PreguntaEditada` |
| `src/banco_preguntas/use_cases/editar_pregunta.py` | Orquesta la validación según el tipo concreto |
| `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` | Endpoint de edición |
| `src/banco_preguntas/frameworks/api/preguntas_router.py` | `PUT /preguntas/{id}` |

---

## Referencias

- Relacionada con: `US-2.1.3`, `US-2.1.4` (crean lo que esta US edita)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§2, §3 `EditarPregunta`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
