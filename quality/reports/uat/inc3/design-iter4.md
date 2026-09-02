# Diseño de Pruebas UAT — Iteración 4 del Incremento 3 "Actividad Evaluativa" (cierre completo)

| Campo | Valor |
|-------|-------|
| Incremento / Iteración | 3 / Iteración 4 (frontend, consume Iteraciones 1 a 3) |
| Baseline | `BL-004` — se abre si este UAT aprueba. Cierra el DoD completo del Incremento 3. |
| US cubiertas | `US-3.4.1` a `US-ADJ-10` (backend ya cerrado en Iteraciones 1-3: `US-3.1.1` a `US-3.3.2`) |
| Entorno | Propio |
| Fecha diseño | 2026-08-31 |

---

## Objetivo

A diferencia de los UAT de Iteración 1 y 2 (que verificaban un tramo parcial), este UAT
verifica el **DoD completo del Incremento 3** (`docs/rf/PLAN_v1.md`):

> Un estudiante completa una evaluación de período abierto de principio a fin — incluida una
> desconexión simulada para validar cero pérdida de respuestas — y el docente puede extender
> el plazo de una sesión activa.

Con la Iteración 4 (frontend, lado Docente `US-3.4.1`-`3.4.4`/`3.4.8`/`3.4.9` y lado
Estudiante `US-3.4.5`-`3.4.7`) ya cerrada, este es el primer momento en que existe una UI real
para recorrer el flujo completo — Iteraciones 1 a 3 eran backend-only y se verificaron solo
vía HTTP directo (`design.md`, Iteración 1).

## Escenario DoD

Un Docente crea una materia con un banco de preguntas, crea una actividad de período abierto,
extiende su plazo y la cierra manualmente. Un Estudiante ve sus materias y actividades
disponibles, inicia su evaluación, responde algunas preguntas (persistencia confirmada
respuesta a respuesta), simula una desconexión (recarga/reingreso — reconexión idempotente,
mismo set), pausa y reanuda manualmente, termina de responder, finaliza, y ve la revisión
completa con aciertos/errores y el texto real de las respuestas.

---

## Capas aplicables

**Capa 1 (pytest + Vitest): aplica.** Suite completa del proyecto, sin escribir tests nuevos —
evidencia fresca de esta verificación.

**Capa 2 (HTTP, entorno propio): aplica.** `smoke.sh` cubre hoy Identidad, Banco de Preguntas,
Cuentas, y el tramo de Actividad Evaluativa de la Iteración 1 (crear actividad + iniciar
evaluación, idempotencia, 422/403). Se agrega una sección nueva con el tramo que faltaba
(Iteraciones 2 y 3, backend ya cerrado pero nunca ejercitado por `smoke.sh`):

1. `POST /evaluaciones/{id}/respuestas` (estudiante) — confirma 2 respuestas (`US-3.2.1`)
2. `POST /evaluaciones/{id}/suspender` (estudiante) — pausa manual (`US-3.2.2`)
3. `POST /evaluaciones/{id}/reanudar` (estudiante) — retoma en el mismo punto, mismas
   respuestas ya marcadas (`US-3.2.2`, INV-AE-11/12)
4. `POST /evaluaciones/{id}/respuestas` — confirma la última pregunta
5. `POST /evaluaciones/{id}/finalizar` (estudiante) — `estado: Finalizada` (`US-3.2.3`)
6. `GET /evaluaciones/{id}/revision` (estudiante) — resumen + detalle, `opciones` con el
   texto real de la respuesta elegida (`US-3.2.3`, `US-3.4.7`)
7. `PATCH /actividades/{id}/periodo` (docente) — extiende `fecha_cierre` de una actividad
   vigente (`US-3.3.1`, RF-11b)
8. `POST /actividades/{id}/cerrar` (docente) — cierre manual, finaliza en cascada las
   `Evaluacion` `EnCurso` (`US-3.3.2`)
9. `POST /evaluaciones` sobre la actividad ya cerrada (esperado 422) — confirma que el
   cierre bloquea nuevos inicios

**UAT manual en navegador real:** recorrido humano en Chrome contra el backend + frontend
reales (mismo criterio que Incremento 1 `BL-002` e Incremento 2 Iteración 2) — primero un
pase de la sesión (Claude Browser), luego Víctor en persona:

Lado Docente:
1. Login como Docente
2. Materias → banco de preguntas con contenido real
3. Nueva actividad de período abierto
4. Detalle de la actividad → extender plazo
5. Cerrar la actividad manualmente

Lado Estudiante:
6. Login como Estudiante
7. Mis materias → Mis actividades (Badge "Pendiente de responder")
8. Rendir: responder 2-3 preguntas (Opción Múltiple y Verdadero/Falso)
9. "Pausar y salir" → pantalla de suspendida → "Continuar" (reanuda en el mismo punto)
10. Recargar la página en medio de la evaluación (desconexión simulada) → reconexión sin
    pérdida de respuestas
11. Responder la última pregunta → "Confirmar y finalizar" → navega a la revisión
12. Revisión: resumen correctas/incorrectas/total, texto real de la respuesta propia y —
    si falló — la correcta
13. Volver al listado de actividades → la tarjeta ya finalizada navega directo a la
    revisión, sin pasar por "rendir"

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — el Incremento 3 corre con
datos de prueba/locales (decisión 2026-08-24, PR #135); no hay entorno de staging desplegado.

---

## Criterio de aceptación

- Capa 1 (pytest + Vitest): 100% en verde, sin regresiones.
- Capa 2 (`smoke.sh` extendido): todos los pasos con el código HTTP/resultado esperado, sin
  pérdida de datos, cleanup verificado.
- DesignReviewer (`src/` completo): 0 CRITICAL.
- Recorrido en navegador real (sesión + Víctor): sin hallazgos 🔴 Bloqueantes.
- Sin no conformidades sin clasificar (toda 🟡/⚪ debe quedar registrada en `evidencia-iter4.md`
  con su track, `PLAN-CM.md` §4).
