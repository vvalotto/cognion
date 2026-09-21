# Diseño de Pruebas UAT — Incremento 6 "Sesión en vivo", Iteración 2

| Campo | Valor |
|-------|-------|
| Incremento | 6 |
| Iteración | 2 (RF-09 dinámica en tiempo real, RF-10 puntaje y ranking) |
| US cubiertas | US-6.1.1 a US-6.1.4 (RF-08) y US-6.2.1 a US-6.2.8 (RF-09/10), verificadas por US-6.2.9 |
| Entorno | Propio (máquina de desarrollo, PostgreSQL local). Staging (Fly.io, WSS real) queda pendiente, ver §"Alcance" |
| Fecha diseño | 2026-09-21 |

## Objetivo

Tener evidencia de que una sesión en vivo completa funciona de punta a punta por la API y por
WebSocket, y de que el cierre de pregunta con toda la clase conectada cumple el primer RNF de
rendimiento duro del proyecto (`RNF_v1.md`, Rendimiento, Escenario 1: ≤100 ms server-side). Es el
hito de la Iteración 2: el Docente conduce una sesión en vivo completa con ranking actualizado en
tiempo real, todavía sin pantalla (el frontend del modo en vivo no tiene iteración asignada).

Sin gate de diseño UX que verificar: backend puro (`docs/specs/inc6/US-6.2.9.md`, "Fuente de
verdad UX: No aplica").

## Estrategia

**Capa 1 (pytest) + Capa 2 (HTTP/WebSocket, entorno propio) + revisión manual.**

- **Capa 1:** suite completa (`tests/unit`, `tests/integration`, `tests/step_defs`) sin regresiones,
  más `tests/integration/inc6/test_sesion_en_vivo_completa.py`, que recorre la sesión completa con
  WebSockets reales.
- **Capa 2:** medición reproducible del RNF (`tests/uat/inc6/medir_rendimiento_cierre.py`) contra
  PostgreSQL real.
- **Revisión manual:** `tests/uat/inc6/guion_manual_iteracion2.sh` — un Docente y tres Estudiantes
  conectados por WebSocket, que el ejecutor juzga a ojo (mismo criterio que la Iteración 1 del
  Incremento 3). Sin recorrido de navegador: no hay pantalla que navegar.

## Escenario DoD

Un Docente crea una sesión en vivo para una Comisión, los Estudiantes se unen y se conectan, se
inicia, se recorren varias preguntas (mostrar opciones → responder → cerrar → avanzar) y se
finaliza. Cada paso responde 200, cada broadcast llega a todos los conectados, el ranking final
coincide con la suma de los puntajes y el Estudiante lo ve solo al finalizar.

## Capa 1 — Tests

| ID | Test | Qué verifica |
|----|------|--------------|
| C1-01 | `TestSesionCompletaDePuntaAPunta` | 5 Estudiantes + Docente por WebSocket real; 3 preguntas; broadcast idéntico a los 6 clientes; ranking final = suma de los `puntaje` de cada respuesta; el Estudiante ve el ranking recién al finalizar (403 antes) |
| C1-02 | `TestRespuestasSimultaneas` | 60 Estudiantes responden a la vez: las 60 se registran, el histograma suma exactamente 60 y el ranking refleja los 60 puntajes |
| C1-03 | `TestReconexion` | El Estudiante pierde la conexión con la pregunta abierta, reconecta: recupera pregunta, `opciones_mostradas_en` + límite y su avance; su participación no se pierde y recibe el siguiente broadcast |
| C1-04 | `TestRespuestaTardia` | Con el tiempo límite vencido: `TiempoAgotado` (422), sin evento de respuesta y el ranking queda en 0 |
| C1-05 | Suite completa | Sin regresiones sobre `US-6.1.x` y `US-6.2.1` a `6.2.8` |

## Capa 2 — Medición del RNF

**Qué se mide (criterio):** procesamiento server-side de `CerrarPreguntaActual` con 60 participantes,
desde que el use case empieza hasta que terminó de publicar a las 60 conexiones (persistir el evento,
leer ranking e histograma y la respuesta correcta, armar y enviar el mensaje). No incluye la latencia
de red de los clientes (el RNF la deja fuera).

**Método:** 6 sesiones × 5 preguntas = **30 cierres sobre preguntas distintas**, con los mismos 60
Estudiantes; en cada pregunta las 60 respuestas entran por la API real y recién entonces se mide el
cierre. PostgreSQL real; **60 conexiones simuladas** registradas en el `ConnectionManager` real (mide
el envío de 60 mensajes, no la red). No se descarta ninguna muestra (ni la primera).

**Criterio de aceptación:** `p95 ≤ 100 ms` sobre ≥30 repeticiones. Si `p95 > 100 ms` → hallazgo
bloqueante de la iteración (US-ADJ o decisión con Víctor); no se optimiza dentro de US-6.2.9.

**Medición complementaria (no decide el veredicto):** el mismo cierre por `POST /cerrar-pregunta` vía
ASGI, que suma JWT, wiring de dependencias y la conexión nueva a la base por operación (`NullPool`,
`ADR-017`). Se reporta al lado para no ocultar ese costo real.

## Verificación manual

`tests/uat/inc6/guion_manual_iteracion2.sh`: siembra Administrador, Docente, materia con 10
preguntas, Comisión y 3 Estudiantes (autoregistro); lanza 4 clientes WebSocket (`cliente_ws.py`) y
recorre los 13 pasos con un 🔍 "Revisar" por cada cosa a juzgar. Incluye la reconexión de un
Estudiante, avanzar sin cerrar, finalizar antes de agotar el set y los rechazos por rol. Deja el
backend corriendo y los datos sembrados; se limpia con `tests/uat/inc6/limpiar_uat.sh <prefijo>`.
Los hallazgos van en `quality/reports/uat/inc6/hallazgos-revision-manual.md`, con la severidad de
`docs/plans/PROCEDIMIENTO-UAT.md` §8.

## Alcance y honestidad del método

- Máquina de desarrollo local, no producción: los números son una **cota de referencia**, no una
  garantía del despliegue final (la infraestructura definitiva sigue pendiente, `CLAUDE.md`).
- **Checkpoint de staging pendiente:** `PROCEDIMIENTO-UAT.md` §4 prevé validar este RNF en Fly.io con
  WSS real detrás de un proxy y PostgreSQL administrado. Esta UAT no lo reemplaza: la mide en el
  entorno propio, como fija la spec de US-6.2.9.
- Las 60 conexiones son simuladas en memoria: no ejercitan keepalive/timeouts de un balanceador ni
  la escritura real a 60 sockets TCP.
- RF-08/09/10 pasaron a **Implementado** en `docs/traceability/matrix.md` tras la validación
  manual del guion por Víctor (2026-09-21).
