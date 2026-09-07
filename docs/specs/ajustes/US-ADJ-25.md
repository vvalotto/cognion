# US-ADJ-25: Administrador asigna un Docente a una Comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1a
**Tipo**: `feature` (pantalla de detalle nueva + endpoint de consulta nuevo, sin caso de uso
de dominio nuevo)
**Agregado principal afectado**: `Comisión` (mutación ya existente, sin invariante nueva)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a. Prerrequisito de
`US-ADJ-26` (generar invitación) — una Comisión sin Docente asignado no sirve para eso.

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **asignar un Docente a una Comisión existente**
para que **ese Docente pueda generar el link de invitación de esa Comisión**.

---

## Contexto del dominio

### Problema

`POST /comisiones/{id}/docentes` (`AsignarDocenteAComisionUseCase`) existe desde el
Incremento 1 (`US-1.1.1`) y ya acepta rol `administrador` — no requiere cambio de backend.
`GET /usuarios?rol=docente` (`US-2.2.2`) también existe sin cambios. Lo que no existe es
ninguna pantalla que los use, ni forma de llegar al detalle de una Comisión puntual:
`/comisiones/:comisionId` renderiza `ComisionPlaceholder` desde `US-ADJ-23`.

**Gap de backend detectado en Fase 0:** no existe `GET /comisiones/{comision_id}`. La
pantalla de detalle necesita horario + docentes asignados de una Comisión puntual sin conocer
de antemano su `materia_id` (se llega ahí por navegación directa, no anidada bajo una
Materia). `ComisionRepositoryPort.obtener_por_id()` ya devuelve exactamente esos datos
(incluidos los docentes vía `selectinload`, cargados desde `US-ADJ-23`) — falta exponerlo por
HTTP.

### Alcance del fix

1. **Backend — endpoint nuevo** `GET /comisiones/{comision_id}` en `comisiones_router.py`,
   guard `require_docente_o_administrador` (ya existente, reutilizable por `US-ADJ-26` para
   la vista del Docente). Responde `ComisionResponse` (ya existe: `id`, `materia_id`,
   `horario`, `administrador_id`, `docentes_asignados: list[UUID]`) o 404 si no existe.
2. **Backend — `ComisionesQueryController.obtener_comision(comision_id)`** nuevo: llama
   directamente a `ComisionRepositoryPort.obtener_por_id()` (ya inyectado en el controller
   para validar existencia en `listar_estudiantes`) y lanza `ComisionNoExiste` si es `None`.
   Sin Use Case dedicado — mismo criterio que el resto de `ComisionesQueryController`, que ya
   trata las consultas como pass-through fino sobre el repositorio en vez de forzar una capa
   de orquestación para una lectura simple.
3. **Frontend — cliente API**: `obtenerComision(comisionId, signal?)` y
   `asignarDocente(comisionId, docenteId, signal?)` nuevos en `identidad-comisiones-api.ts`.
4. **Frontend — pantalla nueva** `ComisionDetalle.tsx`, reemplaza `ComisionPlaceholder` en
   `/comisiones/:comisionId` (ruta ya protegida `RequireRole rol="administrador"`): breadcrumb
   "Comisiones › {horario}" + botón "‹ Volver a Comisiones"; alerta informativa si
   `docentesAsignados.length === 0` ("Hasta que se asigne un Docente, esta Comisión no puede
   generar link de invitación para estudiantes"); select con usuarios `rol=docente`
   (`listarCuentas`, mismo patrón que `Comisiones.tsx`) + botón "Asignar"; tabla de
   Estudiantes inscriptos (`listarEstudiantesDeComision`, ya existente) o estado vacío.

**Fuera de alcance de esta US:**
- Generar invitación — acción exclusiva del Docente, vista y ruta propias (`US-ADJ-26`).
- Impedir asignar más de un Docente — el dominio no lo prohíbe (`Comision.asignar_docente` es
  idempotente y no tiene tope), decisión ya tomada en el wireframe (§3.3).
- Volver a exponer `materia_id` en la UI — el breadcrumb usa solo el horario, no hace falta
  resolver el nombre de la Materia para esta pantalla.

---

## Especificacion del comportamiento

### Precondicion

- Al menos una Comisión existe (creada por `US-ADJ-24`).
- `GET /comisiones/{comision_id}` no existe.
- `/comisiones/:comisionId` renderiza `ComisionPlaceholder`.

### Postcondicion

- Un Administrador autenticado que navega a `/comisiones/{id}` ve el horario, el estado de
  asignación de Docente (alerta si no hay ninguno) y la lista de Estudiantes inscriptos.
- Al elegir un Docente del select y confirmar "Asignar", la Comisión queda con ese Docente en
  `docentes_asignados` y la pantalla lo refleja sin recargar la página completa.
- Asignar un Docente ya asignado es un no-op sin error (mismo comportamiento ya cubierto por
  `Comision.asignar_docente`, idempotente).

### Invariantes

Ninguna nueva del lado del dominio — reutiliza `Comision.asignar_docente()` ya existente. La
única pieza nueva de comportamiento (`obtener_comision`) es una consulta de lectura, sin
mutación.

---

## Criterios de aceptacion

```gherkin
Feature: Administrador asigna un Docente a una Comisión (US-ADJ-25)

  Scenario: Comisión sin Docente asignado muestra alerta informativa
    Given el Administrador ve el detalle de una Comisión sin Docente asignado
    Then ve una alerta explicando que sin un Docente no se puede generar invitación

  Scenario: Administrador asigna un Docente con éxito
    Given el Administrador ve el detalle de una Comisión sin Docente asignado
    And existe al menos un usuario con rol Docente
    When elige un Docente del select y hace clic en "Asignar"
    Then el Docente aparece listado en el detalle de la Comisión
    And la alerta de "sin Docente asignado" desaparece

  Scenario: Detalle de Comisión inexistente
    Given no existe ninguna Comisión con el id solicitado
    When el Administrador navega a su detalle
    Then el sistema responde 404
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — reutiliza `AsignarDocenteAComisionUseCase` ya existente; el único componente
  nuevo de backend es una consulta de lectura sobre un puerto ya inyectado, sin invariante ni
  Use Case adicional.

**Capa(s) afectadas:**
- [x] Backend — `interface_adapters/controllers/comisiones_query_controller.py` (método
  nuevo), `frameworks/api/comisiones_router.py` (endpoint nuevo)
- [x] Frontend — `identidad-comisiones-api.ts` (2 funciones nuevas), `ComisionDetalle.tsx`
  (pantalla nueva), `router.tsx` (reemplaza el placeholder)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/interface_adapters/controllers/comisiones_query_controller.py` | `obtener_comision(comision_id)` — lee `ComisionRepositoryPort.obtener_por_id()`, lanza `ComisionNoExiste` |
| `src/identidad/frameworks/api/comisiones_router.py` | `GET /comisiones/{comision_id}` — guard `require_docente_o_administrador` |
| `frontend/src/lib/identidad-comisiones-api.ts` | `obtenerComision(comisionId, signal?)`, `asignarDocente(comisionId, docenteId, signal?)` |
| `frontend/src/pages/identidad/ComisionDetalle.tsx` (nuevo) | Pantalla de detalle, ruta `/comisiones/:comisionId` |
| `frontend/src/router.tsx` | `/comisiones/:comisionId` usa `ComisionDetalle` en vez de `ComisionPlaceholder` |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a
- `docs/design/ux/wireframes-portal-entrada.md` §3.3
- Issue: [#270](https://github.com/vvalotto/cognion/issues/270)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
