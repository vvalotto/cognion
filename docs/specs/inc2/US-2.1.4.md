# US-2.1.4: Docente carga una pregunta de Verdadero/Falso

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `PreguntaPlantillaVerdaderoFalso`
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **cargar una pregunta de Verdadero/Falso con su respuesta correcta y metadatos**
para **que quede disponible en el banco de su materia, lista para usarse en sesiones (RF-04,
RF-05)**.

---

## Contexto del dominio

### Problema

Segundo tipo de pregunta, con estructura diferenciada de `PreguntaPlantillaOpcionMultiple`
(`US-2.1.3`) — sin lista de opciones, reemplazada por un booleano fijo
(`BC-banco-preguntas-modelo.md` §4).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `PreguntaPlantillaVerdaderoFalso` | `texto`, `respuesta_correcta: bool`, metadatos, `activa` |
| Command | `CargarPreguntaVerdaderoFalso(banco_id, texto, respuesta_correcta, unidad, tema, dificultad, importancia)` | Crea la pregunta |
| Domain Event | `PreguntaCargada` | Señala el alta (mismo evento que `US-2.1.3`, distinto aggregate de origen) |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- `banco_id` corresponde a un `Banco` existente (`US-2.1.1`).

### Postcondicion

- `PreguntaPlantillaVerdaderoFalso` persistida con `activa = true`.
- Evento `PreguntaCargada`.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `respuesta_correcta` es un booleano obligatorio — sin valor por defecto implícito, debe indicarse explícitamente en el request. |

---

## Criterios de aceptacion

```gherkin
Feature: Carga de pregunta Verdadero/Falso (US-2.1.4)

  Scenario: Carga exitosa con respuesta Verdadero
    Given un Docente autenticado y un Banco existente para "Gestión de Proyectos"
    When ejecuta CargarPreguntaVerdaderoFalso con respuesta_correcta = true
    Then el sistema persiste la PreguntaPlantillaVerdaderoFalso con activa = true
    And se emite el evento PreguntaCargada

  Scenario: Carga exitosa con respuesta Falso
    Given un Docente autenticado y un Banco existente
    When ejecuta CargarPreguntaVerdaderoFalso con respuesta_correcta = false
    Then el sistema persiste la PreguntaPlantillaVerdaderoFalso con activa = true
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — `PreguntaPlantillaVerdaderoFalso`
- [x] Use Cases — `CargarPreguntaVerdaderoFalsoUseCase`
- [x] Interface Adapters — controller (mismo `PreguntaRepositoryPort` de `US-2.1.3`)
- [x] Frameworks — endpoint FastAPI, modelo SQLAlchemy + migración
- [ ] Frontend — cubierto por `US-2.1.11`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#nueva-pregunta-vf`) se
especifica en `US-2.1.11`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/pregunta_plantilla.py` | Aggregate `PreguntaPlantillaVerdaderoFalso` |
| `src/banco_preguntas/use_cases/cargar_pregunta_verdadero_falso.py` | Orquesta la creación |
| `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` | Nuevo endpoint/rama para este tipo |
| `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` | Extiende el repositorio de `US-2.1.3` |
| `src/banco_preguntas/frameworks/api/preguntas_router.py` | Endpoint FastAPI (requiere rol `docente`) |
| `src/banco_preguntas/frameworks/db/models.py` | Reutiliza el modelo de `US-2.1.3` (columna discriminadora) |

---

## Referencias

- Relacionada con: `US-2.1.1` (precondición, `Banco`), `US-2.1.3` (mismo patrón, tipo distinto)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§4 `PreguntaPlantillaVerdaderoFalso`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
