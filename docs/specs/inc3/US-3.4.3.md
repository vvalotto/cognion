# US-3.4.3: Docente crea una nueva actividad de período abierto

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-3.1.2`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **crear una actividad de período abierto indicando ventana de disponibilidad, cantidad
de preguntas e intentos permitidos**
para **habilitar una evaluación que mis estudiantes puedan rendir sin coordinación en vivo
(RF-11)**.

---

## Contexto del dominio

### Problema

`POST /actividades` existe desde `US-3.1.2`, sin cambios necesarios — esta US solo construye
el formulario que lo invoca. Sin ella no hay forma de crear una actividad desde la aplicación
real.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /actividades` | Ya existe (`US-3.1.2`) — `materia_id` implícito por el contexto de navegación, no un campo del formulario |

---

## Especificacion del comportamiento

### Precondicion

- `US-3.4.2` implementada (se navega a esta pantalla desde "+ Nueva actividad").

### Postcondicion

- Creación exitosa → vuelve al listado de actividades de la materia (`US-3.4.2`), la actividad
  nueva visible.
- Validación de cliente (`fecha_apertura < fecha_cierre`, intentos ≥ 1) aplicada antes de
  enviar — la regla de negocio la aplica el backend (`PeriodoInvalido`,
  `CantidadIntentosInvalida`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | `cantidad_preguntas` no se valida contra el banco en el cliente — solo se muestra como hint informativo (dato de referencia); el rechazo real (`PreguntasInsuficientes`) es un 422 del backend (INV-AE-01). |

---

## Criterios de aceptacion

```gherkin
Feature: Creación de actividad desde la UI (US-3.4.3)

  Scenario: Creación exitosa
    Given un Docente en el formulario de nueva actividad, con apertura/cierre/preguntas/intentos válidos
    When completa el formulario y guarda
    Then el sistema crea la actividad
    And vuelve al listado de actividades, mostrando la nueva

  Scenario: Rechazo de cliente por período inválido
    Given un Docente con fecha de cierre anterior a la de apertura
    When intenta guardar
    Then el formulario bloquea el envío con un mensaje de validación
    And no se llama al backend

  Scenario: Rechazo del servidor por preguntas insuficientes
    Given un Docente que pide más preguntas de las activas en el banco de la materia
    When guarda
    Then el backend responde 422 PreguntasInsuficientes
    And el formulario muestra el error inline
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/NuevaActividad.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-actividad-evaluativa.md` §2.2 (`#doc-nueva-actividad`). Prototipo:
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/NuevaActividad.tsx` | Nueva — formulario de creación |
| `frontend/src/router.tsx` | Ruta `/actividad-evaluativa/materias/:materiaId/actividades/nueva` |

---

## Referencias

- Relacionada con: `US-3.1.2` (backend consumido), `US-3.4.2` (navegación de entrada y de salida)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
