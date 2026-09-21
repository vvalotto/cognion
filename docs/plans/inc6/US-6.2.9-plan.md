# Plan de Implementación: US-6.2.9 - Verificación de la sesión en vivo completa y del RNF de rendimiento

**Patrón:** clean-architecture (BC-first) — **sin código de producción**: solo tests, medición y evidencia
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Sin BDD ni tests unitarios** (clasificación confirmada): los 5 escenarios de la spec se implementan
   como tests de integración y una medición reproducible. Pipeline: 0 → 2 → 3 → 5 → 7 → 8 → 9.
2. **Helper nuevo** `crear_estudiantes(comision_id, n)` en `tests/integration/inc6/_helpers.py`: inserta N
   Estudiantes en **una sola sesión** calculando el hash bcrypt **una vez** (`crear_estudiante` hashea por
   cada uno: 60 × ~0.25 s solo en preparación). Devuelve `[(id, headers)]`.
3. **`tests/integration/inc6/test_sesion_en_vivo_completa.py`** (4 de los 5 escenarios, contra la app y la
   DB reales):
   - *Sesión completa*: 5 Estudiantes con WebSocket real (`TestClient`) recorren 3 preguntas
     (mostrar → responder → cerrar → avanzar) y se finaliza; cada paso 200, cada broadcast llega a todos,
     ranking final = suma de los `puntaje` de cada respuesta, y el Estudiante ve el ranking recién al finalizar.
   - *60 respuestas simultáneas* (`asyncio.gather`): las 60 se registran, el histograma suma exactamente 60
     y el ranking refleja los 60 puntajes.
   - *Reconexión*: el Estudiante cierra su WebSocket con la pregunta abierta, reconecta y `GET` del estado
     devuelve la pregunta, `opciones_mostradas_en` + límite y su avance; su `ParticipacionEnVivo` no se pierde.
   - *Respuesta tardía*: con `sembrar_opciones_mostradas_hace` (límite vencido) → `TiempoAgotado` 422 y el
     ranking no cambia.
4. **Medición del RNF** `tests/uat/inc6/medir_rendimiento_cierre.py` (script ejecutable, no test de pytest —
   depende de la máquina): **6 sesiones × 5 preguntas = 30 cierres** sobre preguntas distintas, con los mismos
   60 Estudiantes; en cada pregunta: mostrar → 60 respuestas por la API → **medir**
   `CerrarPreguntaActualUseCase.execute`. Corre contra PostgreSQL real, con **60 conexiones simuladas**
   registradas en el `ConnectionManager` real (medir el envío de 60 mensajes, no la red).
   - **Criterio del RNF** (lo que dice la spec): tiempo del use case, desde que empieza hasta que terminó de
     publicar. Reporta n, mediana, p95, máximo y desvío; `p95 ≤ 100 ms` → OK, si no → **hallazgo bloqueante**.
   - **Medición complementaria (no es el criterio):** el mismo cierre por `POST /cerrar-pregunta` vía ASGI,
     que suma JWT, wiring y la **conexión nueva a la DB por operación** (`NullPool`, `ADR-017`). Se reporta
     al lado para no ocultar ese costo real, pero no decide el veredicto.
   - Guarda la evidencia en `quality/reports/uat/inc6/rendimiento-cierre.json`. Vacía la DB local antes y
     después (mismo criterio que la suite).
5. **Guion manual** `tests/uat/inc6/guion_manual_iteracion2.sh` + `cliente_ws.py`: arma la sesión por HTTP
   (curl), deja un cliente WebSocket imprimiendo lo que recibe y no borra nada al final (mismo criterio que
   `tests/uat/inc3/guion_manual_iteracion1.sh`), para que **Víctor lo juzgue a ojo**.
6. **UAT:** `quality/reports/uat/inc6/design-iteracion2.md` y `evidencia-iteracion2.md` con los números
   medidos. `docs/traceability/matrix.md` (RF-08/09/10 → Implementado) **solo tras la validación de Víctor**:
   no se toca antes.
7. **Si el p95 supera 100 ms** no se optimiza dentro de esta US: se registra el hallazgo y se decide con vos
   (US-ADJ o aceptar). La iteración no cierra hasta entonces.
8. **Alcance honesto:** máquina de desarrollo, no producción — cota de referencia. El checkpoint de staging
   (Fly.io, WSS real, `PROCEDIMIENTO-UAT.md` §4) sigue pendiente y se anota en el reporte.

## Componentes a Implementar

### 1. Helper de tests
- [x] `tests/integration/inc6/_helpers.py`
  - `crear_estudiantes(comision_id, n)`

### 2. Test de integración
- [x] `tests/integration/inc6/test_sesion_en_vivo_completa.py`
  - sesión completa, 60 simultáneas, reconexión, respuesta tardía

### 3. Medición del RNF
- [x] `tests/uat/inc6/medir_rendimiento_cierre.py`
  - 30 cierres con 60 participantes, evidencia en JSON

### 4. Guion manual
- [x] `tests/uat/inc6/guion_manual_iteracion2.sh`, `cliente_ws.py`, `limpiar_uat.sh`

### 5. Evidencia UAT
- [x] `quality/reports/uat/inc6/design-iteracion2.md`, `hallazgos-revision-manual.md` (plantilla); `evidencia-iteracion2.md` en Fase 7, con la suite completa

## Tests (Fases 4–6)
- Sin Fase 4 (unitarios) ni 6 (BDD). Fase 5 = el propio test de integración de arriba.
- La suite completa corre en Fase 7 (vacía la DB local).

**Estado:** ✅ COMPLETADO (a falta de la revisión manual de Víctor)
**Fecha completado:** 2026-09-21
**Tareas:** 5/5 secciones completadas

## Desvíos respecto del plan

- Las 8 decisiones de diseño se implementaron como se aprobaron. **Sin código de producción tocado.**
- Se agregó `tests/uat/inc6/limpiar_uat.sh` (no listado): el guion deja datos sembrados y necesitaba su
  script de limpieza, como los de inc3/inc4.
- El test de sesión completa se partió en helpers (`_presentar`, `_mostrar_y_responder`, `_cerrar`) porque
  CodeGuard marcó CC 35 (grado E) en la versión monolítica.
- Fase 7: sin `.py` de `src/` modificados, CodeGuard se corrió sobre los 3 archivos Python nuevos de `tests/`.

## Métricas de Tiempo

Tiempos medidos por el tracker (PRIN-001). Detalle en `docs/reports/inc6/US-6.2.9-report.md`.

## Lecciones Aprendidas

- ✅ El RNF se cumple con margen: p95 43,81 ms (use case) contra 100 ms, y 49,51 ms por HTTP completo.
- ✅ Correr el guion manual entero antes de dárselo a Víctor detectó problemas de formato de salida.
- ⚠️ `crear_estudiante` hashea bcrypt por llamada: para 60 participantes hace falta `crear_estudiantes`.
- ⚠️ En zsh, `codeguard $FILES` con una variable de varios archivos los pasa como un solo argumento:
  usar `${=FILES}`.
- ⚠️ Las 60 conexiones son simuladas: el checkpoint de staging (Fly.io, WSS real) sigue pendiente.
