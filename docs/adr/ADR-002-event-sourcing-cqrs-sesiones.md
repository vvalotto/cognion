# ADR-002 — Event Sourcing + CQRS en BC Sesiones (vs. CRUD estándar)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El BC Sesiones es el Core Domain del sistema. Tiene requerimientos de observabilidad
(reconstruir qué pasó en una sesión), confiabilidad (persistencia atómica de respuestas) y
ciclo de vida complejo (dos modos con transiciones de estado). El RNF de Observabilidad ya
define event sourcing como decisión tomada.

## Opciones Consideradas

- **CRUD estándar** con logging adicional para lograr trazabilidad. Descartada: el logging
  adicional duplica esfuerzo para llegar al mismo nivel de trazabilidad que event sourcing
  entrega naturalmente, y no resuelve por sí solo la reconstrucción de estado ni las
  proyecciones de Analytics.
- **Event Sourcing + CQRS** — los commands modifican el estado mediante eventos inmutables; los
  read models (Analytics) se proyectan desde el event store. Elegida.

## Decisión

Event Sourcing como mecanismo de persistencia en BC Sesiones, combinado con CQRS.

## Justificación

Event sourcing entrega naturalmente el audit trail requerido por Observabilidad, la
trazabilidad de sesiones, y el historial de respuestas. Los read models de Analytics son una
consecuencia directa del mismo stream de eventos, sin duplicar lógica de persistencia.

## Impacto en Configuración

- Tabla append-only `events` (JSONB) en PostgreSQL — migraciones Alembic del BC Sesiones.
- `src/sesiones/entities/` — el aggregate se reconstruye por replay de eventos, no por lectura
  directa de un modelo relacional mutable.
- `src/analytics/` — sus read models leen del event store de Sesiones vía puerto, nunca por
  import directo entre BCs.

## Consecuencias

- ✅ Trazabilidad completa de cualquier sesión sin logging adicional
- ✅ Read models generados desde el mismo stream de eventos
- ✅ Reconstrucción del estado del aggregate desde eventos (event replay)
- ⚠️ Mayor complejidad conceptual que CRUD
- ⚠️ Consultas ad-hoc sobre el estado actual requieren proyecciones
