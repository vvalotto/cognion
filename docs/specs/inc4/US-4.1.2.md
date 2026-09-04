# US-4.1.2: Estudiante consulta su propio desempeño en una materia

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **ver mi desempeño en una materia — detalle por evaluación finalizada y un resumen
acumulado**
para **saber cómo me está yendo en la cursada, sin tener que sumar a mano el resultado de cada
evaluación (RF-15)**.

---

## Contexto del dominio

### Problema

`US-4.1.1` ya expone `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas`, que
devuelve una fila por `Evaluacion` finalizada con sus correctas/incorrectas. Falta el Use Case
que arma la respuesta completa que pide RF-15: el detalle fila por fila **y** el acumulado —
ambos derivados de la misma lectura, sin necesidad de una segunda fuente
(`BC-analytics-modelo.md` §6, hot spot 3, ya resuelto en el modelado).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Use Case (nuevo) | `ObtenerDesempenoEstudianteUseCase` | Llama `listar_evaluaciones_finalizadas(estudiante_id, materia_id)` una sola vez y arma: la lista tal cual (detalle) + el acumulado (suma de correctas, suma de incorrectas, % de acierto, cantidad de evaluaciones) |
| Controller (nuevo) | `AnalyticsController` | Resuelve `estudiante_id` desde el token de sesión (`get_current_user`, `ADR-019`) — nunca de un parámetro de URL, evita que un estudiante consulte el desempeño de otro |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/mi-desempeno` | Rol `estudiante` (`require_rol`, `ADR-019`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.1.1` implementada.
- Estudiante autenticado (JWT válido, rol `estudiante`).

### Postcondicion

- `materia_id` con `Evaluacion` finalizadas del estudiante → respuesta 200 con:
  - `evaluaciones`: lista de `{evaluacion_id, actividad_id, finalizada_en,
    cantidad_correctas, cantidad_incorrectas}`, ordenada por `finalizada_en` descendente (más
    reciente primero).
  - `resumen`: `{total_correctas, total_incorrectas, porcentaje_acierto,
    cantidad_evaluaciones}` — `porcentaje_acierto` redondeado, `0` si `cantidad_evaluaciones`
    es `0` (sin dividir por cero).
- `materia_id` sin ninguna `Evaluacion` finalizada del estudiante → 200 con `evaluaciones: []`
  y `resumen` en cero (no es un error — el estudiante todavía no finalizó ninguna, `#est-
  desempeno` lo muestra como estado vacío en `US-4.1.3`).
- Sin JWT válido → 401. Rol distinto de `estudiante` → 403.

### Invariantes

| ID | Invariante |
|----|------------|
| — | `estudiante_id` siempre sale del token, nunca de un parámetro de la request — un estudiante no puede pedir el desempeño de otro por esta vía (esa consulta es exclusiva del Docente, `US-4.2.1`, con su propio endpoint y su propia verificación de rol). |
| — | `porcentaje_acierto` se calcula sobre el total de respuestas correctas/incorrectas acumuladas, no sobre la cantidad de evaluaciones — coherente con cómo se ve en `#est-desempeno`. |

---

## Criterios de aceptacion

```gherkin
Feature: Estudiante consulta su propio desempeño (US-4.1.2)

  Scenario: Desempeño con evaluaciones finalizadas
    Given un Estudiante autenticado con 2 Evaluacion finalizadas en la materia X
    When hace GET /analytics/materias/X/mi-desempeno
    Then recibe 200 con 2 filas en "evaluaciones" y el "resumen" acumulado correcto

  Scenario: Materia sin evaluaciones finalizadas
    Given un Estudiante autenticado sin ninguna Evaluacion finalizada en la materia Y
    When hace GET /analytics/materias/Y/mi-desempeno
    Then recibe 200 con "evaluaciones": [] y "resumen" en cero

  Scenario: Sin autenticación
    Given una request sin JWT válido
    When hace GET /analytics/materias/X/mi-desempeno
    Then recibe 401

  Scenario: Rol distinto de Estudiante
    Given un Docente autenticado
    When hace GET /analytics/materias/X/mi-desempeno
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — compone el puerto ya definido en `US-4.1.1`, sin fuente de datos nueva ni patrón
  distinto de RBAC (`ADR-019`, ya usado en todos los endpoints del proyecto).

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [x] Use Cases — `ObtenerDesempenoEstudianteUseCase` (nuevo)
- [x] Interface Adapters — `AnalyticsController` (nuevo)
- [x] Frameworks — `analytics_router.py` (agrega el `GET`), `dependencies.py` (cablea el
  controller)
- [ ] Frontend — no aplica a esta US (`US-4.1.3`)

---

## Fuente de verdad UX

No aplica a esta US — endpoint backend puro. La pantalla que lo consume (`#est-desempeno`) se
especifica en `US-4.1.3` contra `docs/design/ux/wireframes-analytics.md` §2.0.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/use_cases/obtener_desempeno_estudiante.py` | Nuevo — `ObtenerDesempenoEstudianteUseCase` |
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | Nuevo — `AnalyticsController` |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega `GET /materias/{materia_id}/mi-desempeno` |
| `src/analytics/frameworks/dependencies.py` | Cablea `AnalyticsController` |
| `tests/unit/inc4/test_obtener_desempeno_estudiante.py` | Tests del Use Case |
| `tests/integration/inc4/test_analytics_router.py` | Tests del endpoint (200/401/403, casos vacío/con datos) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §4 (query
  `ObtenerDesempenoPorEvaluacion` + `ObtenerDesempenoAcumuladoPorMateria`, unificadas acá en un
  solo endpoint porque ambas se muestran juntas en la misma pantalla, `US-4.1.3`)
- Depende de: `US-4.1.1` (#232)
- Consumida por: `US-4.1.3`, y reutilizada por `US-4.2.1` (Docente, mismo Use Case)
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 1

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
