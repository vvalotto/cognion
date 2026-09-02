# Diseño de Pruebas UAT — Iteración 1 del Incremento 3 "Actividad Evaluativa"

| Campo | Valor |
|-------|-------|
| Incremento / Iteración | 3 / Iteración 1 |
| Baseline | No aplica — no cierra ninguna baseline. El Incremento 3 cierra recién al completar las Iteraciones 2, 3 y 4 (frontend). Esta verificación cierra solo la Iteración 1 backend en `CLAUDE.md`. |
| US cubiertas | `US-3.1.1` (infraestructura event sourcing), `US-3.1.2` (crear actividad), `US-3.1.3` (iniciar evaluación) |
| Entorno | Propio |
| Fecha diseño | 2026-08-26 |

---

## Objetivo

Verificar de punta a punta el primer tramo del Hito del Incremento 3 — la parte del flujo que
ya está implementada: **un Docente crea una actividad de período abierto y un Estudiante puede
iniciar su evaluación recibiendo un set aleatorio de preguntas que queda fijo**. No es el DoD
completo del incremento:

> Un estudiante completa una evaluación de período abierto de principio a fin... y el docente
> extiende el plazo de una sesión activa. (`PLAN_v1.md`)

`RegistrarRespuesta`/`FinalizarEvaluacion` (Iteración 2) y la extensión de plazo (Iteración 3)
todavía no existen — el DoD completo del incremento se verifica recién al cerrar la Iteración 3.
Este UAT cierra el alcance real y acotado de la Iteración 1: alta de actividad + inicio de
evaluación con set fijo, idempotente, y las validaciones de período/rol.

**Sin frontend todavía** — `US-3.4.*` (Iteración 4) es la que construye las pantallas. Esta
verificación es 100% backend, vía HTTP directo (no hay UI para recorrer en navegador).

---

## Capas aplicables

**Capa 1 (pytest): aplica.** Suite completa del proyecto — 447/447 tests (unitarios +
integración contra PostgreSQL real + BDD/step_defs, los 4 BC). Se re-ejecuta como evidencia
fresca de esta verificación, sin escribir tests nuevos.

**Capa 2 (HTTP, entorno propio): aplica.** `smoke.sh`
(`.claude/skills/run-cognion/smoke.sh`) se extiende con el flujo real de Actividad Evaluativa,
reutilizando el `docente_token`/`estudiante_token` que el script ya obtiene en el flujo de
Identidad/Banco de Preguntas:

1. `POST /preguntas/verdadero-falso` ×2 — arma un banco con preguntas activas
2. `POST /actividades` — Docente crea una actividad de período abierto vigente (`US-3.1.2`)
3. `POST /evaluaciones` — Estudiante inicia su evaluación, verifica `preguntas_asignadas`
   con la cantidad exacta (`US-3.1.3`, RF-12)
4. `POST /evaluaciones` de nuevo — verifica idempotencia: misma `Evaluacion`, mismo set
   (INV-AE-05/06)
5. Caso de error: `POST /actividades` con `fecha_apertura` futura + `POST /evaluaciones` sobre
   ella → 422 esperado (`FueraDePeriodo`)
6. Caso de error: `POST /evaluaciones` con rol `docente` → 403 esperado (RBAC)

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — no es uno de los
checkpoints nombrados y no hay entorno de staging desplegado (mismo ítem abierto que
`BL-001`/`BL-002`/Iteración 1 de Incremento 2).

**Revisión manual de Víctor:** sin frontend, la revisión humana es vía HTTP directo — Swagger
UI (`/docs`, autogenerado por FastAPI) contra el backend local levantado con datos sembrados, o
re-ejecutando `smoke.sh` él mismo. Ver `evidencia.md` para instrucciones concretas de cómo
levantar el entorno para esa revisión.

---

## Criterio de aceptación

- Capa 1 (pytest) en verde, sin regresiones.
- Capa 2 (HTTP vía `smoke.sh` extendido) responde con los códigos HTTP esperados en el flujo
  completo y en los dos casos de error, sin pérdida de datos, y limpia el event store al
  finalizar.
- DesignReviewer sobre `src/` completo: 0 CRITICAL (ver
  `quality/reports/designreviewer/inc3-iter1-designreviewer-report.md`).
- Sin hallazgo 🔴 Bloqueante en la revisión de Víctor.

---

## Evidencia

Ver `quality/reports/uat/inc3/evidencia.md` (a generar tras la ejecución).
