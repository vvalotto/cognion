# Traceability Matrix — Cognion

> Estado documental: vigente
> Fuente de verdad para: trazabilidad RF → BC → Incremento → US-IEDD → estado, y escenarios de
> calidad (RNF) → BC/alcance → Incremento → estado
> Última actualización: 2026-07-23 — `US-1.1.2` implementada (backend); RF-01 permanece en
> Especificado — depende de `US-1.1.3` (rechazo por link vencido/inválido), todavía no
> implementada. RF-02 permanece en Especificado — depende de `US-1.1.4`-`US-1.1.5`,
> todavía no implementadas. `US-1.1.0` no tiene RF propio (ver nota en §3), por eso su
> implementación no mueve ninguna fila de esta tabla.
> Jerarquía de autoridad: `docs/plans/PLAN-CM.md` §6

---

## 1. Propósito

Esta matriz conecta cada Requerimiento Funcional (RF, ver `docs/rf/RF_v1.md`) con el
Bounded Context responsable, el Incremento de `docs/rf/PLAN_v1.md` donde se implementa, y la
US-IEDD que lo especifica.

También rastrea los escenarios de calidad de `docs/rf/RNF_v1.md` (§4) — un RF puede estar
"Validado" y aun así el escenario de calidad asociado (ej. rendimiento del ranking en vivo)
seguir "Planificado" hasta el incremento donde ese atributo se verifica bajo carga real. Sin
esta sección, un RNF podía quedar sin dueño explícito de incremento — el mismo problema que la
matriz ya resuelve para los RF.

## 2. Estados normalizados (obligatorios — ver `docs/plans/PLAN-CM.md` §6)

| Estado | Significado | Autoridad que lo certifica |
|---|---|---|
| **Planificado** | Existe intención en `PLAN_v1.md`, sin especificación formal | `docs/plans/` |
| **Especificado** | Tiene US-IEDD con precondición/postcondición/invariantes | `docs/specs/` |
| **Implementado** | Código integrado en `develop` | Tests unitarios pasando + revisión de código |
| **Validado** | Tests + UAT + baseline de cierre | `.cm/baselines/` |

No usar "definido" sin calificar a cuál de estos cuatro corresponde.

## 3. Matriz

| RF | BC | Incremento | US-IEDD | Estado |
|---|---|---|---|---|
| RF-01 | Identidad | 1 | US-1.1.1, US-1.1.2, US-1.1.3 | Especificado |
| RF-02 | Identidad | 1 | US-1.1.4, US-1.1.5 | Especificado |
| RF-03 | Identidad | 2 | — | Planificado |
| RF-04 | Banco de preguntas | 2 | — | Planificado |
| RF-05 | Banco de preguntas | 2 | — | Planificado |
| RF-06 | Banco de preguntas | 2 | — | Planificado |
| RF-07 | Banco de preguntas | 7 | — | Planificado |
| RF-08 | Actividad Evaluativa | 6 | — | Planificado |
| RF-09 | Actividad Evaluativa | 6 | — | Planificado |
| RF-10 | Actividad Evaluativa | 6 | — | Planificado |
| RF-11 | Actividad Evaluativa | 3 | — | Planificado |
| RF-11b | Actividad Evaluativa | 3 | — | Planificado |
| RF-12 | Actividad Evaluativa | 3 | — | Planificado |
| RF-13 | Actividad Evaluativa | 3 | — | Planificado |
| RF-14 | Notificaciones | 5 | — | Planificado |
| RF-15 | Analytics | 4 | — | Planificado |
| RF-16 | Analytics | 4 | — | Planificado |
| RF-17 | Analytics | 4 | — | Planificado |
| RF-18 | Analytics | 7 | — | Planificado |
| RF-19 | Identidad | 2 | — | Planificado |

> RF-19 agregado 2026-07-17 (elicitación dedicada, ver `docs/rf/RF_v1.md` revisión 2026-07-17
> y `docs/design/domain/BC-identidad-modelo.md` §11) — agrupado con RF-03 en el Incremento 2.

> La columna US-IEDD se completa a medida que se elaboran las US candidatas de cada
> Incremento (`docs/plans/incN/incN-candidatas.md`) — ver `docs/plans/WORKFLOW-DESARROLLO.md` §3.

