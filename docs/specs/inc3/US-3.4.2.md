# US-3.4.2: Docente ve sus materias y el listado de actividades de una materia

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat backend + frontend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (consulta, sin cambios de invariantes)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver mis materias y, dentro de cada una, el listado de actividades ya creadas**
para **ubicar rápidamente una actividad existente antes de crear una nueva o entrar a su
detalle (RF-11)**.

---

## Contexto del dominio

### Problema

`POST /actividades` existe desde `US-3.1.2`, pero **no existe ningún `GET`** en
`actividades_router.py` — gap detectado al planificar la Iteración 4: la tabla de candidatas
(`inc3-candidatas.md`) asumía que "Iteración 4 = solo frontend, consume las Iteraciones 1 a 3
tal cual", pero backend/frontend real de esta iteración recién se separó (a diferencia de
Banco de Preguntas) y nadie había construido las consultas necesarias. Decisión de Víctor: cada
US de esta iteración que lo necesite extiende el backend mínimo dentro de su propio alcance,
mismo criterio que `US-2.1.9`/`US-2.2.8` — no se abre una iteración técnica aparte.

**Materias:** reutiliza `GET /materias` (`US-2.1.9`, Banco de Preguntas) sin cambios — el
docente ya ve esa lista para el Banco de Preguntas; acá se agrega como punto de entrada
también para Actividad Evaluativa, con destino de navegación distinto.

**Listado de actividades:** no existe. `ActividadEvaluativaPeriodoAbierto` es un aggregate de
Event Sourcing (`ADR-002`) — el listado no puede reconstruir cada stream completo por
request. Mismo criterio que `EvaluacionActivaQueryPort` (`US-3.2.4`, "query de lectura sobre la
tabla `events` existente, no una proyección sincronizada", válido a esta escala de 30-60
alumnos/comisión y documentado como reversible si el volumen cambia).

| Puerto | Método nuevo | Motivo |
|---|---|---|
| `ActividadQueryPort` (nuevo) | `listar_por_materia(materia_id) -> list[ActividadResumen]` | No existe ningún método de listado sobre el stream de actividades |

`ActividadResumen` expone: `id`, `titulo`/`materia_id`, `fecha_apertura`, `fecha_cierre`,
`estado` (`en_curso` / `programada` / `cerrada`, calculado igual que el `Badge` del wireframe
§2.1 — `cerrada` si `cerrada_manualmente` **o** `fecha_cierre` ya pasada), y los conteos de
evaluaciones activas/finalizadas (reutiliza `EvaluacionActivaQueryPort.listar_no_finalizadas()`
filtrado por `actividad_id`, sin ensanchar ese puerto).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint reutilizado | `GET /materias` | Ya existe (`US-2.1.9`), sin cambios |
| Endpoint nuevo | `GET /actividades?materia_id={id}` | Lista actividades de una materia con estado y conteos; rol `docente` |
| Use Case nuevo | `ListarActividadesUseCase` | Orquesta `ActividadQueryPort.listar_por_materia()` |
| Cliente API | `actividad-evaluativa-api.ts` (`US-3.4.1`) | Se agrega `listarActividades(materiaId)`; reutiliza `listarMaterias()` de `banco-preguntas-api.ts` para `#doc-materias` |

---

## Especificacion del comportamiento

### Precondicion

- `US-3.4.1` implementada.
- Docente autenticado (rol `docente`), asignado a al menos una comisión.

### Postcondicion

- `#doc-materias`: tarjeta por materia asignada, navega al listado de actividades de esa
  materia.
- `#doc-actividades`: tarjeta por actividad de la materia elegida, con `Badge` de estado y
  conteos; botón "+ Nueva actividad" navega a `US-3.4.3`; cada tarjeta navega al detalle
  (`US-3.4.4`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El cálculo de `estado` es puramente derivado (fecha actual + `cerrada_manualmente`) — no persiste un campo `estado` propio, evita inconsistencia entre el read model y el aggregate. |

---

## Criterios de aceptacion

```gherkin
Feature: Listado de materias y actividades del Docente (US-3.4.2)

  Scenario: Ver materias
    Given un Docente autenticado con materias asignadas
    When entra a /actividad-evaluativa/materias
    Then ve una tarjeta por materia

  Scenario: Ver actividades de una materia
    Given un Docente en /actividad-evaluativa/materias
    When elige una materia
    Then ve el listado de sus actividades con estado (En curso / Programada / Cerrada)

  Scenario: Materia sin actividades
    Given una materia sin actividades creadas
    When el Docente entra a su listado
    Then ve la grilla vacía con la acción "+ Nueva actividad" disponible
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — reutiliza el mecanismo de query-sobre-`events` ya establecido por `US-3.2.4`, sin
  agregar una proyección sincronizada nueva.

**Capa(s) afectadas:**
- [x] Backend — `src/actividad_evaluativa/entities/ports/actividad_query_port.py` (nuevo),
  `use_cases/listar_actividades.py` (nuevo), `frameworks/api/actividades_router.py` (nuevo `GET`)
- [x] Frontend — `frontend/src/pages/MateriasActividades.tsx`, `Actividades.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-actividad-evaluativa.md` §2.0 (`#doc-materias`), §2.1
(`#doc-actividades`). Prototipo:
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/actividad_query_port.py` | Nuevo — `ActividadQueryPort`, `ActividadResumen` |
| `src/actividad_evaluativa/use_cases/listar_actividades.py` | Nuevo — `ListarActividadesUseCase` |
| `src/actividad_evaluativa/frameworks/api/actividades_router.py` | Nuevo `GET ""` (query param `materia_id`) |
| `frontend/src/pages/MateriasActividades.tsx` | Nueva — tarjetas de materia (`#doc-materias`) |
| `frontend/src/pages/Actividades.tsx` | Nueva — tarjetas de actividad (`#doc-actividades`) |
| `frontend/src/router.tsx` | Rutas `/actividad-evaluativa/materias`, `/actividad-evaluativa/materias/:materiaId/actividades` |

---

## Referencias

- Relacionada con: `US-3.1.2` (aggregate consultado), `US-3.2.4` (patrón de query reutilizado), `US-2.1.9` (`GET /materias` reutilizado)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
