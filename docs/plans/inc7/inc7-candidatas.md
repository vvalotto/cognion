# Incremento 7 — Cierre de alcance v1

**Estado:** **Iteración 1 (UAT manual) cerrada 2026-10-02**; Iteración 2 (RF-07) pendiente, sin spike resuelto. Entre ambas se inserta el **Incremento 7-ADJ** (ver más abajo). Abierto para planificación 2026-09-30, al cerrar `BL-011`.
**Milestone:** sin crear todavía en GitHub
**Política:** último incremento de `docs/rf/PLAN_v1.md` (0 a 7) — sin BC nuevo, no requiere
Iteración 0 de Modelado (regla de `PLAN_v1.md` §"Resumen de la estrategia": "todo incremento
que introduce o extiende un BC abre con Iteración 0" — este no introduce ninguno).

## Origen y decisión de secuencia

Plan original de `PLAN_v1.md` (Iteración 1: RF-18 KPIs históricos; Iteración 2: RF-07
migración desde PDF). Decisión de Víctor 2026-09-30, al planificar el incremento: reemplazar
la Iteración 1 por una **iteración de UAT manual completa de cierre de alcance v1** — no
KPIs. `RF-18` queda diferido, sin incremento asignado (`docs/rf/RF_v1.md` revisión
2026-09-30, `docs/traceability/matrix.md`).

## Alcance

| # | Iteración | Qué | Track | Responsable de ejecución |
|---|---|---|---|---|
| 1 | UAT manual de cierre de alcance v1 | Recorrido manual y exploratorio de todo el sistema (los 7 incrementos acumulados) antes de dar el alcance v1 por cerrado. Produce 4 artefactos en `quality/reports/uat/inc7/`: `plan-de-pruebas.md`, `registro-ejecuciones.md`, `registro-hallazgos.md`, `plan-de-correccion.md` — detalle completo en `docs/plans/PROCEDIMIENTO-UAT.md` §11 | UAT, sin código de producción | Víctor (manual) |
| 2 | RF-07 — Migración desde PDFs existentes | Spike de decisión (parseo automático vs. asistido, `docs/rf/RF_v1.md` §"Ítems que requieren decisión") + implementación | Formal (`/implement-us`), con spike previo | Sesión de Claude Code + Víctor (spike) |

**Orden:** la UAT va primero porque es la validación de todo lo construido hasta ahora, no
solo de este incremento — tiene sentido hacerla antes de sumar la última pieza de scope
(RF-07), no después. El `plan-de-correccion.md` que produce puede además informar cómo se
prioriza el resto del trabajo antes de arrancar RF-07.

## Iteración 1 — UAT manual completa

Ver `docs/plans/PROCEDIMIENTO-UAT.md` §11 para el detalle de los 4 artefactos, quién los
escribe y el gate de cierre de la iteración (el `plan-de-correccion.md` aprobado por Víctor).

Resumen:
1. **Plan de pruebas UAT** (`quality/reports/uat/inc7/plan-de-pruebas.md`) — se escribe antes
   de ejecutar. Define alcance (qué RF/flujos se recorren), entorno, y criterio de aceptación.
2. **Registro de Ejecuciones** (`quality/reports/uat/inc7/registro-ejecuciones.md`) — bitácora
   narrada por Víctor y escrita por la sesión, paso a paso, mismo espíritu que
   `tests/uat/datos-reales/bitacora*.md` de incrementos anteriores.
3. **Registro de hallazgos** (`quality/reports/uat/inc7/registro-hallazgos.md`) — clasificados
   por severidad (🔴 Bloqueante / 🟡 Observación / ⚪ Estético, `PROCEDIMIENTO-UAT.md` §8).
4. **Plan de corrección** (`quality/reports/uat/inc7/plan-de-correccion.md`) — documento de
   priorización (qué hallazgo va directo, cuál necesita US-ADJ, cuál necesita un incremento
   nuevo) — **no implementa nada por sí mismo**, esa es la Iteración 2 de este incremento (si
   el hallazgo es chico) o un incremento de ajuste nuevo (si es grande), según el criterio ya
   establecido de "Clasificación de hallazgos en UAT" (`CLAUDE.md`).

Sin US-IEDD propia — es una iteración de proceso, no de feature, sin Issue de GitHub hasta
que el plan de corrección determine si hace falta uno.

## Iteración 2 — RF-07, migración desde PDF

Sin detalle todavía — se especifica después de cerrar la Iteración 1, y solo después de
resolver el spike de decisión (parseo automático vs. asistido) con Víctor presente, mismo
criterio ya aplicado al spike de puntaje del Incremento 6.

## Cierre de la Iteración 1 (2026-10-02)

UAT ejecutada en mini-sesiones (Víctor ejecuta, la sesión conduce y verifica cada paso contra
la base): 30 pasos sobre los 4 roles, RBAC transversal y sesión en vivo con iPhone/iPad reales.
Artefactos en `quality/reports/uat/inc7/` (PR #472): `plan-de-pruebas.md`,
`registro-ejecuciones.md`, `registro-hallazgos.md` (11 hallazgos: 2 🔴, 6 🟡, 3 ⚪; 3 resueltos
en el momento) y `plan-de-correccion.md`, **aprobado por Víctor** con sus 6 decisiones.
Sin pérdida de datos en ningún paso; los dos 🔴 son reglas del ciclo de vida de la cuenta, no
fallos de pantalla.

## Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1 (decidido 2026-10-02)

Va **antes** de la Iteración 2 (RF-07), fuera de la secuencia 0–7 de `PLAN_v1.md`, mismo
criterio que `3-ADJ` a `6-ADJ`. Detalle y decisiones en
`quality/reports/uat/inc7/plan-de-correccion.md` §3, §5 y §7:

| Orden | Ítem | Track |
|---|---|---|
| 0 | Commit de los fixes de #3 y #8 | Informal — hecho (PR #472) |
| 1 | Spike #1 (autoregistro `201` sin persistir, contra build de producción) y re-prueba #6 (iPhone) | Verificación |
| 2 | `US-ADJ-59` — cuenta deshabilitada no inicia sesión (#11), solo en login | Formal |
| 3 | `US-ADJ-60` — siempre ≥ 1 Administrador operativo (#4), bloqueo temporal para el último | Formal |
| 4 | `US-ADJ-61` — estado "cerrada" visible para el Estudiante (#10), con gate UX | Formal |
| 5 | #7 (texto del ranking) y #9 (evolución temporal) | Informal |
| 6 | `US-ADJ-62` — recuperar contraseña también desbloquea (#5) | Formal |

**Abierto 2026-10-02:** Milestone [#15](https://github.com/vvalotto/cognion/milestone/15) y
`docs/plans/inc7-adj/inc7-adj-candidatas.md`. Las specs de `US-ADJ-59` a `62` y sus Issues se
crean una por una, con Víctor, después (no existen todavía). El orden pasó a `59` → `60` →
`62` → `61` (ver ese archivo).

## Próximo paso

Especificar `US-ADJ-59` (Issue + spec) y arrancar el spike de #1 en paralelo. Después, la
Iteración 2 (RF-07) con su spike de decisión.
