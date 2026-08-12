# US-2.1.9: Docente ve el listado de materias y da de alta una nueva

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.1.1`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver el listado de materias y dar de alta una nueva desde la UI**
para **acceder al banco de cada materia y crear materias nuevas sin usar la API directamente
(RF-04)**.

---

## Contexto del dominio

### Problema

`POST /materias` y el listado de materias existen desde `US-2.1.1`, pero sin esta US ningún
Docente puede operarlos desde la aplicación real.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /materias`, `GET /materias` | Ya existen (`US-2.1.1`) |
| Cliente API | `banco-preguntas-api.ts` (`US-2.1.8`) | Ejecuta los requests |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.8` implementada.
- Docente autenticado (rol `docente`).

### Postcondicion

- Grilla de materias renderizada con el nombre y cantidad de preguntas activas de cada una.
- Alta exitosa de materia → vuelve al listado con la nueva materia visible.
- Nombre duplicado → error inline en el formulario, sin pantalla propia (mismo criterio de
  simplicidad que otros errores de formulario en Identidad).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El formulario no permite enviar un nombre vacío (validación de cliente, la regla de negocio la aplica el backend). |

---

## Criterios de aceptacion

```gherkin
Feature: Listado y alta de materias (US-2.1.9)

  Scenario: Ver el listado de materias
    Given un Docente autenticado con materias existentes
    When navega a la pantalla de materias
    Then ve una tarjeta por cada materia con su cantidad de preguntas activas

  Scenario: Alta exitosa de materia
    Given un Docente autenticado en el listado de materias
    When completa el formulario de nueva materia con un nombre no usado
    Then el sistema crea la materia y su banco
    And vuelve al listado, mostrando la materia nueva

  Scenario: Rechazo por nombre duplicado
    Given una materia existente con nombre "Ingeniería de Software"
    When un Docente intenta crear una materia con ese mismo nombre
    Then el sistema muestra un error inline en el formulario
    And no navega fuera de la pantalla de alta
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume endpoints ya implementados, sin decisiones nuevas.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/Materias.tsx`, `frontend/src/pages/NuevaMateria.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.1 (`#materias`), §2.2 (`#nueva-materia`).
Prototipo navegable: `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/Materias.tsx` | Grilla de materias, tarjeta "Nueva materia" |
| `frontend/src/pages/NuevaMateria.tsx` | Formulario de alta — campo nombre, validación inline de duplicado |
| `frontend/src/router.tsx` | Reemplazar el placeholder de `/materias` por las pantallas reales |

---

## Referencias

- Relacionada con: `US-2.1.1` (backend), `US-2.1.8` (infraestructura, precondición)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 1 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
