# Evidencia — UAT de cierre de la Iteración 4 del Incremento 3 (DoD completo)

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc3/design-iter4.md` |
| Fecha ejecución | 2026-08-31 |
| Ejecutor | Sesión de Claude Code (recorrido en navegador real) |
| Entorno | Propio (local) |

---

## Capa 1 — Tests automatizados

- Backend: `pytest tests/unit tests/integration tests/step_defs` — **735/735** en verde tras
  el fix final (735 = 733 antes de US-ADJ-11 + 2 tests nuevos del fix de concurrencia). Sin
  regresiones en ninguna suite del proyecto.
- Frontend: `npx vitest run --no-file-parallelism` — **226/226** en verde (la corrida con
  paralelismo completo mostró flakes de contención de CPU en archivos no relacionados con esta
  Iteración — confirmado no-regresión reejecutando esos archivos en aislamiento, 8/8 y luego
  la suite completa sin paralelismo, limpia).
- `mypy src/` — limpio, 0 errores sobre 189 archivos.

## Capa 2 — HTTP (`smoke.sh` extendido)

`smoke.sh` no cubría el tramo de Iteraciones 2 y 3 de Actividad Evaluativa (responder, pausar,
reanudar, finalizar, revisión, extender plazo, cerrar) — se extendió como parte de esta UAT.
Ejecución final, con el fix ya mergeado: **todos los pasos en verde**, incluida la extensión de
plazo, el cierre manual, y el rechazo `422` a un Estudiante sin `Evaluacion` previa sobre la
actividad ya cerrada.

## DesignReviewer

0 CRITICAL en cada pre-push de las 3 PRs de esta sesión (`#191`, `#193`, `#194`).

## Recorrido en navegador real (Docente + Estudiante, backend + frontend reales)

Ejecutado por la sesión (Claude Browser) contra `develop` con los dos fixes ya mergeados.
**Recorrido humano de Víctor pendiente** — sección para completar más abajo.

### Lado Docente

1. Login como Docente (María González) — OK
2. Mis materias → Ingeniería de Software (banco con 4 preguntas: 3 V/F + 1 opción múltiple) — OK
3. Nueva actividad de período abierto ("Parcial 1 — Unidades 1 a 3", 2 preguntas) — OK, listado
   la muestra con Badge "En curso"
4. Detalle de actividad → Extender plazo (07/09 → 14/09) — OK, se refleja de inmediato en el
   detalle y en el listado del Estudiante
5. Cerrar actividad manualmente (tras finalizar el Estudiante) — OK, Badge pasa a "Cerrada"

### Lado Estudiante

6. Login como Estudiante (Juan Pérez) — OK
7. Mis materias ("1 pendiente") → Mis actividades (Badge "Pendiente de responder", refleja el
   plazo extendido) — OK
8. Rendir: responder la primera pregunta (Opción Múltiple/V-F), avanza a la 2/2 — OK
9. **Recarga de página en medio de la evaluación (desconexión simulada)** — reconexión exacta:
   misma pregunta pendiente, misma respuesta previa marcada, mismo set — OK (INV-AE-05/06)
10. "Pausar y salir" → pantalla de suspendida ("Guardamos tus 1 respuestas") → "Continuar" →
    retoma en el mismo punto — OK
11. Responder la última pregunta → botón "Confirmar y finalizar" (`US-3.4.7`) → navega a la
    revisión — OK
12. Revisión: resumen "1 Correctas / 1 Incorrectas / 2 Total", texto real de la respuesta
    propia y — en la incorrecta — la respuesta correcta — OK
13. Volver al listado → tarjeta "Finalizada — ver revisión" → navega directo a la revisión, sin
    pasar por rendir — OK

### Verificación cruzada del fix de cierre manual (backend directo)

