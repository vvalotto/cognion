# Diseño de Pruebas UAT — Incremento 1 "BC Identidad"

| Campo | Valor |
|-------|-------|
| Incremento | 1 |
| Baseline | BL-002 |
| US cubiertas | `US-1.1.0` a `US-1.1.9` (backend Iteración 1 + frontend Iteración 2) |
| Entorno | Propio |

---

## Capas aplicables

**Capa 1 (pytest de flujo de dominio vía `use_cases/`): aplica.** El BC Identidad tiene
dominio real desde `US-1.1.0`. Cubierta por la suite automatizada del proyecto: 71
unitarios + 38 integración (contra Postgres real) + 23 BDD (`step_defs`) = 132 tests
backend, más 46 tests frontend (Vitest + React Testing Library, componentes y flujo de
formularios).

**Capa 2 (HTTP, entorno propio): aplica.** Dos verificaciones independientes:
1. `smoke.sh` (`.claude/skills/run-cognion/smoke.sh`) — flujo real vía `curl` contra el
   backend corriendo localmente: bootstrap de Administrador, alta de Docente, creación de
   comisión, asignación, login, generación de invitación, registro de Estudiante con
   token real, y los casos de error (409 email duplicado, 422 token ya usado).
2. UAT manual de Víctor en navegador real — login como Administrador → alta de Docente →
   confirmación, ejercitando el frontend completo contra el backend real (no `fetch`
   mockeado).

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — no es uno de los
checkpoints nombrados (infraestructura/CI-CD, Incremento 5, pre-producción) y no hay
entorno de staging desplegado todavía (mismo ítem abierto de infraestructura que
`BL-001`).

---

## Escenario DoD

Un estudiante se registra vía link de invitación y queda asignado automáticamente a su
comisión; un docente y un administrador se autentican y reciben un JWT con su rol
correcto (`docs/plans/inc1/inc1-candidatas.md` §DoD del Incremento).

---

## Criterio de aceptación

- Flujo completo (alta de usuarios → comisión → asignación → invitación → registro de
  Estudiante) responde con los códigos HTTP esperados y sin pérdida de datos.
- Login por rol (Administrador/Docente/Estudiante) emite un JWT con el claim de rol
  correcto.
- El frontend consume estos endpoints reales (no solo mockeados) y navega según el
  resultado (éxito/error) definido en `docs/design/ux/wireframes-identidad.md`.
- Sin hallazgos 🔴 Bloqueantes sin resolver.

---

## Evidencia

Ver `quality/reports/uat/inc1/evidencia.md`.
