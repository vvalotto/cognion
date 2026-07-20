# US-1.1.5: El sistema restringe el acceso a funcionalidades según el rol del usuario autenticado

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: — (guard transversal, sin aggregate propio)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Sistema**,
quiero **verificar el rol del `Usuario` autenticado en cada request a un recurso protegido**
para **que un Estudiante no pueda acceder a la gestión del banco de preguntas ni a analytics
globales, y un Docente no pueda acceder a las herramientas de administración de cuentas
(RF-02)**.

---

## Contexto del dominio

### Problema

`US-1.1.4` emite el JWT con el claim `rol`, pero sin esta US ningún endpoint valida ese claim
contra el recurso solicitado — cualquier `Usuario` autenticado podría invocar cualquier
endpoint. Esta US agrega el mecanismo de autorización (RBAC) que hace cumplir RF-02.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Value Object | `Rol` | Ya existe (`US-1.1.4`) — se consume acá, no se redefine |
| Query/Guard | `VerificarAcceso(jwt, recurso)` | Sin evento de dominio — es una dependency de FastAPI (`get_current_user` + verificación de rol) |
| Port | `JWTIssuerPort` | Ya existe (`US-1.1.4`) — se reutiliza para validar/decodificar el JWT recibido |

---

## Especificacion del comportamiento

### Precondicion

- El request incluye un JWT en el header `Authorization`.

### Postcondicion

- JWT ausente, inválido o expirado → `401 Unauthorized`.
- JWT válido pero `rol` insuficiente para el recurso solicitado → `403 Forbidden`.
- JWT válido y `rol` suficiente → la request continúa al handler correspondiente.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Un `Usuario` con rol `estudiante` nunca accede a endpoints de gestión del banco de preguntas ni de analytics globales (RF-02). |
| — | Un `Usuario` con rol `docente` nunca accede a endpoints de administración de cuentas (RF-02) — incluye los endpoints de `US-1.1.0` (`CrearUsuario`, `CrearComision`, `AsignarDocenteAComision`). |
| — | La verificación de rol es la misma para todos los recursos protegidos — no hay excepciones por endpoint fuera de la matriz rol→recurso declarada en el router. |

---

## Criterios de aceptacion

```gherkin
Feature: Autorización por rol (RBAC)

  Scenario: Acceso concedido con rol suficiente
    Given un JWT válido con rol="administrador"
    When se solicita un endpoint de administración de cuentas
    Then el sistema concede el acceso y ejecuta el handler

  Scenario: Estudiante rechazado en gestión del banco de preguntas
    Given un JWT válido con rol="estudiante"
    When se solicita un endpoint de gestión del banco de preguntas
    Then el sistema responde 403 Forbidden

  Scenario: Estudiante rechazado en analytics globales
    Given un JWT válido con rol="estudiante"
    When se solicita un endpoint de analytics globales
    Then el sistema responde 403 Forbidden

  Scenario: Docente rechazado en administración de cuentas
    Given un JWT válido con rol="docente"
    When se solicita un endpoint de administración de cuentas (US-1.1.0)
    Then el sistema responde 403 Forbidden

  Scenario: Request sin JWT
    Given un request a un recurso protegido sin header Authorization
    When se procesa el request
    Then el sistema responde 401 Unauthorized

  Scenario: JWT expirado
    Given un JWT cuyo exp ya pasó (más de 60 minutos desde la emisión, ADR-013)
    When se solicita cualquier recurso protegido
    Then el sistema responde 401 Unauthorized
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — decisión ya tomada en `ADR-007` (JWT+RBAC)

**Capa(s) afectadas:**
- [x] Interface Adapters — dependency de autorización, decorador/mapa rol→recurso
- [x] Frameworks — dependency FastAPI `get_current_user` + `require_rol(...)`, aplicado a los
  routers existentes (`usuarios_router.py`, `comisiones_router.py` de `US-1.1.0`)
- [ ] Frontend — sin pantalla propia; el frontend oculta/muestra navegación según el rol
  decodificado del JWT, pero eso no es objeto de esta US (no hay wireframe de navegación
  condicional aprobado todavía)

---

## Fuente de verdad UX

No aplica — esta US no agrega ni modifica pantallas. La restricción de acceso es a nivel de
API (403); el comportamiento de la UI ante un 403 recibido queda fuera de alcance hasta que
exista una pantalla protegida real que lo requiera (banco de preguntas, analytics — incrementos
posteriores).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/interface_adapters/security/get_current_user.py` | Dependency que decodifica y valida el JWT, resuelve el `Usuario`/rol actual |
| `src/identidad/interface_adapters/security/require_rol.py` | Dependency/decorador que verifica `rol` contra una lista de roles permitidos |
| `src/identidad/frameworks/api/usuarios_router.py`, `comisiones_router.py` | Aplicar `require_rol(["administrador"])` a los endpoints de `US-1.1.0` |
| `src/identidad/frameworks/api/invitaciones_router.py` | Aplicar `require_rol(["docente"])` (`US-1.1.1`) |

---

## Referencias

- Relacionada con: `US-1.1.0`, `US-1.1.1`, `US-1.1.4`, `ADR-007`
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` (§4, VO `Rol`)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md`

---

## Notas de implementacion

> Esta US se implementa en paralelo/después de tener al menos un endpoint protegido de cada
> tipo (`US-1.1.0`, `US-1.1.1`) para poder verificar los criterios de aceptación con casos
> reales — no depende de que existan endpoints de banco de preguntas o analytics (fuera de
> alcance del Incremento 1), la matriz rol→recurso se valida contra los endpoints de Identidad
> disponibles en este incremento.

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
