# US-2.1.13: Docente elimina una pregunta desde la UI, con confirmación previa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.1.6`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **eliminar una pregunta desde la UI, con una confirmación previa que me aclare que es
una baja lógica**
para **evitar eliminaciones accidentales y entender que las sesiones pasadas no se ven
afectadas**.

---

## Contexto del dominio

### Problema

`DELETE /preguntas/{id}` existe desde `US-2.1.6`, pero sin esta US no hay forma de eliminarla
desde la aplicación real. Al ser una operación destructiva desde la perspectiva del Docente
(aunque técnicamente sea baja lógica), el wireframe exige una pantalla de confirmación
explícita (`wireframes-banco-preguntas.md` §2.8).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `DELETE /preguntas/{id}` | Ya existe (`US-2.1.6`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.10` implementada (se navega a la confirmación desde la acción "Eliminar" de la tabla
  del banco).

### Postcondicion

- Confirmación muestra el texto de la pregunta a eliminar y aclara explícitamente que es baja
  lógica (no afecta sesiones pasadas).
- Confirmar → el sistema ejecuta `DELETE /preguntas/{id}` y vuelve al banco filtrado, la
  pregunta ya no aparece en la tabla.
- Cancelar → vuelve al banco sin ejecutar ningún cambio.

### Invariantes

| ID | Invariante |
|----|------------|
| — | No hay eliminación directa desde la fila de la tabla sin pasar por la pantalla de confirmación — mismo criterio que cualquier acción destructiva del sistema. |

---

## Criterios de aceptacion

```gherkin
Feature: Eliminación de pregunta desde la UI (US-2.1.13)

  Scenario: Confirmar eliminación
    Given un Docente en la confirmación de eliminación de una pregunta
    When hace clic en "Sí, eliminar"
    Then el sistema ejecuta la baja lógica
    And vuelve al banco filtrado, la pregunta ya no aparece en la tabla

  Scenario: Cancelar eliminación
    Given un Docente en la confirmación de eliminación de una pregunta
    When hace clic en "Cancelar"
    Then el sistema vuelve al banco filtrado
    And la pregunta sigue apareciendo en la tabla, sin cambios
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/EliminarPregunta.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.8 (`#eliminar-pregunta`). Prototipo
navegable: `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/EliminarPregunta.tsx` | Pantalla de confirmación — texto de la pregunta, aclaración de baja lógica, acciones confirmar/cancelar |
| `frontend/src/router.tsx` | Ruta `/materias/:id/banco/preguntas/:preguntaId/eliminar` |

---

## Referencias

- Relacionada con: `US-2.1.6` (backend), `US-2.1.10` (navegación de entrada)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 1 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
