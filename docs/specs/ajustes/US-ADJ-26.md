# US-ADJ-26: Docente genera el link de invitación de una Comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 4-ADJ — Portal de Entrada y Validación E2E`, Iteración 1a
**Tipo**: `feature` (endpoint existente ampliado + pantallas nuevas, sin caso de uso de dominio
nuevo)
**Agregado principal afectado**: `Invitacion` (respuesta ampliada, sin invariante nueva)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a. Depende de `US-ADJ-25`
(una Comisión sin Docente asignado no sirve para esto) — ya cerrada.

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **generar el link de invitación de una Comisión donde estoy asignado**
para que **pueda compartirlo manualmente con mis Estudiantes y se registren**.

---

## Contexto del dominio

### Problema

`POST /comisiones/{id}/invitaciones` (`GenerarInvitacionUseCase`, `US-1.1.1`) ya existe, ya
acepta rol `docente` y ya valida del lado del dominio que el `docente_id` recibido esté en
`Comision.docentes_asignados` (`DocenteNoAsignadoAComision`, INV-ID-08). Lo que no existe es
ninguna pantalla que lo use, ni forma de que el Docente llegue al detalle de una Comisión
propia.

**Gap de backend detectado en Fase 0 (decidido con Víctor):**

1. `InvitacionResponse` no expone el `token` — el endpoint fue diseñado para enviar el token
   por email (`NotificadorPort.enviar_invitacion`, SMTP), no para mostrarlo en pantalla. El
   wireframe (§3.4) pide un botón "Generar link de invitación" + link visible con "Copiar",
   sin flujo de email. Decisión: agregar `token` a `InvitacionResponse` y hacer
   `email_destinatario` opcional en `GenerarInvitacionRequest` — si no se envía, el use case
   omite el envío de email (mismo endpoint sirve para "copiar el link" y, si en el futuro se
   quiere, para "mandarlo por mail" sin duplicar lógica). Sin invariante de dominio nueva:
   `Invitacion.crear()` ya genera el `token`, solo faltaba exponerlo por HTTP.
2. No existe `GET /docentes/{id}/comisiones`. Decisión: no agregar ese endpoint — el Docente
   llega a sus Comisiones navegando **Materias → Comisiones de la materia**, reutilizando
   `GET /materias/{id}/comisiones` (ya acepta rol `docente` desde `US-4.2.2`) sin filtrar por
   asignación en el listado (la validación real de "está asignado" la sigue haciendo el
   backend al generar la invitación — ver INV-ID-08 arriba). Evita un componente técnico
   nuevo solo para esta pantalla.

### Alcance del fix

1. **Backend — `schemas.py`**: `GenerarInvitacionRequest.email_destinatario` pasa a
   `str | None = None`; `InvitacionResponse` gana el campo `token: str`.
2. **Backend — `GenerarInvitacionUseCase.execute`**: solo llama a
   `self._notificador.enviar_invitacion(...)` si `email_destinatario` no es `None`.
3. **Backend — `invitaciones_router.py`**: pasa `body.email_destinatario` (ahora opcional) al
   controller/use case sin cambio de firma; agrega `token=invitacion.token` a la respuesta.
4. **Frontend — cliente API**: `generarInvitacion(comisionId, docenteId, signal?)` nuevo en
   `identidad-comisiones-api.ts` — `POST /comisiones/{id}/invitaciones` sin
   `email_destinatario`, devuelve `{ id, comisionId, docenteId, expiraEn, token }`.
5. **Frontend — pantalla nueva** `ComisionesDeMateria.tsx` en
   `/actividad-evaluativa/materias/:materiaId/comisiones`: lista las Comisiones de la materia
   (`listarComisionesPorMateria`, ya existente) — mismo dato que usa `Comisiones.tsx` del
   Administrador, tabla más simple (Horario + acción "Ver detalle"). Entry point: botón
   "Ver Comisiones" agregado en `Actividades.tsx` (pantalla de actividades por materia, junto
   a "+ Nueva actividad").
6. **Frontend — pantalla nueva** `ComisionDetalleDocente.tsx` en
   `/actividad-evaluativa/comisiones/:comisionId`: breadcrumb "Mis materias › {materia} ›
   Comisiones › {horario}"; botón "Generar link de invitación" que llama a
   `generarInvitacion(comisionId, obtenerUsuarioId())`; tras la respuesta, muestra el link
   (`${origin}/registro?token=${token}`) en un recuadro con botón "Copiar" (`navigator.clipboard`)
   y el botón cambia a "Generar un link nuevo"; tabla de Estudiantes inscriptos
   (`listarEstudiantesDeComision`, ya existente) de solo lectura.

**Fuera de alcance de esta US:**
- Revocar o editar una invitación ya generada — `docs/design/ux/wireframes-portal-entrada.md`
  §4 lo excluye explícitamente de todo el documento.
