# Evidencia UAT — Incremento 6 "Sesión en vivo", Iteración 2

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc6/design-iteracion2.md` |
| Fecha ejecución | 2026-09-21 |
| Ejecutor | Sesión de Claude Code (Capa 1 + Capa 2). Revisión manual de Víctor: ✅ validada (2026-09-21) |

---

## 1. Capa 1 — pytest (backend)

Corrido sobre la branch de `US-6.2.9`, partiendo de `develop` con `US-6.2.8` mergeada (`68171e6`).

```
.venv/bin/python -m pytest tests/unit tests/integration tests/step_defs --cov=src
1590 passed, 105 warnings in 570.19s (0:09:30)
TOTAL 4539 statements, 149 missed, 97%   (src/actividad_evaluativa: 1873/1873, 100%)
```

Sin fallos y sin regresiones sobre `US-6.1.x` y `US-6.2.1` a `US-6.2.8` (1586 → 1590: los 4 tests
nuevos). El flake preexistente de `US-3.2.1` no apareció.

| ID | Test | Resultado |
|----|------|-----------|
| C1-01 | `TestSesionCompletaDePuntaAPunta` (5 Estudiantes + Docente por WebSocket real, 3 preguntas, ranking final = suma de puntajes, ranking del Estudiante 403 antes de finalizar) | ✅ |
| C1-02 | `TestRespuestasSimultaneas` (60 respuestas a la vez, histograma = 60, ranking con los 60) | ✅ |
| C1-03 | `TestReconexion` (recupera pregunta, tiempo y avance; participación intacta; recibe el siguiente broadcast) | ✅ |
| C1-04 | `TestRespuestaTardia` (`TiempoAgotado` 422, ranking sin cambios, sin evento de respuesta) | ✅ |
| C1-05 | Suite completa sin regresiones | ✅ |

---

## 2. Capa 2 — Medición del RNF de rendimiento

```
PYTHONPATH=. .venv/bin/python tests/uat/inc6/medir_rendimiento_cierre.py
```

Evidencia cruda: `quality/reports/uat/inc6/rendimiento-cierre.json`. Entorno: macOS 15.8 x86_64,
Python 3.12.0, PostgreSQL local (`NullPool`), 60 participantes, 60 conexiones simuladas en el
`ConnectionManager` real. 6 sesiones × 5 preguntas = 30 cierres, sin descartar ninguna muestra.
Los 60 clientes recibieron cada uno de los 30 cierres (verificado).

| Medición | n | Mediana | **p95** | Máximo | Mínimo | Desvío |
|----------|---|---------|---------|--------|--------|--------|
| **Use case `CerrarPreguntaActual` (criterio)** | 30 | 32,06 ms | **43,81 ms** | 50,25 ms | 26,24 ms | 5,38 ms |
| `POST /cerrar-pregunta` vía ASGI (complementaria) | 30 | 39,39 ms | 49,51 ms | 53,18 ms | 31,82 ms | 5,14 ms |

**Veredicto: CUMPLE.** `p95 = 43,81 ms ≤ 100 ms` (umbral de `RNF_v1.md`, Rendimiento, Escenario 1),
con más de 2× de margen. La medición completa por HTTP (que suma JWT, wiring y la conexión nueva
a la base por operación) también queda muy por debajo del umbral.

**Alcance de esta evidencia (honestidad del método):**
- Máquina de desarrollo, no producción: es una cota de referencia, no una garantía del despliegue.
- Las 60 conexiones son objetos en memoria: no ejercitan sockets TCP reales ni un proxy/balanceador.
- **Checkpoint de staging pendiente** (`PROCEDIMIENTO-UAT.md` §4: Fly.io, WSS real, PostgreSQL
  administrado). Sigue como ítem abierto antes de promover a producción con usuarios reales.

---

## 3. Revisión manual

`tests/uat/inc6/guion_manual_iteracion2.sh` — **ejecutado por Víctor el 2026-09-21 y validado sin
hallazgos.** Un Docente y tres Estudiantes conectados por WebSocket real, 13 pasos:

- Sala de espera en orden de unión; `participantes_actualizados` creciendo (1, 2, 3) en los 4 clientes.
- Enunciado sin opciones, luego opciones sin indicar la correcta; feedback personal sin ranking
  (est1 2981, est2 2980, est3 0); repetir la respuesta da 422.
- Cierre con un único mensaje idéntico a los 4 clientes; el Estudiante recibe 403 al pedir el ranking
  y el Docente lo ve.
- Reconexión de est1: recupera pregunta, opciones, respuesta correcta y puntaje; `unirse` devuelve la
  misma participación; recibe el siguiente broadcast.
- Avanzar sin cerrar da 422; finalizar con 3 preguntas sin presentar funciona y el ranking por
  WebSocket coincide con el del GET; unirse y finalizar de nuevo dan 422; RBAC 403 y sesión inexistente 404.

Hallazgos: ninguno (`quality/reports/uat/inc6/hallazgos-revision-manual.md`). Los datos de la corrida
se limpiaron con `limpiar_uat.sh`.

---

## 4. Estado

| Ítem | Estado |
|------|--------|
| Capa 1 | ✅ |
| Capa 2 (RNF p95 ≤ 100 ms) | ✅ CUMPLE (43,81 ms) |
| Revisión manual de Víctor | ✅ sin hallazgos |
| RF-08/09/10 → Implementado en la matriz | ✅ (no Validado: espera el cierre de baseline del Incremento 6) |
| Checkpoint de staging del RNF (Fly.io, WSS real) | ⏳ pendiente |
