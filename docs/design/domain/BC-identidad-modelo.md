# BC Identidad — Modelo de Dominio (Event Storming)

> Estado documental: **vigente — aprobado por Víctor (US-1.0.1, Issue #2, cerrado 2026-07-18).**
> Usado como input de las specs US-IEDD de la Iteración 1 (`docs/specs/inc1/US-1.1.0` a
> `US-1.1.5`).
>
> Fuente: `docs/rf/RF_v1.md` (RF-01, RF-02), `ADR-007` (JWT+RBAC), `ADR-012` (invitación),
> `ADR-013` (expiración JWT), `ADR-014` (bcrypt).

---

## 1. Actores

| Actor | Rol en el BC |
|---|---|
| Docente | Genera invitaciones para su comisión; se autentica |
| Estudiante | Se registra vía invitación; se autentica |
| Administrador | Crea cuentas de `Usuario` directamente (§3, `CrearUsuario`), crea comisiones y asigna docentes (`US-1.1.0`); se autentica. Bloqueos/recuperación de cuenta son RF-03, Incremento 2 — fuera de alcance acá |

---

## 2. Línea de tiempo — Eventos de dominio

Orden narrativo, no técnico. 🟧 evento de dominio · 🟦 comando · 🟨 aggregate.

```
[Docente]                     [Estudiante]                    [Docente/Admin/Estudiante]
   |                               |                                    |
🟦 GenerarInvitacion              |                                    |
   |                               |                                    |
🟧 InvitacionGenerada             |                                    |
   |                               |                                    |
   |                        🟦 RegistrarEstudiante(token, datos)        |
   |                               |                                    |
   |                    ┌──────────┴──────────┐                        |
   |                    ▼                     ▼                        |
   |         🟧 InvitacionAceptada    🟧 RegistroRechazado             |
   |         🟧 UsuarioRegistrado     (token vencido/inválido/usado)   |
   |                                                                    |
   |                                                          🟦 IniciarSesion(email, password)
   |                                                                    |
   |                                                          🟧 SesionIniciada
   |                                                          (o rechazo — ver hot spot 2)
```

---

## 3. Comandos → Eventos

| Comando | Actor | Aggregate | Evento(s) | Excepciones |
|---|---|---|---|---|
| `CrearUsuario(nombre, email, password, perfil)` | Administrador | `Usuario` + perfil (`Docente`/`Administrador`/`Estudiante`) — crea ambos, misma transacción | `UsuarioCreado` | `EmailYaRegistrado` |
| `GenerarInvitacion(comision_id, docente_id)` | Docente | `Invitación` (crea) — valida contra `Comisión.docentes_asignados` | `InvitacionGenerada` | `DocenteNoAsignadoAComision` (INV-ID-08) |
| `RegistrarEstudiante(token, nombre, email, password)` | Estudiante | `Invitación` (consulta) → `Usuario` + `Estudiante` (crea ambos, misma transacción) | `InvitacionAceptada`, `UsuarioRegistrado` | `InvitacionVencida`, `InvitacionInvalida`, `InvitacionYaUsada`, `EmailYaRegistrado` |
| `IniciarSesion(email, password)` | Docente, Administrador, Estudiante | `Usuario` (consulta, incluye `perfil`) | `SesionIniciada` (JWT con claim `rol` derivado del tipo de `perfil`) | `CredencialesInvalidas` |

**Diferidos — modelados, sin US en el Incremento 1** (RF-19 elicitado 2026-07-17, ver
`docs/rf/RF_v1.md`; agrupados con RF-03 en el Incremento 2 — mismo mecanismo de desbloqueo):

| Comando | Actor | Evento | Excepciones / notas |
|---|---|---|---|
| `CambiarPassword(usuario_id, password_actual, password_nueva)` | Usuario autenticado (self-service) | `PasswordCambiada` | `PasswordActualIncorrecta` (INV-ID-10), `PasswordDemasiadoCorta` (INV-ID-11, mín. 8) |
| `ResetearPassword(usuario_id, password_nueva, administrador_id)` | Administrador | `PasswordReseteada`, `CuentaDesbloqueada` (si estaba bloqueada) | `PasswordDemasiadoCorta` (INV-ID-11). Es la **única** forma de desbloquear una cuenta — no existe un comando `DesbloquearCuenta` separado |

**Bloqueo automático por intentos fallidos (RF-19):**
- `IniciarSesion` y `CambiarPassword` llevan cada uno su propio contador de intentos fallidos
  consecutivos sobre `Usuario` (`intentos_fallidos_login`, `intentos_fallidos_password`).
- **INV-ID-10:** un acierto resetea a cero el contador de su propio flujo; al tercer fallo
  consecutivo en cualquiera de los dos, `Usuario.bloqueada = true` (evento `CuentaBloqueada`) y
  el usuario no puede volver a intentar hasta que un Administrador ejecute `ResetearPassword`.
- **INV-ID-11:** toda contraseña nueva (`CrearUsuario`, `RegistrarEstudiante`,
  `CambiarPassword`, `ResetearPassword`) tiene un mínimo de 8 caracteres — regla transversal,
  no exclusiva de RF-19 (extiende RF-01 y la alta directa de usuario, ver revisión
  2026-07-17 de `RF_v1.md`).
- Cambiar la contraseña **no** invalida el JWT en curso — sigue vigente hasta su expiración
  natural (60 min, `ADR-013`), decisión confirmada con Víctor (sin blacklist, consistente con
  el diseño stateless de `ADR-007`).

`RegistroRechazado` (token vencido/inválido/usado) y credenciales inválidas en `IniciarSesion`
no persisten como evento propio más allá de incrementar el contador de intentos — excepción de
aplicación (hot spot 2, §5), salvo el evento `CuentaBloqueada` que sí es un cambio de estado
persistente de `Usuario`.

---

## 4. Aggregates

### `Invitación` (Aggregate Root)

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `comision_id` | referencia | ver hot spot 1 — no hay aggregate `Comisión` formal todavía |
| `docente_id` | referencia a `Usuario` | quien la generó |
| `token` | string único | enviado por email (`ADR-012`) |
| `generada_en` | datetime | |
| `expira_en` | datetime | `generada_en + 7 días`, fijo al generar (`ADR-012`) |
| `usada_en` | datetime \| null | se completa al aceptar |

**Invariantes:**
- **INV-ID-01:** una invitación con `usada_en` no null no puede volver a aceptarse (uso único).
- **INV-ID-02:** `expira_en = generada_en + 7 días`, calculado una sola vez al generar — no se
  recalcula ni se extiende (`ADR-012`, sin mecanismo de reenvío/extensión en v1).
- **INV-ID-03:** una invitación es válida para aceptar solo si `ahora < expira_en` y
  `usada_en is null`. Fuera de esa ventana: rechazo sin recuperación automática (`ADR-012`).

### `Usuario` (Aggregate Root)

Resuelto con Víctor (2026-07-17, §8): `Usuario` guarda solo lo común a los tres roles
(identidad y credenciales). Estudiante/Docente/Administrador dejan de ser un tag (`rol`) con
atributos condicionales y pasan a ser **Entities subordinadas**, dentro del límite de
consistencia de `Usuario` — cada `Usuario` tiene exactamente un perfil, creado atómicamente en
el mismo comando que crea el `Usuario` (no puede existir un `Usuario` sin perfil, ni un perfil
huérfano).

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `nombre` | string | |
| `email` | string único | |
| `password_hash` | string | bcrypt (`ADR-014`) |
| `creado_en` | datetime | |
| `perfil` | `Estudiante \| Docente \| Administrador` | Entity subordinada, exactamente una — ver abajo |
| `bloqueada` | bool | `true` tras 3 intentos fallidos consecutivos (RF-19, INV-ID-10) |
| `intentos_fallidos_login` | int | se resetea a 0 en cada login exitoso |
| `intentos_fallidos_password` | int | se resetea a 0 en cada `CambiarPassword` exitoso — contador independiente del de login |

**Invariantes:**
- **INV-ID-04:** `email` único en todo el sistema (sin distinción de rol).
- **INV-ID-06:** `password_hash` nunca se persiste ni se expone en texto plano — solo bcrypt
  (`ADR-014`).
- **INV-ID-09:** todo `Usuario` tiene exactamente un `perfil` (`Estudiante`, `Docente` o
  `Administrador`), asignado en el momento de creación y no reasignable en v1 (no hay RF de
  cambio de rol).

#### `Estudiante` (Entity, `id = usuario_id`, subordinada de `Usuario`)

| Atributo | Tipo | Notas |
|---|---|---|
| `comision_id` | referencia a `Comisión` | asignado en el registro, sin aprobación del docente (RF-01) |

- **INV-ID-05:** un `Estudiante` siempre tiene `comision_id` asignado desde su creación
  (RF-01) — no existe `Estudiante` sin comisión.

#### `Docente` (Entity, `id = usuario_id`, subordinada de `Usuario`)

Sin atributos propios en v1 más allá de existir como tipo — es el actor real de
`GenerarInvitacion` (§3) y el elemento referenciado por `Comisión.docentes_asignados` (§4), en
vez de "un `Usuario` con `rol == docente`". Las comisiones que dicta se derivan de
`Comisión.docentes_asignados` (read model), no se duplican acá.

#### `Administrador` (Entity, `id = usuario_id`, subordinada de `Usuario`)

Sin atributos propios en v1 (gestión de cuentas es RF-03, Incremento 2) — existe como
concepto explícito, es el actor de `CrearComision` y `AsignarDocenteAComision` (§4).

### `Comisión` (Aggregate Root)

Resuelto con Víctor (hot spots 1 y 4): una Comisión es el espacio de dictado de una materia
— tiene horario, docentes asignados y estudiantes inscriptos. Puede haber más de una comisión
por materia.

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `materia` | string \| referencia | ver nota de alcance más abajo |
| `horario` | string/estructura | sin más detalle requerido por RF-01/RF-02 |
| `docentes_asignados` | lista de referencias a `Docente` (`Usuario.id` con perfil `Docente`) | mutada por `AsignarDocenteAComision` |

`estudiantes_inscriptos` **no** es estado propio de `Comisión` — es un read model derivado de
`Estudiante.comision_id` (INV-ID-05). Mantenerlo como colección propia de `Comisión` obligaría
a mutar dos aggregates en la misma transacción (`Usuario` + `Comisión`) cada vez que se
registra un estudiante; con `Estudiante.comision_id` como única fuente de verdad, el registro
de un estudiante solo toca el aggregate `Usuario`.

**Invariantes:**
- **INV-ID-07:** puede existir más de una `Comisión` para la misma materia.
- **INV-ID-08:** un docente debe estar en `docentes_asignados` de una `Comisión` para poder
  ejecutar `GenerarInvitacion` sobre ella — resuelve el hot spot 4 original.

**Comandos → Eventos (nuevos):**

| Comando | Actor | Evento | Excepciones |
|---|---|---|---|
| `CrearComision(materia, horario, administrador_id)` | Administrador | `ComisionCreada` | — |
| `AsignarDocenteAComision(comision_id, docente_id)` | Administrador | `DocenteAsignado` | `UsuarioNoEsDocente` |

**Nota de alcance — BC:** `Comisión` se modela dentro de BC Identidad porque es este BC el
que necesita hacer cumplir INV-ID-08 y RF-01 (asignación automática de estudiante a
comisión). Si más adelante otros BCs (Banco de Preguntas, Actividad Evaluativa) necesitan más
que una referencia por id a la comisión, se expone por puerto (`entities/ports/`) — no se
duplica el aggregate.

### Value Objects

- **`Rol`** — `administrador | docente | estudiante` (RF-02). Ya no es un atributo propio de
  `Usuario` (§8) — se **deriva** del tipo concreto de `perfil` (`Estudiante → estudiante`,
  `Docente → docente`, `Administrador → administrador`). Determina qué endpoints puede invocar
  un `Usuario` (autorización RBAC, `ADR-007`) — el detalle de qué recurso corresponde a qué rol
  se especifica en las US de la Iteración 1, no en este modelo.
- **`JWT`** — no es parte del aggregate `Usuario`; se emite en el comando `IniciarSesion` con
  claim de `rol` (derivado del `perfil`), expira a los 60 minutos, sin refresh ni blacklist
  (`ADR-013`). No se persiste server-side (diseño stateless de `ADR-007`).

---

## 5. Hot spots — resueltos con Víctor (2026-07-17)

1. **¿Qué es "Comisión"?** Resuelto — es el espacio de dictado de una materia: horario,
   docentes asignados, estudiantes inscriptos; puede haber más de una comisión por materia.
   Modelada como aggregate `Comisión` dentro de este BC (§4).
2. **¿Los rechazos son eventos de dominio persistidos?** Resuelto — no. `RegistroRechazado` e
   intento de login fallido son excepciones de aplicación (4xx), no entran al Event Store. Sin
   RNF de auditoría/seguridad que lo exija en v1.
3. **¿Envío de email — mismo comando o policy separada?** Resuelto — mismo comando
   `GenerarInvitacion`, side-effect directo del handler. Sin desacoplar prematuramente (mismo
   criterio que `ADR-012` sobre no adelantar abstracciones).
4. **¿Se valida asignación docente↔comisión?** Resuelto — sí. Es justamente el dato que trae
   el aggregate `Comisión` (`docentes_asignados`, INV-ID-08).

## 6. Pregunta abierta — resuelta con Víctor (2026-07-17)

Al modelar `Comisión` como aggregate con lifecycle propio, faltaba definir quién la crea y
quién asigna docentes — ningún RF cubre alta de comisiones. Resuelto: el **Administrador**
crea Comisiones y asigna docentes, dentro del producto (no seed/fixture) — se agrega una nueva
US a la Iteración 1 (`US-1.1.0`, ver `docs/plans/inc1/inc1-candidatas.md`). Esto también fija
el actor de `AsignarDocenteAComision` (§4): **Administrador**, y agrega el comando
`CrearComision(materia, horario, administrador_id)` → evento `ComisionCreada`.

---

## 8. Ajuste de modelo — perfiles de rol como Entities (resuelto con Víctor, 2026-07-17)

Observación de Víctor sobre la primera versión: Estudiante y Docente son los usuarios reales
de la aplicación, con perfiles bien definidos — no estaban modelados como tales, solo como un
`Usuario` genérico con un VO `Rol` y atributos condicionales según el valor de ese VO (patrón
anémico). Resuelto: `Estudiante`, `Docente` y `Administrador` pasan a ser **Entities
subordinadas** de `Usuario` (id compartido, `id = usuario_id`, 1:1) — viven dentro del límite
de consistencia de `Usuario` en vez de como aggregates propios, porque siempre se crean
atómicamente junto con él y no hay un RF que requiera evolucionarlas de forma
transaccionalmente independiente todavía. Si en un incremento futuro (ej. Incremento 4,
Analytics) `Estudiante` necesita atributos o invariantes propias que no dependan del ciclo de
vida de `Usuario`, se reevalúa promoverla a aggregate root — no antes.

Cambios que esto produjo en el resto del modelo: `Usuario` deja de tener `rol` y `comision_id`
como atributos propios (§4); `Comisión.docentes_asignados` referencia `Docente` en vez de
`Usuario` genérico (§4); `Rol` pasa de atributo a VO derivado del tipo de `perfil` (§4,
"Value Objects").

---

## 9. Alta de usuario, ciclo de vida de credenciales y bootstrap (resuelto con Víctor, 2026-07-17)

Observación de Víctor: la invitación por link (RF-01) es la forma en que se registra un
**Estudiante**, no "la" forma general de alta de un `Usuario` — y el modelo tampoco
contemplaba las operaciones estándar de autenticación (cambio y recuperación de password).
Resuelto:

1. **Alta directa de usuario** — se agrega el comando `CrearUsuario(nombre, email, password,
   perfil)`, actor Administrador, que crea `Usuario` + el perfil indicado (`Docente`,
   `Administrador` o `Estudiante`) en la misma transacción (§3). Se implementa **ya en el
   Incremento 1**: sin esto, `US-1.1.0` no tiene forma de dar de alta al `Docente` que después
   asigna a una `Comisión` — `inc1-candidatas.md` se actualiza para incluirlo en `US-1.1.0`.
2. **Cambio de password** (`CambiarPassword`, self-service) — se modela (§3, "Diferidos"); en
   el momento de esta decisión (2026-07-17) todavía no tenía RF propio, resuelto después en
   §11 (RF-19). Sin US en el Incremento 1 — se implementa en el Incremento 2 junto a RF-03.
3. **Recuperación por olvido de password** (`ResetearPassword`) — mediada por Administrador,
   consistente con la letra de RF-03 ("el administrador puede... gestionar las cuentas para
   resolver problemas — bloqueos, recuperación"). Se modela (§3, "Diferidos") pero su US
   corresponde a RF-03, Incremento 2 — no self-service por email en v1.
4. **Bootstrap del primer Administrador** — problema de huevo-y-gallina: `CrearUsuario` lo
   ejecuta un Administrador, así que el primero no puede darse de alta a sí mismo por ese
   comando. Se crea por **seed/fixture fuera del producto** (script o migración de Alembic al
   desplegar el entorno), no por una Feature — mismo criterio que un superusuario de Django.
   Documentar la decisión operativa (candidato a ADR corto) cuando se implemente `US-1.1.0`.

---

## 11. RF-19 — Cambio de contraseña por el propio usuario (elicitado con Víctor, 2026-07-17)

`CambiarPassword` (punto 2 de §9) quedó modelado sin RF que lo sostuviera — se resolvió con
una sesión de elicitación dedicada (`elicitacion-rf`), agregando **RF-19** a `RF_v1.md`
(revisión 2026-07-17, documento no reescrito — solo se agrega el ítem nuevo). Resultado
incorporado al modelo (§3, "Diferidos", y atributos de `Usuario` en §4):

- Cualquier usuario autenticado cambia su propia contraseña (contraseña actual + nueva).
- Contraseña nueva: mínimo 8 caracteres — regla que también aplica a `CrearUsuario` y
  `RegistrarEstudiante` (INV-ID-11), no exclusiva de este flujo.
- 3 intentos fallidos **consecutivos** (se resetea a cero en cada acierto) bloquean la cuenta
  — tanto en `CambiarPassword` como en `IniciarSesion`, con contadores independientes
  (INV-ID-10).
- Desbloquear una cuenta y resetear su contraseña son la misma operación
  (`ResetearPassword`, actor Administrador) — no hay un comando separado de desbloqueo.
- Cambiar la contraseña no invalida el JWT en curso (sin blacklist, `ADR-013`).

`RF-19` se agrupa con `RF-03` en el Incremento 2 (mismo actor, mismo mecanismo de reseteo) —
no cambia el alcance del Incremento 1 (`inc1-candidatas.md` actualizado).

---

## 12. Próximo paso

Modelo completo (sin hot spots, preguntas abiertas ni observaciones de diseño pendientes) —
pasa a aprobación explícita de Víctor en el comentario de cierre de
https://github.com/vvalotto/cognion/issues/2 (DoD tipo `Modelado`, `WORKFLOW-DESARROLLO.md`
§2).
