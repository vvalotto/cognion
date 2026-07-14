# ADR-005 — WebSockets para sesiones en vivo (vs. polling o SSE)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

Las sesiones en vivo requieren sincronización bidireccional: el docente envía comandos (cerrar
pregunta, avanzar) y el servidor hace broadcast del ranking a todos los clientes. El tiempo de
procesamiento server-side debe ser ≤100ms (escenario de Rendimiento en RNF_v1).

## Opciones Consideradas

- **Polling** — el cliente consulta el servidor a intervalos. Descartada: agrega latencia
  variable (depende del intervalo) y carga innecesaria al servidor con hasta 60 clientes.
- **SSE (Server-Sent Events)** — unidireccional (servidor → cliente). Descartada: no permite que
  el alumno envíe respuestas ni que el docente cierre preguntas por el mismo canal; requeriría
  un canal adicional para el sentido inverso.
- **WebSockets** — conexión TCP persistente y bidireccional. Elegida.

## Decisión

WebSockets para toda la comunicación durante sesiones en vivo.

## Justificación

WebSockets mantiene una conexión persistente y bidireccional: el docente envía el comando de
cierre, el servidor calcula el ranking y hace push a los 60 clientes conectados, todo en el
mismo ciclo async de FastAPI, sin round-trips adicionales ni canales separados por dirección.

## Impacto en Configuración

- `src/sesiones/frameworks/` — endpoints WebSocket de FastAPI, sin dependencias externas de
  mensajería (no requiere Redis pub/sub para esta escala).
- Infraestructura de despliegue (Fly.io) debe permitir conexiones WebSocket persistentes por la
  duración de una sesión en vivo — verificar configuración de proxy/timeout.

## Consecuencias

- ✅ Comunicación bidireccional sin overhead de polling
- ✅ Latencia predecible (no hay round-trips adicionales)
- ✅ Soportado nativamente por FastAPI sin dependencias adicionales
- ⚠️ Las conexiones WebSocket persisten durante toda la sesión (recurso TCP por cliente —
  aceptable a 60 conexiones)
