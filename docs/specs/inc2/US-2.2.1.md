# US-2.2.1: Bloqueo automático de cuenta por 3 intentos fallidos consecutivos de login

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **sistema**,
quiero **bloquear automáticamente una cuenta tras 3 intentos fallidos consecutivos de login**
para **frenar intentos de fuerza bruta sobre las credenciales, sin intervención manual**.

---

## Contexto del dominio

### Problema

`IniciarSesion` (`US-1.1.4`) hoy rechaza credenciales inválidas sin llevar ningún contador —
no hay límite a los reintentos. RF-19 (elicitado 2026-07-17,
`BC-identidad-modelo.md` §11) agrega un mecanismo de bloqueo automático, con un contador
propio para login y otro independiente para `CambiarPassword` (`US-2.2.5`). Esta US
implementa el contador de login y los campos nuevos de `Usuario` que ambos contadores
comparten (`bloqueada`); es la base de la que depende el resto de la Iteración 2.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Usuario` | Gana los atributos `bloqueada`, `intentos_fallidos_login`, `intentos_fallidos_password` |
| Domain Event | `CuentaBloqueada` | Se emite al llegar al 3er fallo consecutivo (cualquiera de los dos contadores) |
| Domain Error | `CuentaBloqueadaError` | `IniciarSesion` la lanza si `Usuario.bloqueada = true`, antes de verificar la contraseña |

---

## Especificacion del comportamiento

### Precondicion

- `Usuario` existe (por email).

### Postcondicion

- Login exitoso (contraseña verifica) → `intentos_fallidos_login = 0`.
- Login fallido (contraseña no verifica) y `intentos_fallidos_login < 2` antes del intento →
  `intentos_fallidos_login += 1`, se sigue lanzando `CredencialesInvalidas` (sin filtrar si la
  cuenta existe, mismo criterio de `US-1.1.4`).
- Login fallido que lleva el contador a 3 → `intentos_fallidos_login = 3`, `bloqueada = true`,
  se emite `CuentaBloqueada`, se lanza `CredencialesInvalidas` (mismo error visible para el
  usuario — no se distingue "credenciales inválidas" de "acabás de bloquear tu cuenta" en esta
  respuesta, ver criterio de aceptación de rechazo por cuenta bloqueada más abajo).
- Intento de login sobre una cuenta ya `bloqueada = true` → se lanza `CuentaBloqueadaError` sin
  verificar la contraseña (no consume intentos adicionales, no tiene sentido seguir contando).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-10 | Un acierto resetea a 0 el contador de su propio flujo (login o cambio de contraseña); al 3er fallo consecutivo en cualquiera de los dos, `bloqueada = true`. |

---

## Criterios de aceptacion

```gherkin
Feature: Bloqueo automático por intentos fallidos de login (US-2.2.1)

  Scenario: Fallo que no llega al límite
    Given un Usuario con intentos_fallidos_login = 1
    When falla un intento de IniciarSesion
    Then intentos_fallidos_login pasa a 2
    And el sistema rechaza con CredencialesInvalidas
    And bloqueada sigue en false

  Scenario: Tercer fallo consecutivo bloquea la cuenta
    Given un Usuario con intentos_fallidos_login = 2
    When falla un intento de IniciarSesion
    Then intentos_fallidos_login pasa a 3
    And bloqueada pasa a true
    And se emite el evento CuentaBloqueada
    And el sistema rechaza con CredencialesInvalidas

  Scenario: Acierto resetea el contador
    Given un Usuario con intentos_fallidos_login = 2
    When IniciarSesion se ejecuta con credenciales correctas
    Then intentos_fallidos_login vuelve a 0

  Scenario: Intento sobre cuenta ya bloqueada
    Given un Usuario con bloqueada = true
    When se ejecuta IniciarSesion con cualquier contraseña
    Then el sistema rechaza con CuentaBloqueadaError sin verificar la contraseña
    And intentos_fallidos_login no cambia
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente, extiende un use case ya en producción.

**Capa(s) afectadas:**
- [x] Entities — `Usuario` gana `bloqueada: bool`, `intentos_fallidos_login: int`,
  `intentos_fallidos_password: int` (con default `False`/`0`/`0`); nuevo evento
  `CuentaBloqueada`, nuevo error `CuentaBloqueadaError`
- [x] Use Cases — `IniciarSesionUseCase` incorpora la lógica de conteo y bloqueo
- [x] Interface Adapters — controller de login traduce `CuentaBloqueadaError` a 403
- [x] Frameworks — migración Alembic agrega las 3 columnas a `usuario` (backfill:
  `bloqueada = false`, contadores en `0` para filas existentes)
- [ ] Frontend — cubierto por `US-2.2.9`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro, sin pantalla propia) — la variante de login con cuenta
bloqueada se especifica en `US-2.2.9`
(`docs/design/ux/wireframes-cuentas-administracion.md` §2.8).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | Agregar `bloqueada`, `intentos_fallidos_login`, `intentos_fallidos_password` |
| `src/identidad/entities/eventos.py` | Agregar `CuentaBloqueada` |
| `src/identidad/entities/errors.py` | Agregar `CuentaBloqueadaError` |
| `src/identidad/use_cases/iniciar_sesion.py` | Verificar `bloqueada` antes de la contraseña; contar fallos/aciertos; emitir `CuentaBloqueada` al llegar a 3 |
| `src/identidad/interface_adapters/gateways/usuario_repository.py` | Persistir los 3 campos nuevos |
| `src/identidad/frameworks/db/models.py` | Columnas nuevas en el modelo SQLAlchemy de `usuario` |
| Migración Alembic nueva | Agrega `bloqueada`, `intentos_fallidos_login`, `intentos_fallidos_password` con backfill |
| `src/identidad/interface_adapters/controllers/auth_controller.py` | Traduce `CuentaBloqueadaError` a `403` |

---

## Referencias

- Relacionada con: `US-2.2.5` (contador independiente sobre el mismo campo `bloqueada`),
  `US-2.2.4` (única forma de desbloquear), `US-2.2.9` (frontend del login bloqueado)
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` §3 "Bloqueo automático por
  intentos fallidos", §11 (INV-ID-10)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Backend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
