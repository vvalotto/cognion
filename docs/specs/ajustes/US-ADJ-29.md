# US-ADJ-29: Home del Estudiante

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1b
**Tipo**: `feature` (pantalla nueva, frontend puro)
**Bounded Context**: ninguno específico — pantalla de entrada, sin lógica de negocio
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b. Depende de `US-ADJ-27`
(menú de navegación persistente, ya cerrada). Sin dependencia de `US-ADJ-28` (pantallas
distintas), pero reutiliza su decisión de saludo genérico.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-portal-entrada.md` §2.2. Prototipo navegable:
`docs/design/ux/prototipos/portal-entrada.html` (`#home-estudiante`).

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **una pantalla de inicio con accesos directos a mis áreas**
para que **no caiga en un callejón sin salida tras el login**.

---

## Contexto del dominio

### Problema

Mismo problema que `US-ADJ-28` (Home del Docente, ya cerrada) para el rol Estudiante:
`InicioPlaceholder` sigue siendo el destino de `/` para Estudiante y Administrador —
`Inicio.tsx` (`US-ADJ-28`) ya despacha por rol, falta agregar la rama `estudiante`.

**Sin gap nuevo de backend:** misma decisión ya tomada en `US-ADJ-28` — saludo genérico
("Hola, Estudiante") en vez de "Hola, {nombre}" del wireframe, sin agregar
`GET /usuarios/me`.

### Alcance del fix

**Frontend puro** — las 2 rutas destino ya existen y ya están protegidas por `RequireRole`.

1. Pantalla nueva `HomeEstudiante.tsx`, mismo patrón que `HomeDocente.tsx`: sin breadcrumb,
   saludo genérico, grid de cards.
2. 2 cards de acceso directo:
   - **Mis Actividades** → `/mis-actividades/materias`
   - **Mi Desempeño** → `/analytics/mi-desempeno`
3. `Inicio.tsx` (`US-ADJ-28`) gana la rama `rol === "estudiante"` → `<HomeEstudiante />`.

**Fuera de alcance de esta US:**
- Home del Administrador — `US-ADJ-30`, pantalla separada.
- Contenido dinámico (contadores, notificaciones) — solo navegación.

---

## Especificacion del comportamiento

### Precondicion

- `/` renderiza `InicioPlaceholder` para Estudiante (y Administrador).

### Postcondicion

- Un Estudiante autenticado que navega a `/` ve el saludo y 2 cards de acceso.
- Un click en cualquier card navega a la ruta correspondiente.
- El ítem "Inicio" del menú (`AppNav`) queda resaltado en esta pantalla.

### Invariantes

Ninguna — frontend puro, sin dominio.

---

## Criterios de aceptacion

```gherkin
Feature: Home del Estudiante (US-ADJ-29)

  Scenario: Estudiante ve sus 2 cards de acceso
    Given un Estudiante autenticado
    When navega a "/"
    Then ve las cards Mis Actividades y Mi Desempeño

  Scenario: Click en una card navega a su ruta
    Given un Estudiante autenticado en "/"
    When hace clic en la card "Mis Actividades"
    Then la pantalla muestra el contenido de /mis-actividades/materias

  Scenario: Otro rol no ve la Home del Estudiante
    Given un Docente autenticado
    When navega a "/"
    Then no ve las cards de Estudiante
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — pantalla de presentación pura, mismo patrón que `US-ADJ-28`.

**Capa(s) afectadas:**
- [x] Frontend — `HomeEstudiante.tsx` (nuevo), `Inicio.tsx` (rama nueva)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/HomeEstudiante.tsx` (nuevo) | Pantalla de home, 2 cards |
| `frontend/src/pages/Inicio.tsx` | Agrega la rama `rol === "estudiante"` |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b
- `docs/design/ux/wireframes-portal-entrada.md` §2.2
- Issue: [#274](https://github.com/vvalotto/cognion/issues/274)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