Con la actividad ya cerrada manualmente por el Docente, un segundo Estudiante (sin
`Evaluacion` previa) intentó iniciar: `POST /evaluaciones` → **422**, mensaje
`"...no admite iniciar una evaluación en este momento"` — confirma el fix de `US-ADJ-11` contra
el flujo real, no solo el test automatizado.

---

## Hallazgos

### 🔴 Bloqueante — `IniciarEvaluacion` no rechazaba actividad cerrada manualmente

Detectado extendiendo `smoke.sh`. **Resuelto en la misma sesión**: `US-ADJ-11`, Issue
[#192](https://github.com/vvalotto/cognion/issues/192), PR
[#193](https://github.com/vvalotto/cognion/pull/193) (mergeada). Verificado end-to-end en el
recorrido manual (ver arriba).

### 🔴 Bloqueante — carrera real de concurrencia en `IniciarEvaluacion`

Detectado en el recorrido manual en navegador (React StrictMode dispara dos `POST
/evaluaciones` concurrentes al montar `RendirEvaluacion.tsx`, dejando la pantalla colgada en
"Cargando…"). **Resuelto en la misma sesión**, misma US-ADJ-11 (ampliada), PR
[#194](https://github.com/vvalotto/cognion/pull/194) (mergeada). Verificado con test de
integración real (`asyncio.gather`) y con el recorrido manual repetido tras el fix.

### 🟡 Observación — `smoke.sh` dejaba huérfanos eventos de `Evaluacion` y de
`ActividadEvaluativaPeriodoAbierto` en su cleanup

Encontrado y corregido en el camino (mismo patrón en ambos: el `DELETE` solo borraba el evento
que llevaba `materia_id`/`actividad_id` en el payload, dejando huérfanos los eventos
posteriores del stream). No es un bug de producción — solo afectaba los datos de prueba del
propio `smoke.sh`. Corregido junto con los fixes de `US-ADJ-11` (mismas PRs).

### ⚪ Estético — numeración de preguntas en la revisión empieza en 0

`RevisionEvaluacion.tsx` (`US-3.4.7`) muestra "0. {texto}" / "1. {texto}" en vez de "1."/"2." —
`fila.orden` es 0-indexado en el dominio y se renderiza sin el `+1`. No bloquea el
funcionamiento (el resto del cálculo y de la UI es correcto). Pendiente de fix — se registra
como deuda menor, track frontend-only.

---

## Criterio de aceptación — resultado

- Capa 1 (pytest + Vitest): ✅ 735/735 backend, 226/226 frontend, sin regresiones.
- Capa 2 (`smoke.sh` extendido): ✅ todos los pasos con el código esperado, cleanup verificado
  sin residuos (`SELECT count(*) FROM events` = 0 tras cada corrida).
- DesignReviewer: ✅ 0 CRITICAL en las 3 PRs de esta sesión.
- Recorrido en navegador real (sesión): ✅ sin hallazgos 🔴 Bloqueantes pendientes — los 2
  encontrados fueron resueltos y reverificados en la misma sesión.
- Recorrido en navegador real (Víctor): ⏳ **pendiente** — sección de abajo para completar.
- 1 hallazgo ⚪ Estético registrado, sin bloquear.

**Conclusión (verificación de la sesión):** el DoD completo del Incremento 3 — *"un estudiante
completa una evaluación de período abierto de principio a fin, incluida una desconexión
simulada para validar cero pérdida de respuestas, y el docente puede extender el plazo de una
sesión activa"* — queda verificado de punta a punta, backend + frontend, con los dos hallazgos
bloqueantes de esta misma UAT ya resueltos y reverificados. **UAT aprobado por la sesión,
pendiente de confirmación de Víctor en persona antes de dar el Incremento 3 por cerrado y abrir
`BL-004`.**

---

## Recorrido manual de Víctor (a completar)

<!-- Espacio para que Víctor registre su propio recorrido en navegador real, mismo criterio
     que Incrementos/Iteraciones anteriores (`BL-002`, Iteración 2 de Incremento 2). -->
