# US-2.1.8: Infraestructura de frontend del Banco de Preguntas

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (soporte técnico, sin lógica de dominio propia)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **las rutas y el cliente API del BC Banco de Preguntas montados en el frontend**
para **tener la base sobre la que se construyen las pantallas de materias, banco y carga de
preguntas (US-2.1.9 a US-2.1.13)**.

---

## Contexto del dominio

### Problema

El cliente HTTP con manejo de JWT/401/403 ya existe (`US-1.1.6`, BC Identidad) — esta US lo
reutiliza, sin duplicar lógica de autenticación. Falta el routing y las funciones de API
específicas de este dominio (`GET /materias`, `POST /materias`, `GET /bancos/{id}/preguntas`,
etc.).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (reutilizado) | `api-client.ts` (`US-1.1.6`) | JWT, manejo de 401/403 — sin cambios |
| Cliente API (nuevo) | `banco-preguntas-api.ts` | Funciones tipadas para los endpoints de este BC |
| Routing | `router.tsx` | Rutas `/materias`, `/materias/:id/banco`, `/materias/:id/banco/preguntas/nueva`, etc. — todas protegidas por `RequireRole` (rol `docente`, reutilizado de `US-1.1.9`) |

---

## Especificacion del comportamiento

### Precondicion

- `US-1.1.6` implementada (cliente API base, `RequireRole`).
- Backend de la Iteración 1 (`US-2.1.1` a `US-2.1.7`) implementado y expuesto.

### Postcondicion

- Rutas del BC Banco de Preguntas registradas en `router.tsx`, protegidas para rol `docente`.
- `banco-preguntas-api.ts` expone funciones para cada endpoint consumido por `US-2.1.9` a
  `US-2.1.13`.
- Sin pantallas visibles todavía — placeholders o redirección, hasta que cada US siguiente las
  reemplace.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Ningún actor sin rol `docente` puede acceder a estas rutas — mismo guard `RequireRole` de `US-1.1.9`. |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de frontend del Banco de Preguntas (US-2.1.8)

  Scenario: Ruta protegida por rol
    Given un Usuario autenticado con rol distinto de docente
    When intenta navegar a /materias
    Then el sistema lo redirige fuera de la ruta (mismo comportamiento que RequireRole en US-1.1.9)

  Scenario: Cliente API disponible
    Given el módulo banco-preguntas-api.ts
    When se invoca cualquiera de sus funciones
    Then reutiliza el mismo manejo de JWT/401/403 que api-client.ts (US-1.1.6)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — reutiliza la infraestructura de `US-1.1.6` sin cambios de arquitectura.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/router.tsx`, `frontend/src/api/banco-preguntas-api.ts`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

No aplica — sin pantalla propia, es soporte técnico (mismo criterio que `US-1.1.6`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/api/banco-preguntas-api.ts` | Funciones tipadas: `crearMateria`, `listarMaterias`, `filtrarBanco`, `cargarPreguntaOpcionMultiple`, `cargarPreguntaVerdaderoFalso`, `editarPregunta`, `eliminarPregunta` |
| `frontend/src/router.tsx` | Rutas nuevas, protegidas con `RequireRole(rol="docente")` |

---

## Referencias

- Relacionada con: `US-1.1.6` (infraestructura reutilizada), `US-2.1.1` a `US-2.1.7` (backend consumido)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
