# US-1.1.6: Infraestructura de frontend — routing, cliente API y manejo de sesión

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.2`
**Tipo**: `feat frontend (infraestructura)`
**Agregado principal afectado**: — (sin lógica de dominio, es infraestructura transversal)
**Bounded Context**: Identidad (soporte técnico, reutilizable por otros BC más adelante)

---

## Descripcion (lenguaje de negocio)

Como **Desarrollador**,
quiero **routing y un cliente API con manejo de sesión (JWT) en `frontend/`**
para **que las pantallas de Identidad (US-1.1.7 a US-1.1.9) tengan la infraestructura mínima
sobre la que construirse**.

---

## Contexto del dominio

### Problema

`frontend/src` sigue siendo el scaffold default de Vite + Tailwind + shadcn/ui (`App.tsx`,
`main.tsx`, un componente `Button` de ejemplo) — sin React Router, sin cliente HTTP, sin
manejo de sesión. Cinco US de backend (`US-1.1.2` a `US-1.1.5`) diferieron su frontend por
esta razón. Esta US resuelve la infraestructura de una vez para desbloquear a las tres
siguientes.

### Modelo involucrado

No aplica — esta US no tiene Aggregate ni comportamiento de dominio propio. Es soporte técnico
transversal: routing, cliente API, y el layout base (auth vs. aplicación) que consumen las
pantallas de negocio.

---

## Especificacion del comportamiento

### Precondicion

- `frontend/src` sin routing ni cliente API (estado actual, scaffold default).
- Backend de Identidad disponible en `http://localhost:8000` (o la URL configurada) con los
  endpoints de `US-1.1.0` a `US-1.1.5` ya implementados.

### Postcondicion

- Routing configurado con al menos las rutas de login (`/login`) y registro
  (`/registro?token=...`), placeholder hasta que `US-1.1.7`/`US-1.1.8` las completen.
- Cliente API (wrapper sobre `fetch`) con base URL configurable vía variable de entorno,
  serialización/deserialización JSON, y manejo uniforme de errores HTTP.
- El cliente adjunta el JWT guardado (si existe) en el header `Authorization: Bearer` de cada
  request.
- Una respuesta `401` del backend limpia la sesión guardada y redirige a `/login`.
- Una respuesta `403` del backend muestra feedback de acceso denegado sin filtrar detalle del
  recurso solicitado (mismo criterio de no-filtración que ya aplica en backend, `US-1.1.5`).
- Dos layouts disponibles: layout de auth (tarjeta centrada, ancho máx. 420px,
  `wireframes-identidad.md` §3) y layout de aplicación (header con marca + usuario
  autenticado, para las pantallas post-login como `US-1.1.9`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El JWT nunca se adjunta a un request si no hay sesión guardada — evita mandar `Authorization: Bearer null`/`undefined`. |
| — | El cliente API es el único punto del frontend que conoce la URL base del backend — ninguna pantalla arma URLs a mano. |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de frontend (US-1.1.6)

  Scenario: El cliente adjunta el JWT en un request a un endpoint protegido
    Given una sesión con un JWT guardado
    When el cliente API ejecuta un request a un endpoint protegido
    Then el request incluye el header "Authorization: Bearer <token>"

  Scenario: Un 401 del backend limpia la sesión y redirige a login
    Given una sesión con un JWT guardado (vencido o inválido)
    When el backend responde 401 a cualquier request
    Then el cliente limpia el JWT guardado
    And el router navega a "/login"

  Scenario: Un 403 del backend muestra acceso denegado sin filtrar el recurso
    Given una sesión con un JWT válido pero rol insuficiente
    When el backend responde 403 a un request
    Then la UI muestra un mensaje genérico de acceso denegado
    And el mensaje no revela qué recurso se intentó acceder
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí — pendiente: mecanismo de almacenamiento del JWT en el cliente (`localStorage` vs.
  memoria vs. cookie `httpOnly`). Se resuelve en Fase 2 (plan de implementación) de
  `/implement-us`, documentando el trade-off elegido — no bloquea la especificación porque no
  cambia el contrato observable de esta US (login guarda sesión, 401 la limpia).

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/lib/api-client.ts` (nuevo), `frontend/src/router.tsx` (nuevo),
  `frontend/src/layouts/` (nuevo)
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad.md` §3 (Responsive — dimensiones y comportamiento de los
dos layouts). Sin pantallas propias — el resto del wireframe (§2) lo consumen `US-1.1.7` a
`US-1.1.9`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/api-client.ts` | Cliente HTTP: base URL, manejo de JSON, adjunta JWT, maneja 401/403 |
| `frontend/src/lib/session.ts` | Guardar/leer/limpiar el JWT y el rol decodificado |
| `frontend/src/router.tsx` | Configuración de React Router — rutas placeholder de login/registro |
| `frontend/src/layouts/AuthLayout.tsx` | Layout de tarjeta centrada para pantallas de auth |
| `frontend/src/layouts/AppLayout.tsx` | Layout con header de aplicación para pantallas post-login |
| `frontend/package.json` | Agregar `react-router` como dependencia |

---

## Referencias

- Relacionada con: `US-1.1.7`, `US-1.1.8`, `US-1.1.9` (bloqueadas por esta US)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md` §Iteración 2
- Issue: #23

---

## Notas de implementacion

> Sin tests BDD de dominio (no hay comportamiento de negocio) — Fase 1 de `/implement-us`
> puede reducirse a los tres escenarios técnicos de arriba (JWT adjuntado, 401 limpia sesión,
> 403 sin filtrar). Tests de integración con un backend real (o mockeado) para validar el
> manejo de 401/403 end-to-end.

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
