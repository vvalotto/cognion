# US-2.1.6: Docente elimina (baja lógica) una pregunta

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `PreguntaPlantillaOpcionMultiple` / `PreguntaPlantillaVerdaderoFalso`
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **eliminar una pregunta que ya no quiero usar**
para **que deje de estar disponible en el banco y en nuevas sesiones, sin afectar sesiones
pasadas que ya la usaron**.

---

## Contexto del dominio

### Problema

La eliminación es lógica, no física (decisión explícita de Víctor,
`BC-banco-preguntas-modelo.md` §5, hot spot 4) — preserva el historial de sesiones que ya
usaron la pregunta (Incremento 3, BC Sesiones).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Command | `EliminarPregunta(pregunta_id)` | Marca `activa = false` |
| Domain Event | `PreguntaEliminada` | Señala la baja |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- La `PreguntaPlantilla` (`pregunta_id`) existe y `activa = true`.

### Postcondicion

- `PreguntaPlantilla.activa = false`.
- La fila no se borra de la base — persiste para no romper el historial de sesiones que ya la
  usaron.
- Evento `PreguntaEliminada`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-BP-04 | Eliminación lógica, no física — `activa = false`, la fila persiste. |
| — | Eliminar una pregunta ya eliminada (`activa = false`) es un error explícito (`PreguntaYaEliminada`), no una operación idempotente silenciosa — evita que el Docente crea que repitió la acción sin efecto cuando en realidad no había nada que eliminar. |

---

## Criterios de aceptacion

```gherkin
Feature: Eliminación lógica de pregunta (US-2.1.6)

  Scenario: Eliminación exitosa
    Given una PreguntaPlantilla activa
    When un Docente ejecuta EliminarPregunta(pregunta_id)
    Then el sistema marca la pregunta como activa = false
    And la pregunta sigue existiendo en la base de datos
    And se emite el evento PreguntaEliminada

  Scenario: Rechazo por pregunta ya eliminada
    Given una PreguntaPlantilla con activa = false
    When un Docente ejecuta EliminarPregunta(pregunta_id) sobre ella
    Then el sistema rechaza la operación con PreguntaYaEliminada
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — método `eliminar()` en `PreguntaPlantilla`
- [x] Use Cases — `EliminarPreguntaUseCase`
- [x] Interface Adapters — controller, reutiliza `PreguntaRepositoryPort`
- [x] Frameworks — endpoint FastAPI `DELETE /preguntas/{id}` (baja lógica, no `DELETE` físico en SQL)
- [ ] Frontend — cubierto por `US-2.1.13`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#eliminar-pregunta`) se
especifica en `US-2.1.13`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/pregunta_plantilla.py` | Método `eliminar()`, valida INV-BP-04 |
| `src/banco_preguntas/entities/eventos.py` | Agregar `PreguntaEliminada` |
| `src/banco_preguntas/use_cases/eliminar_pregunta.py` | Orquesta la baja lógica |
| `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` | Endpoint de eliminación |
| `src/banco_preguntas/frameworks/api/preguntas_router.py` | `DELETE /preguntas/{id}` (UPDATE de `activa`, no DELETE SQL) |

---

## Referencias

- Relacionada con: `US-2.1.3`, `US-2.1.4` (crean lo que esta US elimina), `US-2.1.7` (`FiltrarBanco` excluye inactivas)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§4, INV-BP-04)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
