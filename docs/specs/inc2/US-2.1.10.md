# US-2.1.10: Docente ve y filtra el banco de preguntas de una materia

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.1.7`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver la tabla de preguntas de una materia y filtrarla por unidad, tema, dificultad e
importancia**
para **encontrar rápidamente las preguntas que necesito (RF-06)**.

---

## Contexto del dominio

### Problema

`GET /bancos/{id}/preguntas` con filtros existe desde `US-2.1.7`, pero sin esta US no hay forma
visual de consultarlo. Es también el punto de entrada a cargar/editar/eliminar preguntas
(`US-2.1.11` a `US-2.1.13`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `GET /bancos/{id}/preguntas?unidad=&tema=&dificultad=&importancia=` | Ya existe (`US-2.1.7`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.9` implementada (hay al menos una materia para navegar hasta su banco).

### Postcondicion

- Tabla con las preguntas activas de la materia seleccionada, columnas: texto (truncado), tipo,
  unidad/tema, dificultad, importancia, acciones.
- Cambiar cualquier filtro dispara una nueva consulta y refresca la tabla.
- Combinación de filtros sin resultados → tabla vacía, sin mensaje de error (es un resultado
  válido, no una excepción).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Solo se muestran preguntas activas — igual que el backend (`US-2.1.6`, `US-2.1.7`), sin lógica de filtrado adicional en el cliente. |

---

## Criterios de aceptacion

```gherkin
Feature: Banco de preguntas — listado y filtro (US-2.1.10)

  Scenario: Ver el banco sin filtros
    Given un Docente autenticado navega al banco de "Ingeniería de Software"
    When la pantalla carga
    Then ve todas las preguntas activas de esa materia en la tabla

  Scenario: Filtrar por dificultad
    Given el Docente en la pantalla del banco
    When selecciona dificultad = "Alto"
    Then la tabla se actualiza mostrando solo preguntas activas con dificultad Alto

  Scenario: Filtro sin resultados
    Given el Docente en la pantalla del banco
    When aplica una combinación de filtros sin preguntas que la cumplan
    Then la tabla queda vacía, sin mensaje de error
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/Banco.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.3 (`#banco`). Prototipo navegable:
`docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/Banco.tsx` | Tabla + barra de filtros, acciones por fila (editar/eliminar), botón "Nueva pregunta" |
| `frontend/src/router.tsx` | Reemplazar el placeholder de `/materias/:id/banco` por la pantalla real |

---

## Referencias

- Relacionada con: `US-2.1.7` (backend), `US-2.1.9` (navegación de entrada), `US-2.1.11` a `US-2.1.13` (acciones desde esta pantalla)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 1 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
