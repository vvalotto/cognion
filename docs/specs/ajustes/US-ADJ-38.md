# US-ADJ-38: Solicitar recuperación de contraseña (endpoint público)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 2
**Tipo**: `feature` (backend nuevo, endpoint público)
**Bounded Context**: Identidad (con dependencia nueva hacia Notificaciones)
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 2. Modelo aprobado:
`docs/design/domain/BC-identidad-modelo.md` §13.2/13.3 (`US-ADJ-32`). Primera de la
Iteración — `US-ADJ-39` depende de que el token ya se pueda generar.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §4.1 ("Recuperar — solicitar") y §4.2
("Recuperar — email enviado"). Prototipo navegable:
`docs/design/ux/prototipos/identidad-autoservicio.html` (`#recuperar-solicitar`,
`#recuperar-solicitado`). Sin pantalla propia todavía — esta US es backend puro
(`US-ADJ-40` construye las pantallas).

---

## Descripcion (lenguaje de negocio)

Como **cualquier persona con una cuenta en el sistema que olvidó su contraseña**,
quiero **pedir un link de recuperación ingresando mi email**
para **poder definir una contraseña nueva sin depender del Administrador**.

---

## Contexto del dominio

### Problema

Hoy la única forma de recuperar el acceso a una cuenta con contraseña olvidada es que el
Administrador la resetee manualmente (`US-2.2.4`/`ResetearPasswordUseCase`) — funciona, pero
depende de que exista un Administrador disponible y de que el usuario sepa contactarlo. No hay
mecanismo de autoservicio.

### Alcance del fix

**Backend nuevo**, BC Identidad:

1. Aggregate nuevo `TokenRecuperacionPassword` (`entities/token_recuperacion_password.py`):
   `id`, `usuario_id`, `token` (string único, no adivinable — mismo generador criptográfico que
   ya usa `Invitación`), `generado_en`, `expira_en` (`generado_en + 1 hora`, INV-ID-13),
   `usado_en: datetime | None`.
2. Puerto nuevo `TokenRecuperacionPasswordRepositoryPort` (`entities/ports/`): `guardar()`,
   `obtener_por_token()`, `invalidar_activos_de(usuario_id)` (soporta INV-ID-12 — a lo sumo un
   token activo por usuario).
3. Comando `SolicitarRecuperacionPassword(email)` → `SolicitarRecuperacionPasswordUseCase`:
   busca el `Usuario` por email; si existe, invalida cualquier token activo previo del mismo
   usuario (INV-ID-12), genera uno nuevo, lo persiste, y dispara el envío del email. Si no
   existe, no hace nada — pero **responde exactamente igual** al llamante en ambos casos
   (INV-ID-17, no filtrar existencia de cuentas).
4. Puerto nuevo hacia Notificaciones: `CanalRecuperacionPort` (`entities/ports/`, BC Identidad)
   con adapter in-process (`frameworks/adapters/canal_recuperacion_port_in_process.py`) que
   invoca el `CanalEnvioPort`/`SmtpCanalEnvio` ya existente de BC Notificaciones (`ADR-006`,
   mismo patrón que `NotificacionPort` de Actividad Evaluativa → Notificaciones,
   `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py`) — **no** el
   `NotificadorPort`/SMTP propio de Identidad que usa `GenerarInvitacion` (nota de diseño de
   `BC-identidad-modelo.md` §13.2: primera vez que Identidad depende de un puerto de
   Notificaciones).
5. Endpoint nuevo `POST /identidad/recuperar-password/solicitar` (público, sin `Depends` de
   autenticación) — body `{email}`, responde siempre `202 Accepted` con el mismo mensaje
   genérico, sin importar si el email existe o no.
