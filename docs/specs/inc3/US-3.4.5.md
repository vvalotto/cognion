# US-3.4.5: Estudiante ve sus materias y las actividades disponibles

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat backend + frontend`
**Agregado principal afectado**: — (consulta cruzando BCs, sin cambios de invariantes)
**Bounded Context**: Identidad (endpoint nuevo), Actividad Evaluativa (endpoint nuevo + frontend)

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **ver mis materias y, dentro de cada una, las actividades disponibles con su estado**
para **saber qué tengo pendiente de rendir, sin confundir actividades que todavía no abrieron
o que ya cerré (RF-11, RF-12)**.

---

## Contexto del dominio

### Problema

Es el primer punto de entrada de un Estudiante al frontend de Actividad Evaluativa — hasta acá
ningún BC expone nada gateado a rol `estudiante` salvo lo propio de Identidad
(`US-1.1.6`/`1.1.7`/`1.1.8`, login/registro). "Mis materias" del lado Docente reutiliza
`GET /materias` (Banco de Preguntas), pero ese endpoint está fijado a `require_docente`
(`US-2.1.9`) — no es un simple gap de "falta el `GET`", es un endpoint existente cuyo rol no
sirve para este actor. Reutilizarlo ensanchando su rol filtraría de más (un Docente ve *todas*
las materias; un Estudiante solo debe ver las de su comisión) — se decidió un endpoint nuevo,
propio de Identidad, en vez de tocar el contrato de `US-2.1.9`.

**Resolución de "materias de mi comisión":** `Estudiante.comision_id` (Identidad,
`usuario.py`) resuelve a `Comision.materia_id` (Identidad, ya expuesto como dato del propio
BC) — no hace falta cruzar a Banco de Preguntas para el `id`/`nombre` de la materia si
Identidad ya conoce `materia_id` vía `Comision`; el nombre de la materia sí vive en Banco de
Preguntas y se resuelve con el mismo `MateriaPort` que `US-2.1.2` ya usa desde Identidad
(`Comisión referencia Materia por puerto, sin imports directos entre BCs`) — sin puerto nuevo,
solo un nuevo consumidor de uno que ya existe.

**Resolución de "actividades visibles + mi estado":** el `ActividadQueryPort.listar_por_materia`
de `US-3.4.2` alcanza para el listado base, pero el `Badge` desde la perspectiva del estudiante
(`Pendiente de responder` / `Todavía no abrió` / `Finalizada — ver revisión`) necesita saber si
**ese estudiante puntual** ya tiene una `Evaluacion` `Finalizada` para cada actividad — dato que
ningún puerto expone hoy.

| BC | Puerto | Método nuevo | Motivo |
|---|---|---|---|
| Identidad | — | `GET /identidad/estudiante/materias` (endpoint nuevo, no puerto — es el propio BC dueño del dato) | No existe ningún endpoint de "mis materias" gateado a `estudiante` |
| Actividad Evaluativa | `EvaluacionActivaQueryPort` (`US-3.2.4`) o puerto nuevo — **a definir en Fase 2 de `/implement-us`, mismo criterio que el hot spot de `US-3.2.4`§8** | `existe_finalizada(actividad_id, estudiante_id) -> bool` | Ningún puerto responde "¿este estudiante ya finalizó esta actividad?" |

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint nuevo | `GET /identidad/estudiante/materias` | Materias de la comisión del Estudiante autenticado; rol `estudiante` |
| Endpoint nuevo | `GET /actividades?materia_id={id}&vista=estudiante` (o endpoint separado — a definir en Fase 2) | Actividades visibles para la comisión del Estudiante, con su `Badge` de estado; rol `estudiante` |
| Use Case nuevo | `ListarMateriasDelEstudianteUseCase` (Identidad) | Resuelve `comision_id → materia_id` y el nombre vía `MateriaPort` |
| Use Case nuevo | `ListarActividadesVisiblesUseCase` (Actividad Evaluativa) | Extiende `ListarActividadesUseCase` (`US-3.4.2`) con el estado por-estudiante |

---

## Especificacion del comportamiento

### Precondicion

- `US-3.4.1` implementada.
- Estudiante autenticado (rol `estudiante`), con `comision_id` asignada.

### Postcondicion

- `#est-materias`: tarjeta por materia de su comisión, con `Badge` resumen ("N pendiente" /
  "Sin actividades disponibles").
