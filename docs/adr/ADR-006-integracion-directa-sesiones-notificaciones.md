# ADR-006 — Integración directa entre BC Sesiones y BC Notificaciones (vs. evento en memoria)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

Cuando se abre o cierra una sesión de período abierto, el BC Notificaciones debe enviar un
email al alumno. Se necesita definir cómo el BC Sesiones desencadena esa acción sin violar los
límites de BC.

## Opciones Consideradas

- **Evento en memoria (observer / mediator)** — desacoplaría los BCs correctamente. Descartada
  por ahora: agrega un mecanismo de infraestructura adicional a mantener, que no se justifica
  para un único desarrollador con solo dos integraciones concretas (apertura y cierre de
  sesión).
- **Integración directa** — el Use Case de Sesiones llama directamente al Use Case de
  Notificaciones. Elegida, como deuda técnica consciente.

## Decisión

El Use Case de Sesiones llama directamente al Use Case de Notificaciones al completar la
operación que desencadena la notificación.

## Justificación

Para un sistema con un único desarrollador y dos integraciones concretas, el overhead de un
event bus en memoria no se justifica en esta etapa. Se acepta el acoplamiento resultante como
deuda técnica documentada, no como omisión.

## Impacto en Configuración

No aplica — decisión de integración entre Use Cases, sin artefacto de configuración asociado.

## Consecuencias

- ✅ Implementación simple y directa
- ✅ Sin infraestructura adicional de mensajería
- ⚠️ Acoplamiento entre BC Sesiones y BC Notificaciones — cambios en la interfaz de
  Notificaciones impactan en Sesiones
- ⚠️ Deuda técnica consciente: si Notificaciones crece (más canales, más eventos), conviene
  migrar a evento en memoria — revisar en el Incremento 4 (docs/rf/PLAN_v1.md)
