# US-ADJ-06: Mostrar el nombre real del usuario autenticado en el header de aplicación

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ-01` (misma iteración de ajuste que `US-ADJ-01`/`03`/`04`/`05`)
**Tipo**: `feature backend + frontend`
**Agregado principal afectado**: `Usuario` (sin cambios de invariantes — expone un atributo ya
existente en un lugar nuevo: el JWT)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **cualquier Usuario autenticado**,
quiero **ver mi nombre real en el header de la aplicación (no solo mi rol)**
para **confirmar de un vistazo con qué cuenta estoy trabajando, igual que en el prototipo
aprobado**.

---

## Contexto del dominio

### Problema

Detectado en UAT/UX en vivo (2026-08-23) revisando `Cuentas.tsx`: `AppLayout.tsx` renderiza
`session.rol` en el header ("administrador"), no el nombre. El prototipo
(`identidad-cuentas-administracion.html`, bloque `.who`) muestra "Víctor Valotto ·
Administrador".

Causa raíz: el JWT emitido por `POST /identidad/login` (`ADR-013`) solo incluye `sub` (id) y
`rol` en el payload — el `nombre` de `Usuario` nunca se propaga a la sesión del frontend
(`session.ts` solo persiste `{ token, rol }`, ver `US-1.1.6`).

### Modelo involucrado

Sin cambios de invariantes ni de comportamiento de dominio — `Usuario.nombre` ya existe. El
cambio es de exposición: agregar `nombre` al claim del JWT (o a la respuesta de
`POST /identidad/login`, evaluar cuál evita relogin al invalidar tokens ya emitidos).

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Extendido | JWT (`ADR-013`) o `LoginResponse` | Propagar `Usuario.nombre` a la sesión del frontend |
| Extendido | `session.ts` (frontend) | Persistir `nombre` junto a `rol`/`token` |

---

## Impacto arquitectonico

- Backend: `src/identidad/frameworks/security/jwt_*.py` (o el schema de `LoginResponse` en
  `frameworks/api/schemas.py`), `interface_adapters/controllers/identidad_controller.py`.
- Frontend: `frontend/src/lib/session.ts`, `frontend/src/layouts/AppLayout.tsx` (header:
  avatar con iniciales del nombre + "{nombre} · {rol}").

**Nota para la spec formal:** decidir si agregar `nombre` al payload del JWT (impacto: todo
JWT ya emitido queda con el payload viejo hasta expirar/relogin, `ADR-013` sin refresh) o
devolverlo aparte en `LoginResponse` y guardarlo solo en `localStorage` (no en el JWT firmado)
— más simple, sin tocar la emisión/verificación del token.

---

## Fuente de verdad UX

`docs/design/ux/prototipos/identidad-cuentas-administracion.html` (bloque `.who` del
`app-header`, presente en las 7 pantallas del prototipo).

---

## Referencias

- Relacionada con: `US-1.1.6` (login, emite el JWT actual), `ADR-013` (JWT 60min sin refresh)
- Candidatas: sin incremento asignado — hallazgo de UAT/UX en vivo 2026-08-23, no implementada
  (toca `src/`, requiere track formal según `CLAUDE.md` §"Clasificación de hallazgos en UAT")

---

*Basado en el template de `docs/specs/ajustes/US-ADJ-01.md`. US de ajuste (`SP-ADJ-01`,
`docs/plans/PLAN-CM.md` §12) — sin Issue de GitHub ni branch hasta que se decida el incremento
de implementación.*