6. Migración Alembic: tabla `token_recuperacion_password` (o columna equivalente si se decide
   reusar la tabla de `invitacion` — a resolver en la implementación, evaluando si el shape
   difiere lo suficiente para justificar tabla propia; mismo criterio de "tabla propia por
   aggregate" ya usado para `invitacion`).

**Fuera de alcance de esta US:**
- Confirmar el token y fijar la contraseña nueva — `US-ADJ-39`.
- Cualquier pantalla — `US-ADJ-40`.
- Cuenta SMTP real de producción — sigue el `SmtpCanalEnvio` de prueba ya configurado
  (`CLAUDE.md` §"Ítems abiertos").

---

## Especificacion del comportamiento

### Precondicion

- No existe ningún mecanismo de autoservicio de recuperación de contraseña.
- `Usuario` no tiene relación con ningún `TokenRecuperacionPassword` (aggregate no existe).

### Postcondicion

- Un `POST /identidad/recuperar-password/solicitar` con un email de cuenta existente crea un
  `TokenRecuperacionPassword` válido por 1 hora e invalida cualquier token previo sin usar del
  mismo usuario.
- El mismo endpoint con un email que no corresponde a ninguna cuenta no crea nada, pero
  responde igual (mismo status, mismo body) que el caso exitoso.
- El email se envía a través del canal de Notificaciones (`SmtpCanalEnvio`), no del canal
  propio de invitaciones de Identidad.
- Un fallo de envío de email no bloquea la respuesta al llamante — mismo criterio de "un fallo
  de envío no bloquea la operación de dominio" ya aplicado en Notificaciones (`BL-009`).

### Invariantes

- **INV-ID-12:** a lo sumo un `TokenRecuperacionPassword` activo (sin usar y sin vencer) por
  `Usuario`.
- **INV-ID-13:** `expira_en = generado_en + 1 hora`, fijo al generar, sin extensión.
- **INV-ID-17:** la respuesta de `SolicitarRecuperacionPassword` es indistinguible exista o no
  la cuenta.

---

## Criterios de aceptacion

```gherkin
Feature: Solicitar recuperación de contraseña (US-ADJ-38)

  Scenario: Solicitar recuperación con un email de cuenta existente
    Given un Usuario con email "docente@fiuner.edu.ar" registrado
    When se hace POST /identidad/recuperar-password/solicitar con ese email
    Then la respuesta es 202 Accepted con el mensaje genérico
    And se crea un TokenRecuperacionPassword para ese Usuario, vigente 1 hora

  Scenario: Solicitar recuperación con un email que no existe
    Given ningún Usuario tiene el email "inexistente@fiuner.edu.ar"
    When se hace POST /identidad/recuperar-password/solicitar con ese email
    Then la respuesta es 202 Accepted con el mismo mensaje genérico que el caso exitoso
    And no se crea ningún TokenRecuperacionPassword

  Scenario: Solicitar dos veces invalida el token anterior
    Given un Usuario ya tiene un TokenRecuperacionPassword activo sin usar
    When se solicita una nueva recuperación para el mismo email
    Then el token anterior queda invalidado
    And se crea un token nuevo, distinto del anterior

  Scenario: Un fallo de envío de email no bloquea la respuesta
    Given el canal de envío de Notificaciones falla al intentar enviar
    When se solicita una recuperación con un email de cuenta existente
    Then la respuesta sigue siendo 202 Accepted
    And el TokenRecuperacionPassword queda creado igual
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — primera vez que BC Identidad consume un puerto de BC Notificaciones (hasta ahora la
  dependencia entre BCs de este tipo siempre fue en sentido Actividad Evaluativa →
  Notificaciones). Se resuelve con el mismo mecanismo ya ratificado (`ADR-006`: puerto propio
  del BC consumidor + adapter in-process), sin adapter directo ni import cruzado — no amerita
  un ADR nuevo, es una aplicación más del patrón ya decidido.

**Capa(s) afectadas:**
- [x] Entities — aggregate `TokenRecuperacionPassword`, puertos
  `TokenRecuperacionPasswordRepositoryPort`, `CanalRecuperacionPort`
- [x] Use Cases — `SolicitarRecuperacionPasswordUseCase`
- [x] Interface Adapters — controller/endpoint nuevo
- [x] Frameworks — adapter in-process hacia Notificaciones, repositorio SQLAlchemy, migración
  Alembic

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/token_recuperacion_password.py` | Aggregate nuevo |
| `src/identidad/entities/ports/token_recuperacion_password_repository_port.py` | Puerto nuevo |
| `src/identidad/entities/ports/canal_recuperacion_port.py` | Puerto nuevo (Identidad → Notificaciones) |
| `src/identidad/frameworks/adapters/canal_recuperacion_port_in_process.py` | Adapter nuevo |
| `src/identidad/use_cases/solicitar_recuperacion_password.py` | Use case nuevo |
| `src/identidad/interface_adapters/controllers/` (o equivalente) | Endpoint `POST /identidad/recuperar-password/solicitar` |
| `src/identidad/frameworks/db/` + migración Alembic | Persistencia de `TokenRecuperacionPassword` |
| `src/identidad/frameworks/dependencies.py` | Composition root: cablear el nuevo use case y el adapter hacia Notificaciones |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 2
- `docs/design/domain/BC-identidad-modelo.md` §13.2, §13.3
- `docs/design/ux/wireframes-identidad-autoservicio.md` §4.1, §4.2
- Issue: [#339](https://github.com/vvalotto/cognion/issues/339)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
