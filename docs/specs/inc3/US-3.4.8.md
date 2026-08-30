# US-3.4.8: Fix — comparación de datetimes naive/aware rompe listado y detalle de actividades

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `fix backend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (sin cambios de invariantes de dominio)
**Bounded Context**: Actividad Evaluativa
**Origen**: hallazgo de UAT manual en navegador real (docente: materias → actividades → nueva
actividad → listado), 2026-08-30. Issue [#183](https://github.com/vvalotto/cognion/issues/183).

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que el listado y el detalle de mis actividades no rompan después de crear una
actividad desde la pantalla real**
para **poder usar el flujo completo de Actividad Evaluativa (US-3.4.2 a US-3.4.4) sin
depender de armar las fechas a mano contra la API**.

---

## Contexto del dominio

### Problema

`GET /actividades` (`US-3.4.2`, ya cerrada) y `GET /actividades/{id}` (`US-3.4.4`) responden
`500 Internal Server Error` en cuanto existe al menos una actividad creada desde la UI real —
el navegador lo reporta como error de CORS (Starlette no agrega headers CORS a una excepción
no capturada), pero la causa real es:

```
TypeError: can't compare offset-naive and offset-aware datetimes
  actividades_router.py:64, en _estado_actividad()
  if resumen.cerrada_manualmente or resumen.fecha_cierre <= ahora:
```

- `<input type="datetime-local">` del formulario "Nueva actividad" (`NuevaActividad.tsx`,
  `US-3.4.3`) manda fechas sin offset de timezone (ej. `2026-08-30T17:00`).
- `CrearActividadRequest.fecha_apertura`/`fecha_cierre` (Pydantic `datetime`, sin validador)
  las acepta tal cual → quedan **naive**, se persisten así en el evento
  `ActividadEvaluativaCreada` y se leen naive de vuelta al reconstruir el aggregate.
- `_estado_actividad` compara esa fecha contra `datetime.now(UTC)` (**aware**) → `TypeError`.

Ningún test automatizado lo agarró porque arman las fechas con
`datetime.now(UTC).isoformat()` (aware) en vez de simular el input real del navegador — mismo
patrón que el gap de CORS de `US-1.1.6`/`US-1.1.7` (invisible a Vitest mockeado, visible recién
en navegador real).

### Alcance del fix

Normalizar en el boundary de la API (Pydantic): si el datetime que llega en
`CrearActividadRequest.fecha_apertura`/`fecha_cierre` o en
`ModificarPeriodoDisponibilidadRequest.nueva_fecha_cierre` no trae tzinfo, se le asigna UTC.
Es una simplificación conocida y documentada — el navegador no manda el timezone real del
usuario, así que la hora local ingresada se trata como si fuera UTC. **No se rediseña el
manejo de timezone de punta a punta** (eso implicaría tocar el formulario del frontend para
mandar el offset real, fuera de alcance de este fix).

---

## Especificacion del comportamiento

### Precondicion

- Una actividad ya fue creada con `fecha_apertura`/`fecha_cierre` naive (como las manda el
  navegador real).

### Postcondicion

- `GET /actividades?materia_id=...` responde 200 sin importar si la fecha de origen llegó con
  o sin offset de timezone.
- `PATCH /actividades/{id}/periodo` con `nueva_fecha_cierre` naive tampoco rompe.
- El fix vive en `schemas.py` (usado por ambos endpoints), así que `GET /actividades/{id}`
  (`US-3.4.4`, todavía sin mergear a `develop` al momento de este fix, PR
  [#182](https://github.com/vvalotto/cognion/pull/182)) queda cubierto automáticamente al
  mergear esa branch sobre `develop` con este fix ya integrado — no se agrega un test de
  regresión propio para ese endpoint en esta US porque el endpoint no existe todavía en
  `develop`.
- Actividades ya creadas con fecha aware (tests existentes, API directa) siguen funcionando
  igual — el fix no cambia su comportamiento.

### Invariantes verificadas

- Ninguna invariante de dominio nueva — el fix es de robustez en el boundary HTTP, no de
  reglas de negocio.

---

## Casos de prueba (BDD-style, Gherkin)

```gherkin
Feature: Robustez de fechas naive/aware en Actividad Evaluativa

  Scenario: Listar actividades cuando la fecha se creó sin timezone (como manda el navegador)
    Given una actividad de período abierto creada con fecha_apertura y fecha_cierre naive
    When un Docente pide GET /actividades?materia_id=<materia_id>
    Then la respuesta es 200
    And el estado derivado de la actividad es correcto (en_curso/programada/cerrada)

  Scenario: Modificar el período con una nueva fecha de cierre naive
    Given una actividad de período abierto vigente
    When un Docente ejecuta PATCH /actividades/{id}/periodo con nueva_fecha_cierre naive
    Then la respuesta es 200 y la actividad queda con la nueva fecha de cierre
```

---

## Plan de implementacion

| Archivo | Cambio |
|---|---|
| `src/actividad_evaluativa/frameworks/api/schemas.py` | Validador Pydantic (`field_validator`) en `fecha_apertura`/`fecha_cierre` de `CrearActividadRequest` y `nueva_fecha_cierre` de `ModificarPeriodoDisponibilidadRequest`: si `dt.tzinfo is None`, asignar `UTC` |
| `tests/unit/inc3/` o `tests/integration/inc3/` | Test de regresión que reproduce el escenario real (fecha_apertura/fecha_cierre naive) contra listar/obtener/modificar |

---

## Fuera de alcance

- Rediseño de manejo de timezone de punta a punta (mandar el offset real desde el frontend).
- Cualquier cambio a `US-3.4.2`/`US-3.4.3`/`US-3.4.4` fuera de este fix puntual.
