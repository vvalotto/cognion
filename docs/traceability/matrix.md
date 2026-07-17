# Traceability Matrix — Cognion

> Estado documental: vigente
> Fuente de verdad para: trazabilidad RF → BC → Incremento → US-IEDD → estado, y escenarios de
> calidad (RNF) → BC/alcance → Incremento → estado
> Última actualización: 2026-07-17 — agregado RF-19 (cambio de contraseña por el propio
> usuario, elicitado durante el modelado del BC Identidad)
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
| RF-01 | Identidad | 1 | — | Planificado |
| RF-02 | Identidad | 1 | — | Planificado |
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
| RNF-SEG-1 | Seguridad | ADR-007 | Seguridad | Identidad (transversal a todos los BC) | 1 | Planificado | Revisión de API — RBAC + JWT validado en cada endpoint |
| RNF-USA-1 | Usabilidad | ADR-011 | Usabilidad, Escenario 1 | Frontend (transversal) | Todos los incrementos con frontend | Planificado | Gate UX de cada incremento — verificación de prototipo aprobado |
| RNF-USA-2 | Usabilidad | ADR-011 | Usabilidad, Escenario 2 | Frontend / Actividad Evaluativa en vivo | 6 | Planificado — ⚠️ ítem abierto, criterio a definir en diseño UX antes del Incremento 6 (ver `CLAUDE.md`) | Validación humana en dispositivo real (proyección en aula) |
| RNF-MANT-1 | Mantenibilidad | ADR-001 | Mantenibilidad | Banco de preguntas | 2 | Planificado — ⚠️ depende del modelo polimórfico de tipos de pregunta, a resolver en la Iteración 0 — Modelado | Spike de incorporación de un tipo nuevo en ≤ 1 jornada |
| RNF-OBS-1 | Observabilidad | ADR-002, ADR-010 | Observabilidad | Actividad Evaluativa | 3 | Planificado | Reconstrucción de una actividad evaluativa desde el event store, verificada en UAT |
| RNF-ADM-1 | Administrabilidad | ADR-008 | Administrabilidad, Escenario 1 | Infraestructura | 0 | Implementado | Pipeline de GitHub Actions ya integrado en `develop` (CI/CD + Docker) |
| RNF-ADM-2 | Administrabilidad | Sin ADR — pendiente, no hay decisión de infraestructura de producción todavía | Administrabilidad, Escenario 2 | Infraestructura | Sin asignar | Planificado — ⚠️ ítem abierto, depende de la decisión de infraestructura de producción (ver `CLAUDE.md`) | Backup mensual verificado una vez resuelta la infraestructura definitiva |

> Los escenarios marcados con ⚠️ dependen de un ítem abierto listado en `CLAUDE.md` — no
> deberían pasar de "Planificado" hasta que ese ítem se resuelva. Cuando esa decisión de
> infraestructura se tome, RNF-ADM-2 debe ganar su propio ADR antes de avanzar de estado.
