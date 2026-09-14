# US-ADJ-51: Docente ve la completitud de una actividad puntual

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver, para una actividad puntual que dicto, el estado de cada estudiante del roster
aplicable**
para **saber quién todavía no rindió antes de que cierre el período (RF-23)**.

---

## Contexto del dominio

### Problema

`US-ADJ-47` ya expone `GET /analytics/actividades/{actividad_id}/completitud`. Falta la
pantalla, accesible desde el detalle de una actividad ya existente (`ActividadDetalle.tsx`,
`US-3.4.4`) — no es una entrada directa del menú de Analytics (`wireframes-analytics.md` §3.5).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | `obtenerCompletitudPorActividad(actividadId)` | Sobre `apiFetch`/`ApiError` |
| Pantalla (nueva) | `CompletitudActividad.tsx` | Resumen `.completitud-summary` (4 números) + tabla por estudiante |
| Ruta (nueva) | `/actividad-evaluativa/actividades/:actividadId/completitud` | Protegida con `RequireRole rol="docente"` — vive en el namespace de Actividad Evaluativa por ser accedida desde `ActividadDetalle.tsx`, no en `/analytics/*` |

---

## Especificacion del comportamiento

### Precondicion

- `US-ADJ-47` implementada.
- `US-3.4.4` (`ActividadDetalle.tsx`) implementada — el entry point vive ahí.
- Docente autenticado.

### Postcondicion

- Entry point: `ActividadDetalle.tsx` gana un botón/link "Ver completitud" que navega a la
  ruta nueva con el `actividadId` ya conocido en ese contexto.
- Breadcrumb "Actividades › {título de la actividad} › Completitud".
- Resumen `.completitud-summary`: 4 números (Finalizadas, En curso, Suspendidas, Sin iniciar).
- Tabla: una fila por estudiante — Nombre, Comisión, Estado (`.state-badge` con 4 variantes de
  color, una por estado) — roster de la(s) comisión(es) a la(s) que la actividad está
  restringida, o de toda la materia si no hay restricción (mismo criterio del backend,
  `US-ADJ-47`).
- Columna Comisión: se omite en la tabla si la actividad está restringida a una sola comisión
  (no aporta información); se muestra si mezcla más de una (actividad sin restricción).
- Sin ningún estudiante en el roster aplicable (caso no esperado en la práctica): sin manejo
  especial — mismo criterio del backend, `US-ADJ-47`.

### Invariantes

| ID | Invariante |
|----|------------|
| — | El resumen (4 números) siempre coincide con la suma de estados de la tabla — ambos vienen de la misma respuesta del backend, sin cálculo propio del frontend. |
| — | Esta pantalla nunca es una entrada directa del menú de Analytics — solo se llega desde el detalle de una actividad concreta. |

---

## Criterios de aceptacion

```gherkin
Feature: Completitud de una actividad (US-ADJ-51)

  Scenario: Actividad restringida a una comisión
    Given un Docente en el detalle de una actividad restringida a una sola comisión
    When hace click en "Ver completitud"
    Then ve el resumen de 4 números y la tabla sin columna de Comisión (una sola comisión)

  Scenario: Actividad sin restricción de comisión
    Given una actividad visible a toda la materia (más de una comisión)
    When el Docente ve su completitud
    Then la tabla muestra la columna Comisión, con estudiantes de ambas comisiones

  Scenario: Estados variados renderizados con badge de color
    Given una actividad con estudiantes finalizados, en curso, suspendidos y sin iniciar
    When se renderiza la tabla
    Then cada estado se ve con su propia variante de color de `.state-badge`

  Scenario: Acceso sin rol Docente
    Given un Estudiante o Administrador autenticado
    When intenta acceder directamente a la ruta de completitud
    Then es redirigido por RequireRole, no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, agrega un botón a una pantalla ya existente y una pantalla nueva de
  solo lectura.

**Capa(s) afectadas:**
- [ ] Backend — sin cambios
- [x] Frontend — cliente API (1 función nueva, en `analytics-api.ts` a pesar de vivir en la
  ruta de Actividad Evaluativa, mismo criterio que el endpoint backend), pantalla
  `CompletitudActividad.tsx`, botón nuevo en `ActividadDetalle.tsx`, ruta nueva en
  `router.tsx` protegida con `RequireRole rol="docente"`, sin entrada en `AppNav.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §3.5 (`#doc-completitud-actividad`). Prototipo:
`docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Agrega `obtenerCompletitudPorActividad(actividadId)` |
| `frontend/src/pages/analytics/CompletitudActividad.tsx` | Nueva pantalla |
| `frontend/src/pages/actividad_evaluativa/ActividadDetalle.tsx` | Botón/link "Ver completitud" |
| `frontend/src/router.tsx` | Ruta nueva, `RequireRole rol="docente"` |
| Tests Vitest correspondientes | Con/sin columna de Comisión, badges por estado, RBAC |

---

## Referencias

- Depende de: `US-ADJ-47`, `US-3.4.4`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#361](https://github.com/vvalotto/cognion/issues/361)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
