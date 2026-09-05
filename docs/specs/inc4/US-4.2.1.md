# US-4.2.1: Docente consulta el desempeño de un estudiante elegido

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver el desempeño de un estudiante que yo elijo — mismo detalle que ve el propio
estudiante**
para **hacer seguimiento individual sin depender de que el estudiante comparta su propio
resultado (RF-16)**.

---

## Contexto del dominio

### Problema

`ObtenerDesempenoEstudianteUseCase` (`US-4.1.2`) ya arma detalle + resumen a partir de
`estudiante_id`/`materia_id` — el mismo cálculo sirve para el Docente, cambiando solo el origen
del `estudiante_id` (elegido en vez del propio) y el rol/endpoint. No hace falta un Use Case
nuevo (`BC-analytics-modelo.md` §4).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Use Case (reutilizado) | `ObtenerDesempenoEstudianteUseCase` (`US-4.1.2`) | Sin cambios — se invoca con el `estudiante_id` del path en vez del token |
| Controller | `AnalyticsController` (`US-4.1.2`) | Nuevo método `obtener_desempeno_de_estudiante(docente_id_ignorado, estudiante_id, materia_id)` — o firma equivalente que no reciba el `estudiante_id` del token |
| Endpoint (nuevo) | `GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno` | Rol `docente` (`require_rol`, `ADR-019`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.1.2` implementada.
- Docente autenticado (JWT válido, rol `docente`).
- `estudiante_id` del path corresponde a un `Usuario` con perfil Estudiante existente (no se
  valida pertenencia a ninguna comisión particular del docente — hot spot resuelto).

### Postcondicion

- `estudiante_id` con `Evaluacion` finalizadas en `materia_id` → 200, mismo shape de respuesta
  que `US-4.1.2` (`evaluaciones` + `resumen`).
- `estudiante_id` sin ninguna `Evaluacion` finalizada en `materia_id` → 200 con `evaluaciones:
  []` y `resumen` en cero (no es un error).
- Sin JWT válido → 401. Rol distinto de `docente` → 403.
- `estudiante_id` inexistente → 404 (a diferencia de `US-4.1.2`, que nunca puede recibir un
  `estudiante_id` inválido porque sale del token).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Cualquier Docente autenticado puede consultar el desempeño de cualquier Estudiante — RBAC estándar (rol `docente`), sin restricción de pertenencia a una comisión que el Docente dicte (hot spot de autorización resuelto con Víctor, 2026-09-04). |
| — | El cálculo de correctas/incorrectas/porcentaje es exactamente el mismo que `US-4.1.2` — no se duplica lógica, solo cambia el origen del `estudiante_id`. |

---

## Criterios de aceptacion

```gherkin
Feature: Docente consulta el desempeño de un estudiante elegido (US-4.2.1)

  Scenario: Estudiante con evaluaciones finalizadas
    Given un Docente autenticado y un Estudiante con 2 Evaluacion finalizadas en la materia X
    When el Docente hace GET /analytics/materias/X/estudiantes/{estudiante_id}/desempeno
    Then recibe 200 con 2 filas en "evaluaciones" y el "resumen" acumulado correcto

  Scenario: Estudiante sin evaluaciones finalizadas
    Given un Docente autenticado y un Estudiante sin ninguna Evaluacion finalizada en materia Y
    When el Docente hace GET /analytics/materias/Y/estudiantes/{estudiante_id}/desempeno
    Then recibe 200 con "evaluaciones": [] y "resumen" en cero

  Scenario: Estudiante inexistente
    Given un Docente autenticado
    When hace GET /analytics/materias/X/estudiantes/{id-inexistente}/desempeno
    Then recibe 404

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/estudiantes/{otro_estudiante_id}/desempeno
    Then recibe 403
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — reutiliza el Use Case de `US-4.1.2` sin cambios, mismo patrón de RBAC (`ADR-019`).

**Capa(s) afectadas:**
- [ ] Entities — sin cambios
- [ ] Use Cases — sin cambios (`ObtenerDesempenoEstudianteUseCase` se reutiliza tal cual)
- [x] Interface Adapters — `AnalyticsController` gana un método nuevo (o firma extendida)
- [x] Frameworks — `analytics_router.py` (agrega el `GET`), validación de existencia del
  estudiante vía `UsuarioRepositoryPort` u órgano equivalente
- [ ] Frontend — no aplica a esta US (`US-4.2.5`)

---

## Fuente de verdad UX

No aplica a esta US — endpoint backend puro. La pantalla que lo consume
(`#doc-desempeno-alumno`) se especifica en `US-4.2.5` contra
`docs/design/ux/wireframes-analytics.md` §3.0.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/interface_adapters/controllers/analytics_controller.py` | Nuevo método para desempeño de un estudiante elegido |
| `src/analytics/frameworks/api/analytics_router.py` | Agrega `GET /materias/{materia_id}/estudiantes/{estudiante_id}/desempeno` |
| `tests/integration/inc4/test_analytics_router.py` | Tests del endpoint (200/401/403/404, casos vacío/con datos) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §4
- Depende de: `US-4.1.2` (#233) — sin dependencia de otra US de esta iteración
- Consumida por: `US-4.2.5`
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 2
- Issue: #240

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
