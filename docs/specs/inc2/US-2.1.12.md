# US-2.1.12: Docente edita una pregunta existente desde la UI

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.1.5`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **editar una pregunta existente desde la UI**
para **corregir errores o ajustar su clasificación sin recrearla (RF-05)**.

---

## Contexto del dominio

### Problema

`PUT /preguntas/{id}` existe desde `US-2.1.5`, pero sin esta US no hay forma de editarla desde
la aplicación real. Reutiliza el mismo formulario de carga (`US-2.1.11`), prellenado — el tipo
de la pregunta no se puede cambiar, mismo criterio que el backend.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `PUT /preguntas/{id}` | Ya existe (`US-2.1.5`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.10` implementada (se navega a la edición desde la acción "Editar" de la tabla del banco).

### Postcondicion

- Formulario prellenado con los valores actuales de la pregunta, según su tipo concreto.
- Guardado exitoso → vuelve al banco filtrado con los cambios reflejados.
- Rechazo por `OpcionesInvalidas` (si es Opción Múltiple) → mismo mensaje de validación que
  `US-2.1.11`, sin perder los datos ya ingresados.

### Invariantes

| ID | Invariante |
|----|------------|
| — | El formulario no muestra selector de tipo — mismo criterio que `US-2.1.11`, el tipo es fijo desde la creación. |

---

## Criterios de aceptacion

```gherkin
Feature: Edición de pregunta desde la UI (US-2.1.12)

  Scenario: Edición exitosa
    Given un Docente en la pantalla de edición de una PreguntaPlantillaOpcionMultiple
    When modifica el texto y guarda
    Then el sistema persiste los cambios
    And vuelve al banco filtrado, mostrando el texto actualizado

  Scenario: Rechazo de cliente por opciones inválidas
    Given un Docente editando una pregunta de Opción Múltiple
    When deja más de una opción marcada como correcta e intenta guardar
    Then el formulario bloquea el envío con un mensaje de validación
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/EditarPregunta.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.7 (`#editar-pregunta`). Prototipo navegable:
`docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/EditarPregunta.tsx` | Reutiliza el formulario de `US-2.1.11` según el tipo, prellenado con los datos actuales |
| `frontend/src/router.tsx` | Ruta `/materias/:id/banco/preguntas/:preguntaId/editar` |

---

## Referencias

- Relacionada con: `US-2.1.5` (backend), `US-2.1.10` (navegación de entrada), `US-2.1.11` (formulario reutilizado)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 1 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
