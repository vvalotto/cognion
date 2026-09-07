# US-ADJ-24: Administrador crea una Comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1a
**Tipo**: `feature` (frontend puro, sin cambios de backend)
**Agregado principal afectado**: `Comisión` (alta, sin invariante nueva)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a. Prerrequisito de
`US-ADJ-25` (asignar Docente) y `US-ADJ-26` (generar invitación) — ninguna Comisión existe
hoy sin sembrarla por script.

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **crear una Comisión eligiendo la Materia y el horario**
para **poder asignarle después un Docente y, eventualmente, generar invitaciones de
Estudiante**.

---

## Contexto del dominio

### Problema

`POST /comisiones` (`materia_id`, `horario`, `administrador_id`) existe desde el Incremento 1
(`US-1.1.1`) y ya acepta rol `administrador` — no requiere ningún cambio de backend. No existe
ninguna pantalla que lo consuma: `US-ADJ-23` dejó la ruta `/comisiones/nueva` con
`ComisionPlaceholder` a propósito, a la espera de esta US.

`administrador_id` es un campo obligatorio del body que hoy nada en el frontend puede resolver
— `Session` (`frontend/src/lib/session.ts`) solo persiste `token`/`rol`, no el id del usuario
autenticado. El id sí viaja en el JWT (claim `sub`, ver `src/shared/frameworks/security/
jwt_pyjwt.py:21`), pero nada lo decodifica del lado del cliente todavía.

### Alcance del fix

1. **Frontend — decodificar el `sub` del JWT.** Agregar `obtenerUsuarioId()` a
   `session.ts`: decodifica el payload del JWT ya almacenado (base64url, sin verificar firma
   — la firma la valida el backend en cada request, el cliente solo necesita leer el claim)
   y devuelve el `sub` como `string`. Sin librería nueva — un JWT tiene 3 partes separadas por
   `.`, el payload es la segunda, `atob` more `decodeURIComponent(escape(...))` para UTF-8
   (mismo patrón estándar, sin dependencia externa).
2. **Frontend — cliente API** `crearComision(materiaId, horario)` en
   `identidad-comisiones-api.ts` (ya existente, amplía sus exports): arma el body con
   `administrador_id` resuelto vía `obtenerUsuarioId()`, hace `POST /comisiones`, devuelve
   `{ id }`.
3. **Frontend — pantalla nueva** `NuevaComision.tsx`, reemplaza `ComisionPlaceholder` en
   `/comisiones/nueva`: selector de Materia (`GET /materias`, ya existente,
   `listarMaterias()`), preseleccionada si se llega con `?materiaId=` en la URL (el botón
   "+ Nueva Comisión" de `Comisiones.tsx` pasa a incluirlo); campo Horario (texto libre). Al
   crear, navega a `/comisiones/{id}` (detalle — sigue siendo `ComisionPlaceholder` hasta
   `US-ADJ-25`, no se toca en esta US).
4. **Frontend — `Comisiones.tsx`**: el botón "+ Nueva Comisión" pasa a navegar a
   `/comisiones/nueva?materiaId=${materiaId}` (hoy navega sin query param).

**Fuera de alcance de esta US:**
- Asignar Docente en el mismo formulario — acción separada (`US-ADJ-25`), decisión ya tomada
  con Víctor (`inc4-adj-candidatas.md` §1a, wireframe §3.2).
- Construir la pantalla de detalle de Comisión — sigue siendo `ComisionPlaceholder`, la arma
  `US-ADJ-25`.
- Cualquier cambio de backend — `POST /comisiones` ya acepta `administrador` sin
  modificación.

---

## Especificacion del comportamiento

### Precondicion

- Al menos una Materia existe (`GET /materias`).
- `/comisiones/nueva` renderiza `ComisionPlaceholder`.
- `obtenerUsuarioId()` no existe en `session.ts`.

### Postcondicion

- Un Administrador autenticado puede elegir una Materia (preseleccionada si llega desde el
  listado de esa Materia) y un horario en texto libre, y crear la Comisión.
- Al crear, la Comisión existe en el backend sin Docente asignado (`docentes_asignados: []`,
  mismo comportamiento ya cubierto por `test_comisiones_api_integration.py`) y el navegador
  queda en `/comisiones/{id}`.
- Cancelar vuelve a `/comisiones` (o a `/comisiones?materiaId=...` si había una preselección)
  sin crear nada.

### Invariantes

Ninguna nueva — reutiliza `Comisión.crear()` ya existente (`entities/comision.py`), sin
invariante adicional del lado del dominio. Esta US es de frontend puro.

---

## Criterios de aceptacion

```gherkin
Feature: Administrador crea una Comisión (US-ADJ-24)

  Scenario: Administrador crea una Comisión desde el listado de una Materia
    Given el Administrador está viendo las Comisiones de la Materia "Ingeniería de Software"
    When hace clic en "+ Nueva Comisión"
    Then el formulario aparece con esa Materia ya preseleccionada

  Scenario: Administrador crea una Comisión con éxito
    Given el Administrador completó Materia y Horario válidos
    When hace clic en "Crear Comisión"
    Then la Comisión se crea sin Docente asignado
    And el navegador va al detalle de la Comisión recién creada

  Scenario: Administrador cancela la creación
    Given el Administrador está en el formulario de Nueva Comisión
    When hace clic en "Cancelar"
    Then vuelve al listado de Comisiones sin crear nada
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — consume un endpoint ya existente sin cambios; el único agregado es un helper de
  decodificación de JWT del lado del cliente, sin librería nueva ni cambio de contrato.

**Capa(s) afectadas:**
- [x] Backend — ninguna
- [x] Frontend — `session.ts` (helper nuevo), `identidad-comisiones-api.ts` (función nueva),
  `NuevaComision.tsx` (pantalla nueva), `Comisiones.tsx` (query param), `router.tsx`
  (reemplaza el placeholder)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/session.ts` | `obtenerUsuarioId()` — decodifica el claim `sub` del JWT almacenado |
| `frontend/src/lib/identidad-comisiones-api.ts` | `crearComision(materiaId, horario, signal?)` — `POST /comisiones` |
| `frontend/src/pages/identidad/NuevaComision.tsx` (nuevo) | Formulario de alta, ruta `/comisiones/nueva` |
| `frontend/src/pages/identidad/Comisiones.tsx` | Botón "+ Nueva Comisión" navega con `?materiaId=` |
| `frontend/src/router.tsx` | `/comisiones/nueva` usa `NuevaComision` en vez de `ComisionPlaceholder` |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a
- `docs/design/ux/wireframes-portal-entrada.md` §3.2
- Issue: [#269](https://github.com/vvalotto/cognion/issues/269)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
