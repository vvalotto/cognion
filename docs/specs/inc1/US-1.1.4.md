# US-1.1.4: Docente, administrador y estudiante se autentican y reciben un JWT con su rol

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.1`
**Tipo**: `feat backend` + `feat frontend`
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Docente, Administrador o Estudiante** con una cuenta ya creada,
quiero **autenticarme con mi email y contraseña**
para **recibir un JWT con mi rol y poder operar el resto del sistema según los permisos que me
corresponden (RF-02)**.

---

## Contexto del dominio

### Problema

Es el punto de entrada común a los tres perfiles — sin esta US ninguna de las demás US-IEDD del
sistema (más allá de registro/invitación) puede exigir un actor autenticado. Habilita
`US-1.1.5` (autorización por rol).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Usuario` | Se consulta por `email`, incluye `perfil` |
| Value Object | `Rol` | Derivado del tipo concreto de `perfil` (`Estudiante → estudiante`, `Docente → docente`, `Administrador → administrador`) |
| Value Object | `JWT` | Emitido con claim `rol`; expira a los 60 minutos, sin refresh ni blacklist (`ADR-013`) |
| Command | `IniciarSesion(email, password)` | Dispara la autenticación |
| Domain Event | `SesionIniciada` | Señala la emisión exitosa |
| Port | `PasswordHasherPort`, `JWTIssuerPort` | Verificación de hash y emisión de token |

---

## Especificacion del comportamiento

### Precondicion

- Existe un `Usuario` con ese `email`.

### Postcondicion

- Si la contraseña verifica contra `password_hash` (bcrypt): se emite un JWT con claim `rol`
  derivado del tipo de `perfil` del `Usuario`, `exp` a 60 minutos desde la emisión. Evento
  `SesionIniciada`.
- Si no verifica, o el `email` no existe: rechazo genérico `CredencialesInvalidas` — el mensaje
  no distingue si el email existe o no, para no filtrar existencia de cuentas
  (`wireframes-identidad.md` §2.2).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El JWT expira a los 60 minutos desde la emisión, sin mecanismo de refresh ni blacklist (`ADR-013`). |
| — | El claim `rol` del JWT se deriva siempre del tipo concreto de `perfil` del `Usuario` autenticado — nunca se recibe como input del comando. |
| — | El intento de login fallido no persiste como evento de dominio — es una excepción de aplicación (`BC-identidad-modelo.md` §5, hot spot 2). |

---

## Criterios de aceptacion

```gherkin
Feature: Autenticación con JWT por rol

  Scenario: Login exitoso de un Docente
    Given un Usuario con perfil Docente y contraseña "Docente#2026"
    When ejecuta IniciarSesion(email, "Docente#2026")
    Then el sistema emite un JWT con claim rol="docente"
    And el JWT expira 60 minutos después de la emisión
    And se emite el evento SesionIniciada

  Scenario: Login exitoso de un Administrador
    Given un Usuario con perfil Administrador
    When ejecuta IniciarSesion(email, password correcta)
    Then el sistema emite un JWT con claim rol="administrador"

  Scenario: Login exitoso de un Estudiante
    Given un Usuario con perfil Estudiante
    When ejecuta IniciarSesion(email, password correcta)
    Then el sistema emite un JWT con claim rol="estudiante"

  Scenario: Rechazo por contraseña incorrecta
    Given un Usuario existente
    When ejecuta IniciarSesion(email, password incorrecta)
    Then el sistema rechaza con CredencialesInvalidas
    And el mensaje no distingue si el email existe

  Scenario: Rechazo por email inexistente
    Given ningún Usuario registrado con ese email
    When se ejecuta IniciarSesion(email, cualquier password)
    Then el sistema rechaza con CredencialesInvalidas
    And el mensaje es idéntico al del caso de contraseña incorrecta
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — decisiones ya tomadas en `ADR-007` (JWT+RBAC) y `ADR-013` (expiración)

**Capa(s) afectadas:**
- [x] Entities — VO `Rol` (derivación), VO `JWT`
- [x] Use Cases — `IniciarSesionUseCase`
- [x] Interface Adapters — controller, `UsuarioRepositoryPort`
- [x] Frameworks — endpoint FastAPI `POST /identidad/login`, adaptador PyJWT
- [x] Frontend — pantallas de login y error

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-identidad.md` §2.1 (Login) y §2.2 (Login — error).
- Prototipo: `docs/design/ux/prototipos/identidad-registro-login.html` (`#login`,
  `#login-error`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/rol.py` | VO `Rol`, derivación desde el tipo de `perfil` |
| `src/identidad/entities/jwt.py` | VO `JWT` (claims, expiración) |
| `src/identidad/entities/ports/jwt_issuer_port.py` | Puerto de emisión/verificación |
| `src/identidad/use_cases/iniciar_sesion.py` | Orquesta verificación de password + emisión de JWT |
| `src/identidad/interface_adapters/controllers/auth_controller.py` | Validación de entrada, mapeo a use case |
| `src/identidad/frameworks/security/jwt_pyjwt.py` | Adaptador PyJWT + cryptography (`ADR-007`) |
| `src/identidad/frameworks/api/auth_router.py` | Endpoint FastAPI `POST /identidad/login` |
| `frontend/src/features/identidad/Login.tsx` | Pantalla `#login` |
| `frontend/src/features/identidad/LoginError.tsx` (o estado inline) | Pantalla `#login-error` |
| `frontend/src/lib/auth.ts` | Almacenamiento del JWT en el cliente, cabecera `Authorization` |

---

## Referencias

- Relacionada con: `US-1.1.0`, `US-1.1.2`, `US-1.1.5`, `ADR-007`, `ADR-013`
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` (§3, §4 `Value Objects`)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
