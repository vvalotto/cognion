# US-3.4.4: Docente ve el detalle de una actividad, extiende el plazo y la cierra manualmente

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat backend + frontend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (consulta, sin cambios de invariantes)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver el detalle de una actividad, extender su plazo si hace falta, o cerrarla
manualmente antes de tiempo**
para **ajustar una actividad vigente sin depender de la API directa (RF-11b)**.

---

## Contexto del dominio

### Problema

`PATCH /actividades/{id}/periodo` (`US-3.3.1`) y `POST /actividades/{id}/cerrar` (`US-3.3.2`)
ya existen y no cambian — pero **no existe `GET /actividades/{id}`**, mismo gap de fondo que
`US-3.4.2` (ningún `GET` en `actividades_router.py` antes de esta iteración). Sin el detalle,
el docente no tiene desde dónde disparar "Extender plazo" ni "Cerrar actividad ahora": el
listado (`US-3.4.2`) alcanza para ver el estado agregado, pero no expone los datos completos
de una actividad puntual (apertura/cierre exactos, intentos permitidos).

| Puerto | Método nuevo | Motivo |
|---|---|---|
| `ActividadQueryPort` (`US-3.4.2`) | `obtener(actividad_id) -> ActividadDetalle \| None` | Solo tenía `listar_por_materia`; se agrega el detalle de una actividad puntual al mismo puerto, sin crear uno nuevo |

`ActividadDetalle` extiende `ActividadResumen` (`US-3.4.2`) con `cantidad_preguntas` e
`intentos_permitidos` — únicos campos que pide el wireframe §2.3 y que el listado no necesita.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint nuevo | `GET /actividades/{id}` | Detalle de una actividad; rol `docente` |
| Endpoint reutilizado | `PATCH /actividades/{id}/periodo` | Ya existe (`US-3.3.1`), sin cambios |
| Endpoint reutilizado | `POST /actividades/{id}/cerrar` | Ya existe (`US-3.3.2`), sin cambios |
| Use Case nuevo | `ObtenerActividadUseCase` | Orquesta `ActividadQueryPort.obtener()` |

---

## Especificacion del comportamiento

### Precondicion

- `US-3.4.2` implementada (se navega al detalle desde una tarjeta del listado).

### Postcondicion

- `#doc-detalle-actividad`: datos completos + acción "Extender plazo" (visible mientras no esté
  cerrada manualmente) + acción "Cerrar actividad ahora" (destructiva).
- `#doc-extender-plazo`: éxito → vuelve al detalle con el nuevo cierre reflejado; rechazo del
  servidor (`NoSePuedeAcortarConEvaluacionesActivas`) → mensaje inline, sin navegar.
- `#doc-cerrar-actividad`: confirmación explícita → vuelve al detalle, actividad `Cerrada`.

### Invariantes

| ID | Invariante |
|----|------------|
| — | "Extender plazo" y "Cerrar actividad ahora" no se ocultan por estado en el cliente más allá de `cerrada_manualmente` — la validación fina (INV-AE-04, evaluaciones activas) la sigue haciendo el backend; el cliente solo muestra el error inline. |

---

## Criterios de aceptacion

```gherkin
Feature: Detalle, extensión y cierre de actividad (US-3.4.4)

  Scenario: Ver detalle
    Given un Docente en el listado de actividades
    When elige una actividad
    Then ve apertura, cierre, cantidad de preguntas, intentos, evaluaciones activas y finalizadas

  Scenario: Extender plazo exitosamente
    Given un Docente en el detalle de una actividad no cerrada
    When va a "Extender plazo" y guarda una fecha de cierre posterior
    Then el sistema actualiza el cierre
    And vuelve al detalle mostrando el nuevo valor

  Scenario: Rechazo al intentar acortar con evaluaciones activas
    Given una actividad con evaluaciones activas
    When el Docente intenta guardar un cierre anterior al actual
    Then el backend responde 422 NoSePuedeAcortarConEvaluacionesActivas
    And el formulario muestra el error inline sin navegar

  Scenario: Cierre manual
    Given un Docente en el detalle de una actividad no cerrada
    When confirma "Sí, cerrar actividad ahora"
    Then el sistema cierra la actividad y finaliza en cascada sus evaluaciones activas
    And vuelve al detalle mostrando el estado Cerrada
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — extiende un puerto ya creado en `US-3.4.2`, reutiliza dos endpoints existentes sin
  cambios.

**Capa(s) afectadas:**
- [x] Backend — `entities/ports/actividad_query_port.py` (método nuevo),
  `use_cases/obtener_actividad.py` (nuevo), `frameworks/api/actividades_router.py` (nuevo `GET {id}`)
- [x] Frontend — `frontend/src/pages/ActividadDetalle.tsx`, `ExtenderPlazo.tsx`, `CerrarActividad.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-actividad-evaluativa.md` §2.3 (`#doc-detalle-actividad`), §2.4
(`#doc-extender-plazo`), §2.5 (`#doc-cerrar-actividad`). Prototipo:
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/actividad_query_port.py` | Agrega `obtener(actividad_id)` |
| `src/actividad_evaluativa/use_cases/obtener_actividad.py` | Nuevo — `ObtenerActividadUseCase` |
| `src/actividad_evaluativa/frameworks/api/actividades_router.py` | Nuevo `GET /{actividad_id}` |
| `frontend/src/pages/ActividadDetalle.tsx` | Nueva — detalle + acciones |
| `frontend/src/pages/ExtenderPlazo.tsx` | Nueva — formulario de nuevo cierre |
| `frontend/src/pages/CerrarActividad.tsx` | Nueva — confirmación destructiva |
| `frontend/src/router.tsx` | Rutas de detalle, extender y cerrar |

---

## Referencias

- Relacionada con: `US-3.3.1`, `US-3.3.2` (backend reutilizado), `US-3.4.2` (puerto extendido, navegación de entrada)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
