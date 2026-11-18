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

## Enmienda 2026-11-18 (`US-12.1.3`, hallazgo `AQ-04`)

La advertencia de arriba se cumplió: una clase supera los 60 minutos. Se probó en el navegador con un vencimiento corto: con la sala de espera de una sesión en vivo abierta, la consulta periódica recibe un `401` al vencer el token y la aplicación manda al docente a `/login` sin aviso, sin que haga nada.

**El vencimiento por defecto pasa a 480 minutos (8 horas, una jornada).** Sigue sin haber refresh ni blacklist; la decisión original de no agregar estado en el servidor se mantiene. Costo aceptado: un token robado vale hasta 8 horas; a la escala del proyecto (un docente, comisiones de 30 a 60 alumnos) el riesgo es bajo.

La variable real es `ACCESS_TOKEN_EXPIRE_MINUTES` (en `.env` y `.env.example`); `JWT_EXPIRATION_MINUTES`, que figura arriba, no existe en el código.

Queda como candidato, para el Incremento 11: renovación automática del token (reemplazaría a este valor fijo) y avisar en `/login` que la sesión venció.
