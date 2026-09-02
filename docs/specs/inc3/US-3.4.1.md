# US-3.4.1: Infraestructura de frontend de Actividad Evaluativa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.4`
**Tipo**: `feat frontend` (técnica)
**Agregado principal afectado**: — (soporte técnico, sin lógica de dominio propia)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **las rutas y el cliente API del BC Actividad Evaluativa montados en el frontend**
para **tener la base sobre la que se construyen las 6 US de pantallas siguientes
(`US-3.4.2` a `US-3.4.7`)**.

---

## Contexto del dominio

### Problema

El cliente HTTP con manejo de JWT/401/403 ya existe (`US-1.1.6`), y el guard de rol
`RequireRole` ya existe (`US-1.1.9`, usado hasta ahora solo con `administrador`/`docente`) —
esta US los reutiliza sin cambios. Falta el routing y las funciones de API específicas de este
BC, para los dos actores que lo consumen (Docente y, por primera vez en el frontend,
Estudiante).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (reutilizado) | `api-client.ts` (`US-1.1.6`) | JWT, manejo de 401/403 — sin cambios |
| Cliente API (nuevo) | `actividad-evaluativa-api.ts` | Funciones tipadas para los endpoints de `/actividades` y `/evaluaciones` |
| Routing | `router.tsx` | Rutas nuevas bajo `/actividad-evaluativa/*` (docente) y `/mis-actividades/*` (estudiante) |

---

## Especificacion del comportamiento

### Precondicion

- `US-1.1.6` implementada (cliente API base, `RequireRole`).
- Backend de las Iteraciones 1 a 3 implementado (`US-3.1.1` a `US-3.3.2`).

### Postcondicion

- Rutas del BC registradas en `router.tsx`: `RequireRole rol="docente"` para las de
  `/actividad-evaluativa/*`, `RequireRole rol="estudiante"` para las de `/mis-actividades/*`
  (primer uso de ese rol en el guard — hasta ahora solo se usó con `administrador`/`docente`).
- `actividad-evaluativa-api.ts` expone funciones para cada endpoint consumido por `US-3.4.2` a
  `US-3.4.7`.
- Sin pantallas visibles todavía — placeholders, hasta que cada US siguiente las reemplace
  (mismo patrón que `US-2.1.8`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Ningún actor sin rol `docente` puede acceder a `/actividad-evaluativa/*`; ningún actor sin rol `estudiante` puede acceder a `/mis-actividades/*` — mismo guard `RequireRole` de `US-1.1.9`. |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de frontend de Actividad Evaluativa (US-3.4.1)

  Scenario: Ruta de docente protegida por rol
    Given un Usuario autenticado con rol distinto de docente
    When intenta navegar a /actividad-evaluativa/materias
    Then el sistema lo redirige fuera de la ruta

  Scenario: Ruta de estudiante protegida por rol
    Given un Usuario autenticado con rol distinto de estudiante
    When intenta navegar a /mis-actividades/materias
    Then el sistema lo redirige fuera de la ruta

  Scenario: Cliente API disponible
    Given el módulo actividad-evaluativa-api.ts
    When se invoca cualquiera de sus funciones
    Then reutiliza el mismo manejo de JWT/401/403 que api-client.ts (US-1.1.6)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — reutiliza la infraestructura de `US-1.1.6`/`US-1.1.9` sin cambios de arquitectura.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/router.tsx`, `frontend/src/lib/actividad-evaluativa-api.ts`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

No aplica — sin pantalla propia, es soporte técnico (mismo criterio que `US-2.1.8`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/actividad-evaluativa-api.ts` | Nuevo — funciones tipadas para `/actividades` y `/evaluaciones`, completadas incrementalmente por `US-3.4.2` a `US-3.4.7` |
| `frontend/src/router.tsx` | Rutas nuevas bajo `/actividad-evaluativa/*` (`RequireRole rol="docente"`) y `/mis-actividades/*` (`RequireRole rol="estudiante"`) |

---

## Referencias

- Relacionada con: `US-1.1.6` (infraestructura reutilizada), `US-3.1.1` a `US-3.3.2` (backend consumido)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` §Iteración 4

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
