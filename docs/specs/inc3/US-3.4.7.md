# US-3.4.7: Estudiante finaliza su evaluación y ve la revisión completa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-3.2.3`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **finalizar mi evaluación cuando termine, y ver de inmediato el detalle de cada
pregunta con lo que respondí y si estuvo bien**
para **conocer mi resultado sin esperar a que el docente lo publique (RF-13)**.

---

## Contexto del dominio

### Problema

`POST /evaluaciones/{id}/finalizar` (`US-3.2.3`) y `GET .../revision` (`revision_router.py`,
`US-3.2.3`) ya existen y no cambian — esta US solo construye la pantalla que los invoca. Sin
ella no hay forma de finalizar ni ver la revisión desde la aplicación real.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /evaluaciones/{id}/finalizar` | Ya existe (`US-3.2.3`) |
| Endpoint consumido | `GET /evaluaciones/{id}/revision` | Ya existe (`US-3.2.3`), devuelve `RevisionEvaluacionResponse` |

---

## Especificacion del comportamiento

### Precondicion

- `US-3.4.6` implementada (se finaliza desde dentro de `#est-rendir`, o automáticamente por
  `VerificadorDeVencimientos`, `US-3.2.4`).

### Postcondicion

- Finalización exitosa (manual o automática) → `#est-revision`: barra resumen
  (correctas/incorrectas/total) + detalle por pregunta (enunciado, `Badge` correcta/incorrecta,
  respuesta propia, y — solo si falló — la respuesta correcta).
- Accesible también desde el listado de actividades (`US-3.4.5`) cuando el `Badge` es
  "Finalizada — ver revisión", sin límite de tiempo posterior.

### Invariantes

| ID | Invariante |
|----|------------|
| — | La revisión nunca es visible antes de `EvaluacionFinalizada` — ni siquiera parcialmente durante `#est-rendir` (RF-13, ya garantizado por el backend desde `US-3.2.3`; esta US no agrega ninguna ruta de acceso previa). |

---

## Criterios de aceptacion

```gherkin
Feature: Finalización y revisión de la evaluación (US-3.4.7)

  Scenario: Finalizar manualmente
    Given un Estudiante en #est-rendir con al menos una pregunta respondida
    When elige finalizar
    Then el sistema finaliza la Evaluacion
    And navega a #est-revision

  Scenario: Ver revisión con aciertos y errores
    Given una Evaluacion Finalizada con 7 respuestas correctas y 3 incorrectas
    When el Estudiante entra a la revisión
    Then ve el resumen "7 correctas, 3 incorrectas, 10 total"
    And cada pregunta incorrecta muestra también la respuesta correcta

  Scenario: Acceso posterior desde el listado
    Given una actividad ya finalizada por el Estudiante
    When entra al listado de actividades y elige esa tarjeta
    Then va directo a la revisión, sin pasar por #est-rendir
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume dos endpoints ya implementados.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/RevisionEvaluacion.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-actividad-evaluativa.md` §3.5 (`#est-revision`). Prototipo:
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/RevisionEvaluacion.tsx` | Nueva — resumen + detalle por pregunta |
| `frontend/src/router.tsx` | Ruta `/mis-actividades/:actividadId/revision` |

---

## Referencias

- Relacionada con: `US-3.2.3` (backend consumido), `US-3.2.4` (finalización automática, mismo flujo de llegada), `US-3.4.5`/`US-3.4.6` (navegación de entrada)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
