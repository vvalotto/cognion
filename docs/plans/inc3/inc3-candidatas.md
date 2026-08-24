# Incremento 3 — Actividad Evaluativa, período abierto — US candidatas

> Estado documental: **Iteración 0 — Modelado pendiente de iniciar.** Este archivo define
> únicamente las US-IEDD tipo `Modelado` que arrancan el incremento (WORKFLOW-DESARROLLO.md
> §3, paso 0). El detalle de comandos/eventos de las Iteraciones 1 a 3 (RF-11, RF-11b, RF-12,
> RF-13) se agrega recién cuando el event storming y los wireframes estén aprobados por
> Víctor — mismo criterio que `inc1-candidatas.md`/`inc2-candidatas.md`, cuyas tablas de
> Iteración 1+ se escribieron junto con el cierre de su propia Iteración 0, no antes: las
> candidatas referencian el modelo de dominio aprobado, no lo anticipan (anti-patrón
> "spec-validatoria", `PLAN-CM.md` §5).
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 3 (revisión 2026-08-24 incluida — ver nota de
> estrategia de datos de prueba más abajo), `docs/rf/RF_v1.md` (RF-11, RF-11b, RF-12, RF-13),
> `docs/rf/RNF_v1.md` (Confiabilidad — escenario de interrupción durante sesión de período
> abierto), `ADR-002` (Event Sourcing + CQRS, Aceptado), `ADR-015` (BC renombrado de
> "Sesiones" a "Actividad Evaluativa", Aceptado — usar el nombre nuevo en todo artefacto
> nuevo: paths, código, Issues).

---

## Nota de contexto — estrategia de datos y gate de infraestructura

`PLAN_v1.md` (texto original) condicionaba el arranque de este incremento a resolver antes los
ítems abiertos de infraestructura de producción y backup, por ser el primer incremento con
"datos reales de estudiantes en juego". Revisión 2026-08-24 (decisión de Víctor, PR #135):
los Incrementos 3 a 7 corren con datos de prueba/locales, no datos reales de estudiantes en
producción — esa decisión institucional se resuelve recién en la última iteración antes de la
prueba funcional de validación previa al despliegue real. **El gate no bloquea el arranque de
este incremento.**

---

## Iteración 0 — Modelado

Dos US-IEDD **tipo `Modelado`** (WORKFLOW-DESARROLLO.md §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue. Ambas deben estar cerradas
antes de pasar a la Iteración 1.

Es el primer **Core Domain** del sistema (`ARQ_v1.md`, driver 3) y el primer BC con
**Event Sourcing + CQRS** (`ADR-002`) — a diferencia de Identidad y Banco de Preguntas, que
usan repositorios CRUD estándar. No existe todavía infraestructura de event store append-only
reutilizable de los BCs anteriores; el modelado debe cubrirla.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-3.0.1** | Modelado | Event storming BC Actividad Evaluativa: aggregate `ActividadEvaluativa` (período abierto), eventos de dominio (`SesionCreada`, `RespuestaRegistrada`, `SesionCerrada`, `PeriodoDisponibilidadModificado`), comandos, invariantes de persistencia atómica respuesta a respuesta (RNF Confiabilidad), invariante de set de preguntas fijo desde el inicio de la sesión, invariante de no acortar el período con estudiantes activos (RF-11b, caso límite), y el diseño concreto del event store append-only (mecanismo de persistencia, no solo el agregado) | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-actividad-evaluativa-modelo.md` |
| **US-3.0.2** | Modelado | Wireframes del flujo de período abierto: creación de sesión por el docente (materia, ventana de disponibilidad, cantidad de preguntas/intentos), extensión de plazo en caliente sobre una sesión activa, toma del examen por el estudiante (incluida la reconexión sin pérdida de respuestas), revisión al finalizar | Víctor aprueba los wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-actividad-evaluativa.md` + prototipo en `docs/design/ux/prototipos/` |

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` §4 — los escenarios RF-11,
RF-11b, RF-12, RF-13 y RNF-CONF-1/RNF-DISP-2 pasan de *Planificado* a *Especificado*
(WORKFLOW-DESARROLLO.md §3, paso 0e).

---

## Vista preliminar de iteraciones siguientes (según `PLAN_v1.md`, sin detalle de comandos/eventos)

Referencia rápida, no candidatas formales — se completan recién con el modelo aprobado:

| Iteración | RF | Contenido |
|---|---|---|
| 1 | RF-11, RF-12 | Creación de sesión de período abierto, set aleatorio por estudiante |
| 2 | RNF Confiabilidad, RF-13 | Persistencia respuesta a respuesta, revisión al finalizar |
| 3 | RF-11b | Modificación del período de disponibilidad en caliente |

**Hito del incremento:** un estudiante completa una evaluación de período abierto de principio
a fin —incluida una desconexión simulada para validar cero pérdida de respuestas— y el docente
extiende el plazo de una sesión activa.

---

## Próximos pasos

1. Crear GitHub Issues (Milestone `Incremento 3 — Actividad Evaluativa`, labels `us-iedd`,
   `incremento-3`, `tipo:modelado`) para US-3.0.1 y US-3.0.2, y sus specs en
   `docs/specs/inc3/US-3.0.1.md` / `US-3.0.2.md`.
2. Ejecutar el event storming (US-3.0.1) y los wireframes (US-3.0.2), con aprobación explícita
   de Víctor en cada Issue.
3. Al cerrar la Iteración 0: actualizar este archivo con el detalle completo de comandos/
   eventos de las Iteraciones 1 a 3, mismo formato que `inc2-candidatas.md`.
