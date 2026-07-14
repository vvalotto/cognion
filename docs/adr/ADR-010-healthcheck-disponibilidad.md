# ADR-010 — Healthcheck endpoint público (vs. depender solo del monitoreo del proveedor)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El escenario de calidad de Disponibilidad en `RNF_v1.md` exige que el docente pueda verificar
el estado del sistema sin depender de reportes de alumnos, especialmente durante una sesión en
vivo. El escenario de Observabilidad exige, además, poder diagnosticar el sistema de forma
proactiva.

## Opciones Consideradas

- **Depender solo del monitoreo propio del proveedor de hosting (Fly.io)** — descartada: no
  permite verificación directa por el docente, ni una señal reutilizable para reinicio
  automático del proveedor.
- **Healthcheck endpoint público expuesto por la Backend API** — elegida.

## Decisión

Exponer un endpoint `GET /health` público (sin autenticación) que reporta el estado de la
aplicación y de su conexión a PostgreSQL.

## Justificación

Es el mecanismo mínimo y estándar para que tanto el proveedor de hosting (Fly.io, para
reinicios automáticos ante fallas) como el docente (para diagnóstico manual antes o durante una
sesión) puedan verificar disponibilidad sin depender de reportes indirectos de alumnos.

## Impacto en Configuración

- Router raíz de FastAPI — endpoint `GET /health`, sin dependencia de autenticación.
- `fly.toml` — configuración de healthcheck del proveedor apuntando a ese endpoint.

## Consecuencias

- ✅ Verificación de estado sin autenticación ni dependencia de reportes de terceros
- ✅ Integrable con el mecanismo de reinicio automático de Fly.io
- ⚠️ Expone públicamente el estado de conexión a la base de datos — aceptable, no revela datos
  sensibles
