# Incremento 1 — BC Identidad — US candidatas

> Estado documental: **Iteración 0 — Modelado cerrada (2026-07-18).** US-1.0.1 (modelo de
> dominio, Issue #2) y US-1.0.2 (wireframes de registro/login/alta de Docente, Issue #4)
> aprobadas por Víctor. Esta tabla ya puede usarse como base para elaborar las US-IEDD formales
> de la Iteración 1 (WORKFLOW-DESARROLLO.md §3, paso 1) — revisarla contra el modelo aprobado
> antes de crear los Issues y specs, por si el event storming o los wireframes ajustaron algún
> comando/evento respecto de lo anticipado acá.
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 1, `docs/rf/RF_v1.md` (RF-01, RF-02),
> `ADR-012` (invitación), `ADR-013` (JWT), `ADR-014` (bcrypt).

---

## Iteración 0 — Modelado

Dos US-IEDD **tipo `Modelado`** (WORKFLOW-DESARROLLO.md §1, §2) — mismo esquema que el resto,
DoD = artefacto aprobado explícitamente por Víctor en el comentario que cierra el Issue. Ambas
deben estar cerradas antes de pasar a la Iteración 1.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-1.0.1** | Modelado | Event storming BC Identidad: aggregates (`Usuario`, `Invitación`), Value Object `Rol`, eventos de dominio (ej. `InvitacionGenerada`, `InvitacionAceptada`, `UsuarioRegistrado`, `SesionIniciada`), comandos, invariantes — incluida la asignación automática a comisión y el rechazo sin recuperación de invitación vencida/inválida (`ADR-012`) | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-identidad-modelo.md` |
| **US-1.0.2** | Modelado | Wireframes de registro (vía link de invitación, con estado de link vencido/inválido) y login | Víctor aprueba los wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-identidad.md` + prototipo en `docs/design/ux/prototipos/` |

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` §4 — los escenarios RNF
que este incremento aborda pasan de *Planificado* a *Especificado* (WORKFLOW-DESARROLLO.md
§3, paso 0e).

---

## Iteración 1 — RF-01, RF-02: registro por invitación, roles, JWT

Formato compacto (precedente: AtaraxiaDive Inc 1.2 "El dominio habla") — tabla en vez de
narrativa larga, porque es el primer incremento con dominio real y todavía no hay agregados
maduros que justifiquen una spec extensa por US.

| US | Descripción | Comando | Evento(s) | Actor | Invariantes clave | Precondición → Postcondición |
|---|---|---|---|---|---|---|
| **US-1.1.0** | Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes — precondición de todo lo demás: sin esto no hay `Docente` ni `Comisión` contra qué validar `GenerarInvitacion` | `CrearUsuario(nombre, email, password, perfil)`, `CrearComision(materia, horario, administrador_id)`, `AsignarDocenteAComision(comision_id, docente_id)` | `UsuarioCreado`, `ComisionCreada`, `DocenteAsignado` | Administrador | `Usuario` + perfil se crean en la misma transacción (INV-ID-09); email único (INV-ID-04, `EmailYaRegistrado` si no); password hasheado con bcrypt (INV-ID-06, `ADR-014`); puede existir más de una comisión por materia (INV-ID-07); solo un `Usuario` con perfil `Docente` puede ser asignado (`UsuarioNoEsDocente` si no) | Administrador autenticado → `Usuario`(es) con perfil `Docente` creados, `Comisión` persistida con al menos un `Docente` en `docentes_asignados` |
| **US-1.1.1** | Docente genera link de invitación para una comisión | `GenerarInvitacion(comision_id, docente_id)` | `InvitacionGenerada` | Docente | Solo un `Docente` asignado a la comisión puede generarla (INV-ID-08); expiración = 7 días desde la emisión (`ADR-012`) | `Docente` autenticado y presente en `docentes_asignados` de la comisión → invitación persistida con token único y `expira_en` calculado |
| **US-1.1.2** | Estudiante se registra con un link de invitación válido y queda asignado a la comisión sin aprobación del docente | `RegistrarEstudiante(token, datos_usuario)` | `UsuarioRegistrado`, `InvitacionAceptada` | Estudiante | Invitación no usada, no vencida (INV-ID-01, INV-ID-03); asignación a comisión es automática e inmediata (RF-01, INV-ID-05); email único (INV-ID-04, `EmailYaRegistrado` si no); password hasheado con bcrypt (INV-ID-06, `ADR-014`) | Invitación válida y vigente → `Usuario` + perfil `Estudiante` creados en la misma transacción (INV-ID-09), `Estudiante.comision_id` = comisión de la invitación |
| **US-1.1.3** | Estudiante intenta registrarse con link vencido o inválido y el sistema rechaza sin recuperación automática | `RegistrarEstudiante(token, datos_usuario)` | `RegistroRechazado` | Estudiante | Sin mecanismo de reenvío automático — el docente debe generar una invitación nueva (`ADR-012`) | Invitación vencida (`expira_en` pasado) o token inexistente → error explícito, ningún `Usuario` creado |
| **US-1.1.4** | Docente, administrador y estudiante se autentican con usuario/contraseña y reciben un JWT con su rol | `IniciarSesion(email, password)` | `SesionIniciada` | Docente, Administrador, Estudiante | JWT expira a los 60 minutos, sin refresh ni blacklist (`ADR-013`); password verificado contra hash bcrypt; claim `rol` derivado del tipo de `perfil` (`Docente`/`Administrador`/`Estudiante`) | Credenciales válidas → JWT emitido con claim de rol correcto |
| **US-1.1.5** | El sistema restringe el acceso a funcionalidades según el rol del usuario autenticado | (query/guard, sin nuevo evento) `VerificarAcceso(jwt, recurso)` | — | Sistema (dependency `get_current_user`) | `Estudiante` no accede a banco de preguntas ni analytics globales; `Docente` no accede a administración de cuentas (RF-02, criterios de aceptación) | JWT válido con rol insuficiente para el recurso → 403; rol suficiente → acceso concedido |

**Nota sobre US-1.1.0:** no tiene RF propio — surgió como necesidad derivada del event
storming (`BC-identidad-modelo.md` §6 y §9): sin `Comisión` con al menos un docente asignado,
ni forma de dar de alta a ese docente sin invitación, no hay manera de probar el flujo de
punta a punta de RF-01/RF-02. Se resuelve dentro del producto (Administrador lo ejecuta), no
como seed/fixture. La única excepción real es el **primer** Administrador — problema de
huevo-y-gallina, se crea por seed/fixture al desplegar el entorno (`BC-identidad-modelo.md`
§9, punto 4).

**Fuera de alcance de esta iteración** (queda para el Incremento 2, BC Identidad extendido):
RF-03 (gestión de cuentas por administrador — bloqueos, recuperación) y RF-19 (cambio de
contraseña por el propio usuario, con bloqueo automático a los 3 intentos fallidos
consecutivos — en login y en cambio de contraseña, contadores independientes). `RF-19` ya
tiene RF propio (elicitado 2026-07-17, ver `docs/rf/RF_v1.md`), pero se agrupa con RF-03 en el
Incremento 2 porque comparten mecanismo: desbloquear una cuenta y resetear su contraseña son
la misma operación (`ResetearPassword`, actor Administrador).

---

## Iteración 2 — Frontend de Identidad (cierra la Iteración 1 de cara al Hito del Incremento)

> Decisión 2026-07-24 (`docs/plans/PLAN-CM.md` §7): una Baseline con gate UX aprobado no
> cierra backend-only — BL-002 espera a que este frontend también esté implementado. No
> requiere una nueva Iteración 0 — Modelado: el wireframe ya está aprobado
> (`docs/design/ux/wireframes-identidad.md`, US-1.0.2/Issue #4) y el backend que cada pantalla
> consume ya está implementado y probado (US-1.1.0, US-1.1.2 a US-1.1.5).
>
> **Fuera de alcance de esta iteración:** UI de `CrearComision`/`AsignarDocenteAComision` — el
> wireframe las deja explícitamente sin resolver (§4) y el Hito del Incremento no las requiere
> como flujo demostrable. Se retoma si una iteración futura lo necesita.

| US | Descripción | Pantallas (`wireframes-identidad.md`) | Backend consumido | Depende de |
|---|---|---|---|---|
| **US-1.1.6** | Infraestructura de frontend: routing, cliente API con manejo de JWT/401/403, layout auth vs. layout app | Sin pantalla propia — soporte técnico | — | — |
| **US-1.1.7** | Docente/Administrador/Estudiante inicia sesión desde la UI | §2.1 `#login`, §2.2 `#login-error` | `POST /identidad/login` (US-1.1.4) | US-1.1.6 |
| **US-1.1.8** | Estudiante se registra desde la UI con un link de invitación | §2.3 `#registro`, §2.4 `#registro-error`, §2.5 `#registro-exito` | `POST /identidad/registro` (US-1.1.2, US-1.1.3) | US-1.1.6 |
| **US-1.1.9** | Administrador da de alta un Docente desde la UI | §2.6 `#alta-docente`, §2.7 `#alta-docente-exito` | `POST /usuarios` con `perfil=docente`, protegido por `require_administrador` (US-1.1.0, US-1.1.5) | US-1.1.6 |

**Orden de implementación:** US-1.1.6 primero (bloquea a las otras tres). US-1.1.7 antes que
1.1.8/1.1.9 — valida la infraestructura con el flujo más simple del wireframe antes de encarar
los flujos con más estados (registro: 3 pantallas; alta de docente: ruta protegida + rol).

> ~~US-1.1.6 (Infraestructura de frontend)~~ Cerrada 2026-07-24 —
> `docs/reports/inc1/US-1.1.6-report.md`, 16/16 tests, quality gates APROBADO. Desbloquea
> US-1.1.7.

> ~~US-1.1.7 (Docente/Administrador/Estudiante inicia sesión desde la UI)~~ Cerrada 2026-07-27 —
> `docs/reports/inc1/US-1.1.7-report.md`, 21/21 tests, quality gates APROBADO. Próxima:
> US-1.1.8.

---

## DoD del Incremento (hito, `PLAN_v1.md`)

> Un estudiante se registra vía link de invitación y queda asignado automáticamente a su
> comisión; un docente y un administrador se autentican y reciben un JWT con su rol correcto.
> Corre en el entorno local sobre la fundación técnica del Incremento 0.

Se verifica de punta a punta en UAT (Capa 1 pytest + Capa 2 HTTP) al cierre del incremento,
según `PROCEDIMIENTO-UAT.md` — no basta con que cada US individual pase sus propios tests.

---

## Próximos pasos

1. ~~Ejecutar Iteración 0 — Modelado (event storming + wireframes) y obtener aprobación
   explícita de Víctor.~~ Cerrada 2026-07-18 (US-1.0.1, Issue #2; US-1.0.2, Issue #4).
2. Con el modelo y los wireframes aprobados, revisar esta tabla de candidatas — ajustar
   comandos/eventos si el event storming o el prototipo UX revelan agregados, invariantes o
   pantallas distintas a las anticipadas acá.
3. Crear GitHub Issues (Milestone `Incremento 1 — BC Identidad`, labels `us-iedd`,
   `incremento-1`) y `docs/specs/inc1/US-1.1.K.md` por cada US aprobada.
4. Actualizar `docs/traceability/matrix.md`: RF-01 y RF-02 pasan de *Planificado* a
   *Especificado*, completando la columna US-IEDD.
5. ~~Iteración 1 (RF-01, RF-02): backend completo.~~ Cerrada 2026-07-24 (US-1.1.0 a US-1.1.5,
   132/132 tests). RF-01 y RF-02 pasan a *Implementado* en la matriz.
6. Iteración 2 — Frontend de Identidad aprobada por Víctor 2026-07-24 (tabla arriba). Crear
   Issues (Milestone `Incremento 1 — BC Identidad`) y `docs/specs/inc1/US-1.1.{6,7,8,9}.md`.
   Recién con esto integrado se abre BL-002 (`docs/plans/PLAN-CM.md` §7).
