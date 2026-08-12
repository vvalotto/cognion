# ADR-013 — Expiración de JWT sin refresh token (resuelve advertencia abierta de ADR-007)

**Estado:** Aceptado
**Fecha:** 2026-07-16

---

## Contexto

ADR-007 adoptó JWT stateless pero dejó como advertencia abierta (⚠️) que la revocación de
tokens requiere expiración corta + refresh, sin definir el mecanismo. Esta decisión se toma
antes de la Iteración 0 del Incremento 1 (BC Identidad), porque `JWT_EXPIRATION_MINUTES` es
una variable de configuración que ese incremento debe fijar.

## Opciones Consideradas

- **Access + refresh token** (access corto, refresh de vida larga validado contra una tabla en
  base) — descartada: requiere almacenamiento server-side de refresh tokens, lo que contradice
  la razón original de ADR-007 (JWT stateless sin sesión ni almacenamiento server-side) y no
  está justificado por el escenario de Seguridad de `RNF_v1.md`, que explícitamente no exige
  mecanismos adicionales de ocultamiento.
- **Access token corto, sin refresh** (re-login al expirar) — elegida.

## Decisión

El access token JWT expira a los 60 minutos. No hay refresh token ni blacklist en v1: al
expirar, el usuario vuelve a autenticarse.

## Justificación

60 minutos cubre una clase típica de FIUNER sin forzar re-login a mitad de una sesión de
período abierto o en vivo, manteniendo el diseño 100% stateless de ADR-007. Un refresh token
agregaría estado server-side que el driver de equipo unipersonal (ADR-001) y el escenario de
Seguridad de `RNF_v1.md` no justifican.

## Impacto en Configuración

- `.env.example` — `JWT_EXPIRATION_MINUTES=60`.
- `src/identidad/frameworks/` — configuración de expiración del token al firmarlo.

## Consecuencias

- ✅ Mantiene el diseño 100% stateless de ADR-007 — sin tabla de refresh tokens ni blacklist.
- ⚠️ El usuario debe re-loguearse cada 60 minutos — revisar si el Incremento 6 (sesión en
  vivo) tiene escenarios que superen esa ventana antes de implementarlo.