> `US-1.1.0` (alta de usuarios, comisión y asignación de docentes) no tiene RF propio — surgió
> como necesidad derivada del event storming (`BC-identidad-modelo.md` §6, §9) y es
> precondición técnica de RF-01/RF-02, por eso no aparece en la columna US-IEDD de ninguna
> fila. Detalle en `docs/plans/inc1/inc1-candidatas.md`. **Estado: Implementado** — mergeada a
> `develop` el 2026-07-21 (PR #11, `docs/reports/inc1/US-1.1.0-report.md`), 37/37 tests,
> quality gates APROBADO. Con la precondición resuelta, `US-1.1.1` (Docente genera invitación)
> queda desbloqueada como siguiente paso de la Iteración 1.

> `US-1.1.1` (Docente genera invitación) — implementada (`docs/plans/inc1/US-1.1.1-plan.md`),
> 53/53 tests, quality gates APROBADO.

> `US-1.1.2` (Estudiante se registra con invitación válida) — implementada en backend
> (`docs/plans/inc1/US-1.1.2-plan.md`), 77/77 tests, quality gates APROBADO. Frontend
> diferido a una US-IEDD separada (ver nota de alcance en el plan). **RF-01 permanece en
> Especificado** — la fila no pasa a Implementado hasta que también esté implementada
> `US-1.1.3` (rechazo por link vencido/inválido), la última US-IEDD que RF-01 requiere.

## 4. Escenarios de calidad (RNF)

IDs propios (`RNF-<atributo>-N`) porque `docs/rf/RNF_v1.md` no numera los escenarios de forma
única entre atributos. Mismos cuatro estados de la sección 2 — para un escenario de calidad,
"Validado" exige evidencia específica del atributo (medición de performance, UAT bajo carga,
revisión de API, etc.), no solo tests unitarios.

**Regla:** todo escenario debe vincularse a un ADR — ver `docs/plans/PLAN-CM.md`. La única
excepción válida es que el escenario dependa de una decisión puramente de **comportamiento de
dominio** (se vincula al RF, no a un ADR inventado) o de un **ítem abierto** sin decisión
tomada todavía (se marca "Sin ADR — pendiente", nunca se deja vacío sin explicación).

| RNF | Atributo | ADR | RNF_v1.md § | BC / Alcance | Incremento | Estado | Verificación esperada |
|---|---|---|---|---|---|---|---|
| RNF-REND-1 | Rendimiento | ADR-005 | Rendimiento, Escenario 1 | Actividad Evaluativa | 6 | Planificado | Medición server-side ≤100ms con hasta 60 clientes conectados |
| RNF-DISP-1 | Disponibilidad | ADR-010 | Disponibilidad, Escenario 1 | Actividad Evaluativa / Infraestructura | 0 (healthcheck) → 6 (cancelación a los 5 min) | Planificado | Healthcheck expuesto (Inc 0) + comportamiento de cancelación verificado en UAT de Inc 6 |
| RNF-DISP-2 | Disponibilidad | N/A — decisión de dominio (RF-11b), no arquitectónica | Disponibilidad, Escenario 2 | Actividad Evaluativa | 3 | Planificado | RF-11b (modificación de cierre en caliente) cubre el escenario |
| RNF-CONF-1 | Confiabilidad | ADR-009, ADR-004 | Confiabilidad | Actividad Evaluativa | 3 | Planificado | Test de reconexión sin pérdida de respuestas confirmadas |
| RNF-SEG-1 | Seguridad | ADR-007 | Seguridad | Identidad (transversal a todos los BC) | 1 | Especificado | Revisión de API — RBAC + JWT validado en cada endpoint. Mecanismo concreto (roles derivados de `perfil`, JWT sin refresh/blacklist) definido en `docs/design/domain/BC-identidad-modelo.md` (US-1.0.1, aprobado 2026-07-17) |
| RNF-USA-1 | Usabilidad | ADR-011 | Usabilidad, Escenario 1 | Frontend (transversal) | Todos los incrementos con frontend | Planificado — gate cumplido para Incremento 1 | Gate UX de cada incremento — verificación de prototipo aprobado. Incremento 1: `docs/design/ux/wireframes-identidad.md` + prototipo aprobados (US-1.0.2, 2026-07-18). Estado global se mantiene "Planificado" hasta que cada incremento con frontend repita el gate |
| RNF-USA-2 | Usabilidad | ADR-011 | Usabilidad, Escenario 2 | Frontend / Actividad Evaluativa en vivo | 6 | Planificado — ⚠️ ítem abierto, criterio a definir en diseño UX antes del Incremento 6 (ver `CLAUDE.md`) | Validación humana en dispositivo real (proyección en aula) |
| RNF-MANT-1 | Mantenibilidad | ADR-001 | Mantenibilidad | Banco de preguntas | 2 | Planificado — ⚠️ depende del modelo polimórfico de tipos de pregunta, a resolver en la Iteración 0 — Modelado | Spike de incorporación de un tipo nuevo en ≤ 1 jornada |
| RNF-OBS-1 | Observabilidad | ADR-002, ADR-010 | Observabilidad | Actividad Evaluativa | 3 | Planificado | Reconstrucción de una actividad evaluativa desde el event store, verificada en UAT |
| RNF-ADM-1 | Administrabilidad | ADR-008 | Administrabilidad, Escenario 1 | Infraestructura | 0 | Implementado | Pipeline de GitHub Actions ya integrado en `develop` (CI/CD + Docker) |
| RNF-ADM-2 | Administrabilidad | Sin ADR — pendiente, no hay decisión de infraestructura de producción todavía | Administrabilidad, Escenario 2 | Infraestructura | Sin asignar | Planificado — ⚠️ ítem abierto, depende de la decisión de infraestructura de producción (ver `CLAUDE.md`) | Backup mensual verificado una vez resuelta la infraestructura definitiva |

> Los escenarios marcados con ⚠️ dependen de un ítem abierto listado en `CLAUDE.md` — no
> deberían pasar de "Planificado" hasta que ese ítem se resuelva. Cuando esa decisión de
> infraestructura se tome, RNF-ADM-2 debe ganar su propio ADR antes de avanzar de estado.
