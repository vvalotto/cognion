# ADR-007 — JWT + RBAC para autenticación y autorización (vs. sesiones server-side u OAuth2 delegado)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El sistema distingue tres roles fijos (administrador, docente, estudiante — RF-02). El
escenario de calidad de Seguridad en `RNF_v1.md` exige control de acceso suficiente para el
contexto académico, sin mecanismos adicionales de ocultamiento. El equipo es unipersonal y no
existe todavía una integración con un proveedor de identidad institucional.

## Opciones Consideradas

- **Sesiones server-side (cookies + almacenamiento de sesión)** — descartada: requiere estado
  adicional en el servidor (session store) que fricciona con el driver 4 (equipo unipersonal,
  deployment sin fricción) y con el estilo async stateless de FastAPI.
- **OAuth2 delegado a un proveedor externo** (Google, institucional FIUNER) — descartada: no
  existe todavía una integración institucional definida, y añade una dependencia externa no
  justificada para tres roles fijos en v1.
- **JWT + RBAC propio** — autenticación stateless, autorización por rol validada en cada
  endpoint. Elegida.

## Decisión

Autenticación stateless con JWT; autorización por RBAC de tres roles, validado en cada endpoint
del servidor vía dependency injection de FastAPI.

## Justificación

JWT es stateless — no requiere sesión ni almacenamiento server-side — y encaja naturalmente con
la arquitectura async de FastAPI. Un RBAC simple de tres roles es suficiente para el escenario
de Seguridad de `RNF_v1.md`, que explícitamente no exige mecanismos adicionales de ocultamiento
para el contexto académico.

## Impacto en Configuración

- `pyproject.toml` — dependencias `PyJWT` + `cryptography`.
- `.env.example` — variables `JWT_SECRET_KEY`, `JWT_EXPIRATION_MINUTES`.
- `src/identidad/interface_adapters/` — dependency de FastAPI que valida el token y el rol
  requerido por endpoint.

## Consecuencias

- ✅ Stateless — sin sesión server-side que mantener
- ✅ Validación de rol uniforme vía dependency injection en cada endpoint
- ⚠️ Revocación de tokens requiere expiración corta + refresh — no hay blacklist de tokens en v1
- ⚠️ Sin SSO institucional en v1 — cada usuario tiene credenciales propias del sistema
