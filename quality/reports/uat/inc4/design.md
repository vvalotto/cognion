# Diseño de Pruebas UAT — Iteración 1 del Incremento 4 "Portal del estudiante y Analytics"

| Campo | Valor |
|-------|-------|
| Incremento / Iteración | 4 / Iteración 1 |
| Baseline | No aplica — cierra la Iteración 1 en `CLAUDE.md`. `BL-006` (o la que corresponda) se abre
al cierre completo del Incremento 4 (Iteraciones 1 y 2). |
| US cubiertas | `US-4.1.1` a `US-4.1.3` (RF-15: Estudiante ve su desempeño, backend + frontend) |
| Entorno | Propio |
| Fecha diseño | 2026-09-05 |

---

## Objetivo

Verificar de punta a punta la primera mitad del RF-15 (`RF_v1.md`): el Estudiante consulta su
propio desempeño histórico (correctas/incorrectas por evaluación finalizada y resumen
acumulado) en una materia, tanto desde la API como desde la pantalla "Mi desempeño"
(`wireframes-analytics.md` §2.0, `#est-desempeno`).

A diferencia de Actividad Evaluativa (Incremento 3), esta iteración no difiere el frontend —
cierra RF-15 de punta a punta de una sola vez, mismo criterio que Banco de Preguntas.

---

## Capas aplicables

**Capa 1 (pytest + Vitest): aplica.** Ya cubierta por la suite del proyecto — 775/775 tests
backend (unitarios + integración contra Postgres real + BDD/step_defs) + 242/242 tests
frontend (Vitest + React Testing Library). Se re-ejecuta como evidencia fresca de esta
verificación, sin escribir tests nuevos.

**Capa 2 (HTTP, entorno propio): aplica.** `smoke.sh` (`.claude/skills/run-cognion/smoke.sh`)
ya cubre Identidad, Banco de Preguntas, Cuentas y el flujo completo de Actividad Evaluativa
(período abierto → responder → suspender/reanudar → finalizar → revisión). Se agrega una
sección nueva de Analytics inmediatamente después de que ese flujo deja una `Evaluacion`
`Finalizada` conocida (2 preguntas V/F, respuesta correcta `false` para ambas, el estudiante
contestó `true` a las dos → 0 correctas / 2 incorrectas esperadas):

1. `GET /analytics/materias/{materia_id}/mi-desempeno` (estudiante que finalizó la evaluación)
   → la evaluación aparece en el detalle con `cantidad_correctas=0`/`cantidad_incorrectas=2`,
   resumen `cantidad_evaluaciones=1`/`total_correctas=0`/`total_incorrectas=2` (US-4.1.2)
2. Mismo endpoint con rol `docente` → 403 esperado (RBAC, `require_estudiante`)
3. `GET /analytics/materias/{materia_id}/mi-desempeno` (un segundo estudiante, sin ninguna
   `Evaluacion` finalizada en la materia) → lista vacía, resumen en cero — caso "materia sin
   evaluaciones" de `US-4.1.2`/`US-4.1.3`

**UAT manual de Víctor en navegador real:** guión aparte, `tests/uat/inc4/guion_manual_iteracion1.sh`
siembra los datos y deja el backend + frontend corriendo para que Víctor navegue la pantalla
"Mi desempeño" real. Ver `guion-manual-iteracion1.md` para el checklist paso a paso.

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — mismo criterio que las
iteraciones anteriores, no hay entorno de staging desplegado.

---

## Criterio de aceptación

- Capa 1 (pytest + Vitest) en verde, sin regresiones.
- Capa 2 (HTTP vía `smoke.sh` extendido) responde con los códigos HTTP y los valores
  (`cantidad_correctas`, `cantidad_incorrectas`, resumen acumulado) esperados, incluido el
  caso de materia sin evaluaciones y el rechazo por rol.
- UAT visual en navegador real (Víctor) sin hallazgos 🔴 Bloqueantes — clasificación de
  severidad según `PROCEDIMIENTO-UAT.md` §8.

---

## Evidencia

Ver `quality/reports/uat/inc4/evidencia.md` (Capa 1 + Capa 2, generada por la sesión) y
`quality/reports/uat/inc4/guion-manual-iteracion1.md` (revisión manual, a completar por
Víctor).