- Enviar el link por email desde esta pantalla — el `NotificadorPort` sigue existiendo para
  cuando haga falta, pero esta pantalla no lo ejercita (decisión de alcance arriba).
- Menú de navegación persistente (`.app-nav`, `US-ADJ-27`) — el entry point de esta US es un
  botón dentro de una pantalla ya existente, no un ítem del menú principal.

---

## Especificacion del comportamiento

### Precondicion

- La Comisión objetivo tiene al menos un Docente asignado (`US-ADJ-25`).
- `InvitacionResponse` no expone `token`; `GenerarInvitacionRequest.email_destinatario` es
  obligatorio.
- No existe ninguna pantalla que consuma `POST /comisiones/{id}/invitaciones`.

### Postcondicion

- Un Docente autenticado navega Mis materias → materia → "Ver Comisiones" → una Comisión
  donde está asignado, y ve el botón "Generar link de invitación".
- Al confirmar, ve el link completo (`.../registro?token=...`) y puede copiarlo con un click.
- Generar de nuevo produce una invitación distinta (nuevo `id`, nuevo `token`) — no reutiliza
  la anterior, ambas quedan válidas hasta su propio vencimiento (comportamiento ya existente
  de `GenerarInvitacionUseCase`, sin cambios).
- Un Docente que **no** está asignado a la Comisión recibe 422 al intentar generar el link
  (`DocenteNoAsignadoAComision`, ya cubierto por el use case) — la UI no debería llegar a
  ofrecer el botón en ese caso, pero el backend es la fuente de verdad.

### Invariantes

Ninguna nueva. INV-ID-08 (`DocenteNoAsignadoAComision`) ya existente y sin cambios — sigue
siendo la única defensa real contra que un Docente genere invitaciones de una Comisión ajena.

---

## Criterios de aceptacion

```gherkin
Feature: Docente genera el link de invitación de una Comisión (US-ADJ-26)

  Scenario: Docente asignado genera el link con éxito
    Given el Docente está asignado a una Comisión
    When navega al detalle de esa Comisión y hace clic en "Generar link de invitación"
    Then ve el link completo con un botón "Copiar"
    And el botón cambia a "Generar un link nuevo"

  Scenario: Generar un link nuevo produce una invitación distinta
    Given el Docente ya generó un link para una Comisión
    When hace clic en "Generar un link nuevo"
    Then el link mostrado cambia (token distinto del anterior)

  Scenario: Docente no asignado no puede generar el link
    Given el Docente no está asignado a la Comisión solicitada
    When intenta generar el link (vía API directa, bypaseando la UI)
    Then el sistema responde 422 (DocenteNoAsignadoAComision)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — reutiliza `GenerarInvitacionUseCase`/`Invitacion.crear()` ya existentes; el único
  cambio de backend es ampliar un schema de respuesta y volver opcional un campo de request,
  sin invariante ni Use Case nuevo.

**Capa(s) afectadas:**
- [x] Backend — `frameworks/api/schemas.py` (`GenerarInvitacionRequest`/`InvitacionResponse`),
  `use_cases/generar_invitacion.py` (email condicional), `frameworks/api/invitaciones_router.py`
  (campo `token` en la respuesta)
- [x] Frontend — `identidad-comisiones-api.ts` (`generarInvitacion` nueva),
  `ComisionesDeMateria.tsx` (nueva), `ComisionDetalleDocente.tsx` (nueva),
  `Actividades.tsx` (botón "Ver Comisiones"), `router.tsx` (2 rutas nuevas)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/frameworks/api/schemas.py` | `email_destinatario: str \| None = None`; `InvitacionResponse.token: str` nuevo |
| `src/identidad/use_cases/generar_invitacion.py` | Envío de email condicional a `email_destinatario is not None` |
| `src/identidad/frameworks/api/invitaciones_router.py` | Agrega `token=invitacion.token` a la respuesta |
| `frontend/src/lib/identidad-comisiones-api.ts` | `generarInvitacion(comisionId, docenteId, signal?)` |
| `frontend/src/pages/actividad-evaluativa/ComisionesDeMateria.tsx` (nuevo) | Listado de Comisiones de una materia, ruta `/actividad-evaluativa/materias/:materiaId/comisiones` |
| `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx` (nuevo) | Detalle + generar link, ruta `/actividad-evaluativa/comisiones/:comisionId` |
| `frontend/src/pages/actividad-evaluativa/Actividades.tsx` | Botón "Ver Comisiones" |
| `frontend/src/router.tsx` | 2 rutas nuevas, `RequireRole rol="docente"` |

---

## Referencias

- Incremento: 4-ADJ
- `docs/plans/inc4-adj/inc4-adj-candidatas.md` §Iteración 1a
- `docs/design/ux/wireframes-portal-entrada.md` §3.4
- Issue: [#271](https://github.com/vvalotto/cognion/issues/271)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
