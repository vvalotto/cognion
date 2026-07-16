# HITO-3 — El "Próximo paso" de CLAUDE.md pedía un artefacto que el workflow no contempla para Incremento 0

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-3 — hallazgo metodológico previo a la ejecución del Incremento 0 |
| **Fecha** | 2026-07-16 |
| **Incremento / contexto** | Verificación del estado real del Incremento 0 antes de arrancarlo |
| **Relacionado** | `CLAUDE.md` §Estado actual, `docs/plans/WORKFLOW-DESARROLLO.md` §3 y §6, `HITO-1-FUNDACION-TECNICA-VS-PRIMER-BC-DOMINIO.md` (mismo tipo de falla) |

---

## Contexto

Al confirmar si el Incremento 0 ya estaba terminado, se revisó evidencia real del repo
(sin `docker-compose.yml`, sin migraciones de Alembic propias, sin `BL-001`, CI tolerando
"0 tests", CD con migraciones/deploy/healthcheck comentados) y se concluyó que el
Incremento 0 no estaba ejecutado. Víctor señaló entonces: *"pero no hay US candidatas
para el incremento 0"* — una observación que, al auditarla, resultó ser más que una
constatación: expuso que el "Próximo paso" de `CLAUDE.md` pedía armar
`docs/plans/inc0/inc0-candidatas.md`, un artefacto que el propio workflow del proyecto
no contempla para este caso.

---

## Hallazgo / Análisis

`docs/plans/WORKFLOW-DESARROLLO.md` define dos ciclos distintos según el tipo de
incremento:

- **§3 — Ciclo por Iteración (con US-IEDD):** su paso 1 es "Elaborar el archivo de US
  candidatas: `docs/plans/incN/incN-candidatas.md` → Lista todas las US del incremento".
- **§6 — Incrementos técnicos sin US** (cita explícitamente "Incremento 0 — Walking
  Skeleton" como ejemplo): branch `feature/inc-N-descripcion` → commits por tarea →
  CodeGuard → PR/DesignReviewer → merge → registrar en `BL-00N`. **Sin mención alguna de
  `incN-candidatas.md`.**

El "Próximo paso" de `CLAUDE.md` mezclaba ambos: pedía el artefacto del ciclo con US
(§3) para un incremento que el propio plan clasifica, desde la revisión del 2026-07-15,
como infraestructura pura sin dominio (§6). Es la misma clase de falla que `HITO-1`: una
inconsistencia entre documentos de planificación (acá, entre `CLAUDE.md` y
`WORKFLOW-DESARROLLO.md`) que ninguna revisión automática detecta, porque no es un error
de código sino de coherencia semántica entre artefactos de proceso.

Diferencia con `HITO-1`: ahí la inconsistencia estaba *dentro* de `PLAN_v1.md` (una
afirmación del propio documento se contradecía con su contenido). Acá está *entre* dos
documentos distintos (`CLAUDE.md` cita un paso que `WORKFLOW-DESARROLLO.md` reserva para
otro tipo de incremento) — confirma que el riesgo no es puntual a un documento, sino
estructural a cualquier punto donde un resumen operativo (`CLAUDE.md`) referencia un
procedimiento detallado sin revalidar contra la versión vigente de ese procedimiento.

---

## Aprendizaje(s)

- **L-3.1:** Cuando `CLAUDE.md` declara un "Próximo paso" que involucra un procedimiento
  ya definido en otro documento (workflow, plan), hay que releer ese documento antes de
  escribir el paso — no basta con que "suene" al patrón usual (US candidatas → specs →
  implement-us), porque no todos los incrementos siguen ese patrón.
- **L-3.2:** Una pregunta corta y aparentemente de detalle ("¿por qué no hay candidatas
  para este incremento?") puede exponer una inconsistencia de proceso, igual que en
  `HITO-1` las preguntas de dominio expusieron una inconsistencia de plan — el rol del
  human-in-the-loop sigue siendo el mismo tipo de chequeo, aplicado en un punto distinto.

---

## Relación con la hipótesis del ensayo

Refuerza `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md` §3.4 en el
mismo sentido que `HITO-1`: la detección de inconsistencias entre artefactos de
planificación es una función estructural del human-in-the-loop, no un caso aislado — ya
son dos hallazgos de esta misma naturaleza antes de ejecutar una sola línea de código del
Incremento 0.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-3.1 | Antes de escribir un "Próximo paso" en CLAUDE.md, releer el workflow vigente para ese tipo de incremento — no asumir el patrón usual | Documentación / Proceso |
| L-3.2 | Una pregunta breve sobre un detalle de proceso puede exponer una inconsistencia estructural entre documentos de planificación | Proceso |

---

*Creado: 2026-07-16*