- `#est-actividades`: tarjeta por actividad visible, con `Badge` de estado desde su
  perspectiva; navega a `#est-rendir` (`US-3.4.6`, o `#est-suspendida` si ya tiene una
  `Evaluacion` `Suspendida`), `#est-fuera-periodo` (esta misma US, ver abajo), o `#est-revision`
  (`US-3.4.7`) según el `Badge`.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `EnCurso` y `Suspendida` no se distinguen en esta grilla — ambas caen en "Pendiente de responder" (wireframe §3.1, fuera de alcance explícito). |

---

## Criterios de aceptacion

```gherkin
Feature: Materias y actividades del Estudiante (US-3.4.5)

  Scenario: Ver materias de mi comisión
    Given un Estudiante autenticado con comisión asignada
    When entra a /mis-actividades/materias
    Then ve una tarjeta por materia de su comisión

  Scenario: Actividad pendiente de responder
    Given una actividad dentro de su período vigente, sin Evaluacion Finalizada del Estudiante
    When entra al listado de actividades de esa materia
    Then la ve con Badge "Pendiente de responder"

  Scenario: Actividad que todavía no abrió
    Given una actividad con fecha_apertura futura
    When el Estudiante entra al listado
    Then la ve con Badge "Todavía no abrió"

  Scenario: Actividad ya finalizada por el Estudiante
    Given una actividad donde el Estudiante ya tiene una Evaluacion Finalizada
    When entra al listado
    Then la ve con Badge "Finalizada — ver revisión"
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí — primer endpoint de Identidad gateado a rol `estudiante` distinto de
  login/registro/cambio de password; primer cruce Identidad→Banco de Preguntas del lado
  estudiante (reutiliza `MateriaPort` de `US-2.1.2`, sin puerto nuevo). Revisar con Víctor si el
  método `existe_finalizada` va en `EvaluacionActivaQueryPort` (ensanchando ese puerto más allá
  de "no finalizadas", su propósito original en `US-3.2.4`) o en un puerto de consulta nuevo,
  separado por command/query (mismo criterio ya aplicado en `US-2.2.2` para evitar CRITICAL de
  CBO) — decisión concreta en Fase 2 de `/implement-us`.

**Capa(s) afectadas:**
- [x] Backend — Identidad: `interface_adapters/`/`frameworks/api/` (endpoint nuevo); Actividad
  Evaluativa: extensión de `ListarActividadesUseCase` o Use Case nuevo
- [x] Frontend — `frontend/src/pages/MisMaterias.tsx`, `MisActividades.tsx`, `FueraDePeriodo.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-actividad-evaluativa.md` §3.0 (`#est-materias`), §3.1
(`#est-actividades`), §3.2 (`#est-fuera-periodo`). Prototipo:
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/frameworks/api/*.py` | Nuevo `GET /identidad/estudiante/materias` |
| `src/identidad/use_cases/listar_materias_del_estudiante.py` | Nuevo |
| `src/actividad_evaluativa/use_cases/listar_actividades_visibles.py` | Nuevo (o extensión de `listar_actividades.py` de `US-3.4.2`) |
| `frontend/src/pages/MisMaterias.tsx` | Nueva — tarjetas de materia (`#est-materias`) |
| `frontend/src/pages/MisActividades.tsx` | Nueva — tarjetas de actividad (`#est-actividades`) |
| `frontend/src/pages/FueraDePeriodo.tsx` | Nueva — estado "todavía no abrió" / "cerrada sin rendir" (`#est-fuera-periodo`) |
| `frontend/src/router.tsx` | Rutas `/mis-actividades/materias`, `/mis-actividades/materias/:materiaId`, `/mis-actividades/:actividadId/fuera-de-periodo` |

---

## Referencias

- Relacionada con: `US-2.1.2` (`MateriaPort` reutilizado), `US-3.2.4` (puerto candidato a extender), `US-3.4.2` (Use Case base del lado docente)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
