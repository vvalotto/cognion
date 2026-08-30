# US-3.4.9: Docente edita el título de una actividad ya creada

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat backend + frontend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (nuevo evento, sin invariantes de dominio)
**Bounded Context**: Actividad Evaluativa
**Origen**: hallazgo de UAT manual en navegador real (docente: materias → actividades →
detalle), 2026-08-30. Issue [#186](https://github.com/vvalotto/cognion/issues/186).

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **poder corregir o completar el título de una actividad ya creada**
para **no quedar atado a como la titulé al crearla, sobre todo si la dejé sin título**.

---

## Contexto del dominio

### Problema

El campo `titulo` (agregado a `ActividadEvaluativaPeriodoAbierto` en `US-3.4.2`, sin haberse
contemplado en el wireframe aprobado) solo se define al crear la actividad
([fix del input de creación, PR #185](https://github.com/vvalotto/cognion/pull/185)) — no hay
ningún endpoint para editarlo después. `PATCH /actividades/{id}/periodo` (`US-3.3.1`) solo toca
`fecha_cierre`.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Evento nuevo | `TituloActividadModificado(actividad_id, nuevo_titulo)` | Cuarto evento posible del stream (después de `ActividadEvaluativaCreada`, `PeriodoDisponibilidadModificado`, `ActividadEvaluativaCerrada`) |
| Comando | `ModificarTituloActividad(actividad_id, nuevo_titulo)` | Sin invariantes de dominio — a diferencia de `fecha_cierre`, el título es texto libre sin restricciones de negocio |
| Use Case nuevo | `ModificarTituloActividadUseCase` | Carga el stream, valida que la actividad exista (`ActividadNoExiste`), emite el evento |
| Endpoint nuevo | `PATCH /actividades/{id}/titulo` | Rol `docente` |

**A diferencia de `ModificarPeriodoDisponibilidad`:** no hay `ActividadYaCerrada` — el título
puede editarse en cualquier estado, incluso con la actividad cerrada manualmente (corregir un
título no tiene el mismo riesgo que reabrir un período ya cerrado).

---

## Especificacion del comportamiento

### Precondicion

- Una `ActividadEvaluativaPeriodoAbierto` con stream existente.

### Postcondicion

- `PATCH /actividades/{id}/titulo` con `{"nuevo_titulo": "..."}` → 200, `GET /actividades/{id}`
  refleja el nuevo título de inmediato.
- Funciona igual si la actividad está cerrada manualmente (`cerrada_manualmente = true`).
- `actividad_id` inexistente → 404 (`ActividadNoExiste`).

### Invariantes verificadas

- Ninguna invariante de dominio nueva — sin restricciones sobre el contenido de `nuevo_titulo`
  (incluido vacío, para poder "borrar" el título y volver al fallback de fecha en la UI).

---

## Casos de prueba (BDD-style, Gherkin)

```gherkin
Feature: Edición de título de una actividad

  Scenario: Docente edita el título de una actividad vigente
    Given una actividad de período abierto creada con título "Parcial 1"
    When un Docente ejecuta PATCH /actividades/{id}/titulo con nuevo_titulo="Parcial 1 (final)"
    Then la respuesta es 200
    And GET /actividades/{id} devuelve titulo="Parcial 1 (final)"

  Scenario: Docente edita el título de una actividad ya cerrada
    Given una actividad de período abierto cerrada manualmente
    When un Docente ejecuta PATCH /actividades/{id}/titulo con un nuevo título
    Then la respuesta es 200

  Scenario: Rechazo por actividad inexistente
    When un Docente ejecuta PATCH /actividades/{id}/titulo sobre un id inexistente
    Then la respuesta es 404
```

---

## Plan de implementacion

| Archivo | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/eventos.py` | `TituloActividadModificado` |
| `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py` | Caso nuevo en `_aplicar_evento` |
| `src/actividad_evaluativa/use_cases/modificar_titulo_actividad.py` | `ModificarTituloActividadUseCase` (nuevo) |
| `src/actividad_evaluativa/interface_adapters/controllers/actividades_controller.py` | Método `modificar_titulo`, cuarto Use Case inyectado — vigilar CBO (patrón repetido en este controller desde `US-2.1.2`) |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Wiring del Use Case nuevo |
| `src/actividad_evaluativa/frameworks/api/schemas.py` | `ModificarTituloRequest` |
| `src/actividad_evaluativa/frameworks/api/actividades_router.py` | `PATCH /actividades/{id}/titulo` |
| `frontend/src/lib/actividad-evaluativa-api.ts` | `modificarTitulo(actividadId, nuevoTitulo)` |
| `frontend/src/pages/EditarTituloActividad.tsx` | Formulario de un campo, mismo patrón que `ExtenderPlazo.tsx` |
| `frontend/src/pages/ActividadDetalle.tsx` | Acción "Editar título" |
| `frontend/src/router.tsx` | Ruta `/actividad-evaluativa/actividades/:actividadId/editar-titulo` |

---

## Fuera de alcance

- Cualquier invariante de negocio sobre el contenido del título (longitud máxima, caracteres
  permitidos) — no lo pidió el hallazgo de UAT ni el wireframe.
