# US-2.1.11: Docente carga una pregunta eligiendo su tipo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.1.3`/`US-2.1.4`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **elegir el tipo de pregunta (Opción Múltiple o Verdadero/Falso) y completar el
formulario correspondiente**
para **cargar preguntas al banco desde la UI, sin usar la API directamente (RF-04, RF-05)**.

---

## Contexto del dominio

### Problema

`POST /preguntas/opcion-multiple` y `POST /preguntas/verdadero-falso` existen desde
`US-2.1.3`/`US-2.1.4`, pero sin esta US no hay forma de cargarlas desde la aplicación real. Los
dos tipos tienen formularios distintos (sin estructura uniforme forzada,
`BC-banco-preguntas-modelo.md` §4) — se resuelve con una pantalla previa de selección de tipo.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /preguntas/opcion-multiple` | Ya existe (`US-2.1.3`) |
| Endpoint consumido | `POST /preguntas/verdadero-falso` | Ya existe (`US-2.1.4`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.10` implementada (se navega a la carga desde el botón "Nueva pregunta" del banco).

### Postcondicion

- Selección de tipo → navega al formulario correspondiente.
- Carga exitosa (cualquiera de los dos tipos) → vuelve al banco filtrado, la pregunta nueva
  visible en la tabla.
- Validación de opciones (Opción Múltiple: mínimo 2, exactamente una correcta) aplicada en el
  cliente antes de enviar — la regla de negocio la aplica el backend (`OpcionesInvalidas`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El tipo elegido en la primera pantalla no se puede cambiar después — no hay botón "volver" que preserve datos ya cargados entre formularios de distinto tipo. |

---

## Criterios de aceptacion

```gherkin
Feature: Carga de pregunta desde la UI (US-2.1.11)

  Scenario: Elegir tipo Opción Múltiple
    Given un Docente en la pantalla de selección de tipo
    When elige "Opción múltiple"
    Then el sistema muestra el formulario con lista de opciones y radio de correcta

  Scenario: Carga exitosa de Opción Múltiple
    Given un Docente en el formulario de Opción Múltiple con 3 opciones y una marcada correcta
    When completa el texto y guarda
    Then el sistema crea la pregunta
    And vuelve al banco filtrado, mostrando la pregunta nueva

  Scenario: Rechazo de cliente por opciones inválidas
    Given un Docente en el formulario de Opción Múltiple sin ninguna opción marcada como correcta
    When intenta guardar
    Then el formulario bloquea el envío con un mensaje de validación
    And no se llama al backend

  Scenario: Carga exitosa de Verdadero/Falso
    Given un Docente en el formulario de Verdadero/Falso
    When completa el texto, elige "Verdadero" y guarda
    Then el sistema crea la pregunta
    And vuelve al banco filtrado
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume endpoints ya implementados.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/NuevaPreguntaTipo.tsx`, `NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.4 (`#nueva-pregunta-tipo`), §2.5
(`#nueva-pregunta-om`), §2.6 (`#nueva-pregunta-vf`). Prototipo navegable:
`docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/NuevaPreguntaTipo.tsx` | Selector de tipo (dos tarjetas) |
| `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` | Formulario — opciones dinámicas, radio de correcta, metadatos |
| `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx` | Formulario — selector V/F, metadatos |
| `frontend/src/router.tsx` | Rutas de carga bajo `/materias/:id/banco/preguntas/nueva/*` |

---

## Referencias

- Relacionada con: `US-2.1.3`, `US-2.1.4` (backend), `US-2.1.10` (navegación de entrada)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 1 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
