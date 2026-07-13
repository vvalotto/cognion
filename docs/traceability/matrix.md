# Traceability Matrix — Cognion

> Estado documental: vigente
> Fuente de verdad para: trazabilidad RF → BC → Incremento → US-IEDD → estado
> Última actualización: 2026-07-13
> Jerarquía de autoridad: `docs/cm/PLAN-CM.md` §6

---

## 1. Propósito

Esta matriz conecta cada Requerimiento Funcional (RF, ver `docs/rf/RF_v1.md`) con el
Bounded Context responsable, el Incremento de `docs/rf/PLAN_v1.md` donde se implementa, y la
US-IEDD que lo especifica.

## 2. Estados normalizados (obligatorios — ver `docs/cm/PLAN-CM.md` §6)

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
| RF-01 | Identidad | 0 | — | Planificado |
| RF-02 | Identidad | 0 | — | Planificado |
| RF-03 | Identidad | 1 | — | Planificado |
| RF-04 | Banco de preguntas | 1 | — | Planificado |
| RF-05 | Banco de preguntas | 1 | — | Planificado |
| RF-06 | Banco de preguntas | 1 | — | Planificado |
| RF-07 | Banco de preguntas | 6 | — | Planificado |
| RF-08 | Sesiones | 5 | — | Planificado |
| RF-09 | Sesiones | 5 | — | Planificado |
| RF-10 | Sesiones | 5 | — | Planificado |
| RF-11 | Sesiones | 2 | — | Planificado |
| RF-11b | Sesiones | 2 | — | Planificado |
| RF-12 | Sesiones | 2 | — | Planificado |
| RF-13 | Sesiones | 2 | — | Planificado |
| RF-14 | Notificaciones | 4 | — | Planificado |
| RF-15 | Analytics | 3 | — | Planificado |
| RF-16 | Analytics | 3 | — | Planificado |
| RF-17 | Analytics | 3 | — | Planificado |
| RF-18 | Analytics | 6 | — | Planificado |

> La columna US-IEDD se completa a medida que se elaboran las US candidatas de cada
> Incremento (`docs/plans/incN/incN-candidatas.md`) — ver `docs/cm/WORKFLOW-DESARROLLO.md` §3.
