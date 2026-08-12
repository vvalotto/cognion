# US-1.1.2: Estudiante se registra con un link de invitación válido

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.1`
**Tipo**: `feat backend` + `feat frontend`
**Agregado principal afectado**: `Usuario` (perfil `Estudiante`), `Invitación`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Estudiante** que recibí un link de invitación,
quiero **completar mi registro con ese link**
para **quedar asignado automáticamente a la comisión del docente que me invitó, sin
aprobación adicional (RF-01)**.

---

## Contexto del dominio

### Problema

RF-01 exige que la asignación a comisión sea automática e inmediata al aceptar la invitación —
no hay paso de aprobación por parte del docente. El registro consume la invitación (uso único)
y crea el `Usuario` + perfil `Estudiante` en la misma transacción.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Invitación` | Se consulta y se marca como usada (`usada_en`) |
| Aggregate | `Usuario` | Se crea junto con la Entity subordinada `Estudiante` |
| Entity subordinada | `Estudiante` | `comision_id` asignado desde el momento de creación |
| Command | `RegistrarEstudiante(token, nombre, email, password)` | Dispara el registro |
| Domain Event | `InvitacionAceptada`, `UsuarioRegistrado` | Señalan la aceptación y el alta |
| Port | `PasswordHasherPort` | Hashing bcrypt (`ADR-014`) |

---

## Especificacion del comportamiento

### Precondicion

- Existe una `Invitación` con ese `token`.
- `ahora < Invitación.expira_en` y `Invitación.usada_en is null` (INV-ID-03).
- `email` recibido no está registrado por otro `Usuario` (INV-ID-04).

### Postcondicion

- `Usuario` + `Estudiante` creados en la misma transacción (INV-ID-09); `password_hash` con
  bcrypt (INV-ID-06); `Estudiante.comision_id` = `Invitación.comision_id` (INV-ID-05).
- `Invitación.usada_en = ahora` — queda inutilizable para un segundo registro (INV-ID-01).
- Eventos `InvitacionAceptada`, `UsuarioRegistrado`.
- El registro **no** autentica automáticamente — el Estudiante debe iniciar sesión después
  (`US-1.1.4`), decisión de simplicidad confirmada en `wireframes-identidad.md` §2.5.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-01 | Una invitación con `usada_en` no null no puede volver a aceptarse (uso único). |
| INV-ID-03 | Una invitación es válida para aceptar solo si `ahora < expira_en` y `usada_en is null`. |
| INV-ID-04 | `email` único en todo el sistema — `EmailYaRegistrado` si ya existe. |
| INV-ID-05 | Un `Estudiante` siempre tiene `comision_id` asignado desde su creación — no existe `Estudiante` sin comisión. |
| INV-ID-06 | `password_hash` se persiste siempre con bcrypt; nunca en texto plano. |
| INV-ID-09 | Todo `Usuario` tiene exactamente un perfil, creado atómicamente junto con él. |

---

## Criterios de aceptacion

```gherkin
Feature: Registro de Estudiante vía invitación válida

  Scenario: Registro exitoso con invitación vigente
    Given una Invitación vigente (no vencida, no usada) para la Comisión "IS-2026-C1"
    When el Estudiante ejecuta RegistrarEstudiante(token, nombre, email, password)
    Then el sistema crea un Usuario con perfil Estudiante en la misma transacción
    And Estudiante.comision_id queda asignado a "IS-2026-C1"
    And la Invitación queda marcada como usada
    And se emiten los eventos InvitacionAceptada y UsuarioRegistrado
    And el Estudiante NO queda autenticado automáticamente

  Scenario: Rechazo por email ya registrado
    Given una Invitación vigente
    And un Usuario ya existe con el email que se intenta registrar
    When el Estudiante ejecuta RegistrarEstudiante con ese email
    Then el sistema rechaza la operación con EmailYaRegistrado
    And la Invitación no se marca como usada
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente (`ADR-012`, `ADR-014`)

**Capa(s) afectadas:**
- [x] Entities — `Usuario`, `Estudiante`, `Invitación` (transición de estado), eventos
- [x] Use Cases — `RegistrarEstudianteUseCase`
- [x] Interface Adapters — controller, repositorios
- [x] Frameworks — endpoint FastAPI (público, sin JWT — se autentica después)
- [x] Frontend — pantallas de registro y éxito

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-identidad.md` §2.3 (Registro — link válido) y §2.5
  (Registro — éxito).
- Prototipo: `docs/design/ux/prototipos/identidad-registro-login.html` (`#registro`,
  `#registro-exito`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | Agregar Entity subordinada `Estudiante` si no existe (compartida con `US-1.1.0`) |
| `src/identidad/entities/invitacion.py` | Método/transición para marcar `usada_en` |
| `src/identidad/entities/eventos.py` | Agregar `InvitacionAceptada`, `UsuarioRegistrado` |
| `src/identidad/use_cases/registrar_estudiante.py` | Orquesta validación de invitación + alta atómica de Usuario/Estudiante |
| `src/identidad/interface_adapters/controllers/registro_controller.py` | Validación de entrada (password mínimo 8, confirmación) |
| `src/identidad/interface_adapters/gateways/usuario_repository.py`, `invitacion_repository.py` | Persistencia (compartidos con otras US) |
| `src/identidad/frameworks/api/registro_router.py` | Endpoint FastAPI público `POST /identidad/registro` |
| `frontend/src/features/identidad/Registro.tsx` | Pantalla `#registro` |
| `frontend/src/features/identidad/RegistroExito.tsx` | Pantalla `#registro-exito` |

---

## Referencias

- Relacionada con: `US-1.1.1`, `US-1.1.3`, `US-1.1.4`, `ADR-012`, `ADR-014`
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` (§3, §4 `Usuario`, `Estudiante`)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
