# US-1.1.7: Docente/Administrador/Estudiante inicia sesión desde la UI

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `POST /identidad/login`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Docente, Administrador o Estudiante** con una cuenta ya creada,
quiero **autenticarme desde una pantalla de login**
para **recibir un JWT con mi rol y poder operar el resto del sistema según los permisos que
me corresponden (RF-02)**.

---

## Contexto del dominio

### Problema

`POST /identidad/login` está implementado y probado desde `US-1.1.4`, pero no hay ninguna
pantalla que lo consuma — el único cliente hasta ahora es `pytest`/`curl`. Sin esta US, ningún
actor puede autenticarse desde la aplicación real.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /identidad/login` | Ya existe (`US-1.1.4`) — recibe `email`/`password`, devuelve `access_token`/`rol`/`expira_en` o 401 |
| Cliente API | `api-client.ts` | Ya existe (`US-1.1.6`) — ejecuta el request y guarda la sesión si la respuesta es 200 |

---

## Especificacion del comportamiento

### Precondicion

- `US-1.1.6` implementada (routing + cliente API disponibles).
- El actor tiene una cuenta existente (creada por `US-1.1.0` para Docente/Administrador, o por
  `US-1.1.2`/`US-1.1.8` para Estudiante).

### Postcondicion

- Credenciales válidas → `POST /identidad/login` devuelve 200, el cliente guarda el JWT y el
  rol, y la UI redirige a la vista correspondiente al rol (placeholder hasta que existan
  pantallas post-login propias de cada rol — para `administrador` redirige a `/docentes/nuevo`,
  cubierta por `US-1.1.9`; para `docente`/`estudiante`, placeholder simple hasta incrementos
  futuros).
- Credenciales inválidas (401, `CredencialesInvalidas`) → se muestra `LoginError.tsx` con un
  mensaje genérico, sin distinguir si el email existe.

### Invariantes

| ID | Invariante |
|----|------------|
| — | El mensaje de error no distingue entre email inexistente y contraseña incorrecta (mismo criterio que el backend, `US-1.1.4`, `CredencialesInvalidas`). |
| — | El JWT no se guarda hasta que el backend confirme 200 — un intento fallido no deja sesión parcial. |

---

## Criterios de aceptacion

```gherkin
Feature: Login desde la UI (US-1.1.7)

  Scenario: Login exitoso
    Given un Usuario con cuenta existente y contraseña "Docente#2026"
    When completa el formulario de login con su email y esa contraseña
    Then el sistema guarda el JWT recibido
    And redirige a la vista correspondiente a su rol

  Scenario: Login rechazado por credenciales inválidas
    Given un Usuario con cuenta existente
    When completa el formulario de login con una contraseña incorrecta
    Then el sistema muestra la pantalla de error de login
    And el mensaje no distingue si el email existe

  Scenario: Login rechazado por email inexistente
    Given ningún Usuario registrado con el email ingresado
    When completa el formulario de login
    Then el sistema muestra la misma pantalla de error que ante contraseña incorrecta
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado (`ADR-007`, `ADR-013`), sin decisiones nuevas.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/Login.tsx`, `frontend/src/pages/LoginError.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad.md` §2.1 (`#login`), §2.2 (`#login-error`), §3
(responsive, layout de auth). Prototipo navegable: `docs/design/ux/prototipos/`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/Login.tsx` | Pantalla de login — campos email/password, acción "Iniciar sesión" |
| `frontend/src/pages/LoginError.tsx` | Pantalla de error — mensaje genérico |
| `frontend/src/router.tsx` | Reemplazar el placeholder de `/login` por las pantallas reales |

---

## Referencias

- Relacionada con: `US-1.1.4` (backend), `US-1.1.6` (infraestructura, precondición)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md` §Iteración 2
- Issue: #24

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
