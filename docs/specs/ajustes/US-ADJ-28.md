# US-ADJ-28: Home del Docente

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1b
**Tipo**: `feature` (pantalla nueva, frontend puro)
**Bounded Context**: ninguno específico — pantalla de entrada, sin lógica de negocio
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b. Depende de `US-ADJ-27`
(menú de navegación persistente, ya cerrada).

---

## Fuente de verdad UX

`docs/design/ux/wireframes-portal-entrada.md` §2.1. Prototipo navegable:
`docs/design/ux/prototipos/portal-entrada.html` (`#home-docente`).

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **una pantalla de inicio con accesos directos a mis áreas**
para que **no caiga en un callejón sin salida tras el login**.

---

## Contexto del dominio

### Problema

`InicioPlaceholder` (`frontend/src/pages/_placeholders.tsx`) es la pantalla de `/` para los 3
roles desde `US-1.1.7` (Incremento 1) — "Sesión iniciada, pendiente de pantalla propia", sin
ningún acceso navegable. `US-ADJ-27` ya resolvió la navegación cruzada entre pantallas (menú
persistente); esta US resuelve el punto de aterrizaje inicial para el rol Docente.

**Gap de backend detectado en Fase 0 (decidido con Víctor):** el wireframe (§2.1) pide un
saludo "Hola, {nombre}" — ningún endpoint expone el nombre del propio usuario autenticado
(`GET /usuarios/{id}` es solo `administrador`; el JWT solo trae `sub`/`rol`, sin `nombre`).
Decisión: **saludo genérico sin nombre** ("Hola, Docente"), sin agregar backend nuevo — se
aparta del wireframe literal, documentado como desvío aceptado en esta spec.

### Alcance del fix

**Frontend puro** — las 4 rutas destino ya existen y ya están protegidas por `RequireRole`.

1. Pantalla nueva `HomeDocente.tsx`, reemplaza `InicioPlaceholder` para `session.rol ===
   "docente"` en la ruta `/` (la ruta sigue siendo `index: true` dentro de `AppLayout`, el
   router debe distinguir por rol — ver Artefactos).
2. Sin breadcrumb (es la raíz). Saludo "Hola, Docente".
3. 4 cards de acceso directo (mismo componente `Card` ya usado en `MateriasActividades.tsx`/
   `Actividades.tsx`), cada una con título + descripción de una línea:
   - **Banco de Preguntas** → `/materias`
   - **Actividades** → `/actividad-evaluativa/materias`
   - **Desempeño por alumno** → `/analytics/desempeno-por-alumno`
   - **Desempeño por tema** → `/analytics/desempeno-por-tema`

**Fuera de alcance de esta US:**
- Contenido dinámico (contadores, notificaciones) — solo navegación
  (`portal-entrada-modelo.md` §5).
- Homes de Estudiante/Administrador — `US-ADJ-29`/`30`, pantallas separadas.

---

## Especificacion del comportamiento

### Precondicion

- `/` renderiza `InicioPlaceholder` para cualquier rol, incluido Docente.

### Postcondicion

- Un Docente autenticado que navega a `/` ve el saludo y 4 cards de acceso.
- Un click en cualquier card navega a la ruta correspondiente.
- El ítem "Inicio" del menú (`AppNav`, `US-ADJ-27`) queda resaltado en esta pantalla.

### Invariantes

Ninguna — frontend puro, sin dominio.

---

## Criterios de aceptacion

```gherkin
Feature: Home del Docente (US-ADJ-28)

  Scenario: Docente ve sus 4 cards de acceso
    Given un Docente autenticado
    When navega a "/"
    Then ve las cards Banco de Preguntas, Actividades, Desempeño por alumno y Desempeño por tema

  Scenario: Click en una card navega a su ruta
    Given un Docente autenticado en "/"
    When hace clic en la card "Banco de Preguntas"
    Then la pantalla muestra el contenido de /materias

  Scenario: Otro rol no ve la Home del Docente
    Given un Estudiante autenticado
    When navega a "/"
    Then no ve las cards de Docente
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — pantalla de presentación pura, sin backend nuevo (decisión de saludo genérico
  evita agregar `GET /usuarios/me`).

**Capa(s) afectadas:**
- [x] Frontend — `HomeDocente.tsx` (nuevo), `router.tsx` (index route condicional por rol)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/HomeDocente.tsx` (nuevo) | Pantalla de home, 4 cards |
| `frontend/src/router.tsx` | La ruta índice (`/`) pasa de `InicioPlaceholder` fijo a un componente `Inicio` que elige la home según `session.rol` (Docente → `HomeDocente`, otros roles → `InicioPlaceholder` hasta `US-ADJ-29`/`30`) |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1b
- `docs/design/ux/wireframes-portal-entrada.md` §2.1
- Issue: [#273](https://github.com/vvalotto/cognion/issues/273)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
