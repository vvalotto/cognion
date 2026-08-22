# Diseño de Pruebas UAT — Iteración 2 del Incremento 2 "Cuentas y contraseñas"

| Campo | Valor |
|-------|-------|
| Incremento / Iteración | 2 / Iteración 2 |
| Baseline | No aplica — cierra la Iteración 2 en `CLAUDE.md`. `BL-003` se abre al cierre completo del Incremento 2, incluida la iteración de ajuste conjunta (`US-ADJ-01`/`US-ADJ-03`, pendiente). |
| US cubiertas | `US-2.2.1` a `US-2.2.9` (RF-03, RF-19: gestión de cuentas por administrador y cambio de contraseña propio, backend + frontend) |
| Entorno | Propio |
| Fecha diseño | 2026-08-21 |

---

## Objetivo

Verificar de punta a punta la segunda mitad del Hito del Incremento 2 (`PLAN_v1.md`):

> El administrador resuelve problemas de cuentas sin depender del docente.

Concretamente: bloqueo automático de una cuenta tras 3 intentos fallidos consecutivos (login
o cambio de contraseña propio), que el Administrador pueda encontrarla, ver su detalle y
resetear su contraseña desbloqueándola, y que cualquier usuario pueda cambiar su propia
contraseña — todo reflejado también en la UI (Iteración 2 completa, backend + frontend).

---

## Capas aplicables

**Capa 1 (pytest + Vitest): aplica.** Ya cubierta por la suite del proyecto — 357/357 tests
backend (unitarios + integración contra Postgres real + BDD/step_defs) + 148/148 tests
frontend (Vitest + React Testing Library). Se re-ejecuta como evidencia fresca de esta
verificación, sin escribir tests nuevos.

**Capa 2 (HTTP, entorno propio): aplica.** `smoke.sh` (`.claude/skills/run-cognion/smoke.sh`)
hoy cubre Identidad (Iteración 1/2 de Inc. 1) y Banco de Preguntas (Iteración 1 de Inc. 2),
pero nada de gestión de cuentas. Se agrega una sección nueva al final, reutilizando el
`estudiante` que el driver ya registra vía invitación (`US-1.1.8`):

1. `POST /identidad/login` (estudiante) con password incorrecta — 1er y 2do intento → 401
2. `POST /identidad/login` (estudiante) con password incorrecta — 3er intento consecutivo →
   401, pero la cuenta queda bloqueada (INV-ID-10, `US-2.2.1`)
3. `POST /identidad/login` (estudiante) con la password **correcta** → 403 esperado — la
   cuenta sigue bloqueada, no se llega a verificar la contraseña (`CuentaBloqueadaError`)
4. `GET /usuarios?estado=bloqueada` (administrador) → el estudiante aparece en el listado
   filtrado (`US-2.2.2`)
5. `GET /usuarios/{id}` (administrador) → detalle con `bloqueada: true` (`US-2.2.3`)
6. `POST /usuarios/{id}/resetear-password` (administrador) → `bloqueada: false` en la
   respuesta (`US-2.2.4`)
7. `POST /identidad/login` (estudiante) con la password reseteada → 200 OK — desbloqueada
8. `PUT /usuarios/me/password` (estudiante autenticado) con `password_actual` incorrecta,
   dos veces → 401 con `intentos_restantes` decreciente (`US-2.2.5`)
9. `PUT /usuarios/me/password` (estudiante) con `password_actual` incorrecta una 3ra vez →
   401 con `detail.bloqueada: true` — cuenta bloqueada por este flujo, contador propio
   (`US-2.2.1`, contador distinto al de login)
10. `POST /identidad/login` (estudiante, password correcta) → 403 — confirma que el bloqueo
    por `cambiar_password` también afecta el login (mismo campo `Usuario.bloqueada`)
11. `POST /usuarios/{id}/resetear-password` (administrador) — desbloquea de nuevo y fija una
    password conocida para dejar el flujo limpio
12. `PUT /usuarios/me/password` (estudiante, con la password reseteada) — cambio exitoso →
    204

**UAT manual de Víctor en navegador real:** recorrido humano en Chrome real contra el backend
real (mismo criterio que la Iteración 1, `BL-002`):

1. Login como Administrador
2. Listado de cuentas (`/cuentas`) — filtrar por rol y por estado
3. Ver el detalle de una cuenta
4. Resetear/desbloquear la contraseña de una cuenta
5. Login con un usuario de prueba, fallar la contraseña 3 veces seguidas → ver la alerta de
   "Cuenta bloqueada" en el login (`US-2.2.9`), formulario deshabilitado
6. Como Administrador, encontrar esa cuenta bloqueada en el listado y resetearla
7. Login exitoso con la cuenta ya desbloqueada
8. Cambiar la propia contraseña desde `/mi-cuenta/cambiar-password` (`US-2.2.8`)

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — mismo criterio que la
Iteración 1, no hay entorno de staging desplegado.

---

## Criterio de aceptación

- Capa 1 (pytest + Vitest) en verde, sin regresiones.
- Capa 2 (HTTP vía `smoke.sh` extendido) responde con los códigos HTTP y los estados
  (`bloqueada`, `intentos_restantes`) esperados en el flujo completo de bloqueo/detección/
  reseteo/desbloqueo, sin pérdida de datos.
- UAT visual en navegador real sin hallazgos 🔴 Bloqueantes — clasificación de severidad según
  `PROCEDIMIENTO-UAT.md` §8.

---

## Evidencia

Ver `quality/reports/uat/inc2/evidencia-iter2.md` (a generar tras la ejecución).
