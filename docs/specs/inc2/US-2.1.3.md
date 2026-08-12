# US-2.1.3: Docente carga una pregunta de opción múltiple

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `PreguntaPlantillaOpcionMultiple`
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **cargar una pregunta de opción múltiple con sus opciones y metadatos**
para **que quede disponible en el banco de su materia, lista para usarse en sesiones (RF-04,
RF-05)**.

---

## Contexto del dominio

### Problema

Es el primer tipo de pregunta a implementar — establece el patrón de carga que `US-2.1.4`
(Verdadero/Falso) sigue con su propia estructura diferenciada, sin generalizar entre ambas
(`BC-banco-preguntas-modelo.md` §4).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `PreguntaPlantillaOpcionMultiple` | `texto`, `opciones` (lista `{texto, es_correcta}`), metadatos, `activa` |
| Command | `CargarPreguntaOpcionMultiple(banco_id, texto, opciones, unidad, tema, dificultad, importancia)` | Crea la pregunta |
| Domain Event | `PreguntaCargada` | Señala el alta |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- `banco_id` corresponde a un `Banco` existente (`US-2.1.1`).

### Postcondicion

- `PreguntaPlantillaOpcionMultiple` persistida con `activa = true`.
- Evento `PreguntaCargada`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-BP-02 | Exactamente una opción con `es_correcta = true` — `OpcionesInvalidas` si no. |
| INV-BP-03 | Mínimo 2 opciones — `OpcionesInvalidas` si no. |

---

## Criterios de aceptacion

```gherkin
Feature: Carga de pregunta de opción múltiple (US-2.1.3)

  Scenario: Carga exitosa
    Given un Docente autenticado y un Banco existente para "Ingeniería de Software"
    When ejecuta CargarPreguntaOpcionMultiple con 3 opciones y una marcada como correcta
    Then el sistema persiste la PreguntaPlantillaOpcionMultiple con activa = true
    And se emite el evento PreguntaCargada

  Scenario: Rechazo por ninguna opción correcta
    Given un Docente autenticado y un Banco existente
    When ejecuta CargarPreguntaOpcionMultiple con 3 opciones y ninguna marcada como correcta
    Then el sistema rechaza la operación con OpcionesInvalidas

  Scenario: Rechazo por más de una opción correcta
    Given un Docente autenticado y un Banco existente
    When ejecuta CargarPreguntaOpcionMultiple con 2 opciones marcadas como correctas
    Then el sistema rechaza la operación con OpcionesInvalidas

  Scenario: Rechazo por menos de 2 opciones
    Given un Docente autenticado y un Banco existente
    When ejecuta CargarPreguntaOpcionMultiple con una única opción
    Then el sistema rechaza la operación con OpcionesInvalidas
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — `PreguntaPlantillaOpcionMultiple`, evento `PreguntaCargada`
- [x] Use Cases — `CargarPreguntaOpcionMultipleUseCase`
- [x] Interface Adapters — controller, `PreguntaRepositoryPort`
- [x] Frameworks — endpoint FastAPI, modelo SQLAlchemy + migración
- [ ] Frontend — cubierto por `US-2.1.11`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#nueva-pregunta-om`) se
especifica en `US-2.1.11`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/pregunta_plantilla.py` | Aggregate `PreguntaPlantillaOpcionMultiple` (y clase base común mínima si aplica, sin forzar estructura uniforme con V/F) |
| `src/banco_preguntas/entities/eventos.py` | Agregar `PreguntaCargada` |
| `src/banco_preguntas/entities/ports/pregunta_repository_port.py` | Puerto de persistencia |
| `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py` | Orquesta INV-BP-02, INV-BP-03 |
| `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` | Validación de entrada, mapeo a use case |
| `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` | Implementación SQLAlchemy |
| `src/banco_preguntas/frameworks/api/preguntas_router.py` | Endpoint FastAPI (requiere rol `docente`) |
| `src/banco_preguntas/frameworks/db/models.py` | Modelo SQLAlchemy `pregunta_plantilla` (columna discriminadora de tipo) |
| `src/banco_preguntas/frameworks/db/migrations/` | Migración Alembic |

---

## Referencias

- Relacionada con: `US-2.1.1` (precondición, `Banco`), `US-2.1.4` (mismo patrón, tipo distinto)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§4 `PreguntaPlantillaOpcionMultiple`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
