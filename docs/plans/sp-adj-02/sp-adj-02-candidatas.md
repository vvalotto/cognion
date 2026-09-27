# SP-ADJ-02 — Iteración de ajuste del Incremento 6 (antes de `BL-011`)

**Estado:** en curso (abierta 2026-09-27)
**Milestone:** [Incremento 6 — Sesión en Vivo](https://github.com/vvalotto/cognion/milestone/8)
**Política:** `docs/plans/PLAN-CM.md` §12 (SP-ADJ: ajuste técnico y documental antes de cerrar una baseline)

## Origen y decisión de secuencia

La revisión manual de la app (2026-09-26, `quality/reports/uat/inc6/revision-manual-app.md`) y
la validación de `US-6.3.10` (2026-09-25) dejaron tres ajustes especificados: `US-ADJ-56`,
`57` y `58`. En un principio `56` y `57` iban **después** de `BL-011`; el 2026-09-26 Víctor
decidió agruparlos en una iteración de ajuste **antes** del cierre, junto con `58` y la revisión
de los ajustes diferidos de `SP-ADJ-01` (`US-ADJ-06`/`07`/`08`). `BL-011` cierra al terminar
esta iteración.

## Alcance

| # | US | Qué | Track | Issue |
|---|---|---|---|---|
| 0 | Gate UX | Ampliar wireframes y prototipos de `58` (`wireframes-actividad-evaluativa-en-vivo.md` §8, pantallas 20-22) y `56` (`wireframes-analytics.md` §6) | Diseño | — |
| 1 | `US-ADJ-58` | Cancelar una sesión `EnEspera`, finalizar desde cualquier etapa, no iniciar sin participantes | Formal (`/implement-us`) | [#445](https://github.com/vvalotto/cognion/issues/445) |
| 2 | `US-ADJ-56` | Las sesiones en vivo en "Mi desempeño" y "Desempeño por alumno" | Formal | [#441](https://github.com/vvalotto/cognion/issues/441) |
| 3 | `US-ADJ-57` | El Docente solo ve y modifica los recursos de sus materias | Formal | [#443](https://github.com/vvalotto/cognion/issues/443) |
| 4 | `US-ADJ-08` | Ver la materia/comisión de la invitación antes de registrarse | Formal | [#448](https://github.com/vvalotto/cognion/issues/448) |
| 5 | `US-ADJ-07` | Nombre legible de la comisión en el detalle de cuenta | Informal (solo `frontend/`) | — |
| 6 | Barrido documental | §12 de PLAN-CM: `docs/architecture/`, wireframes contra el código, matriz, `CLAUDE.md` | Documentación | — |

**Fuera de alcance:** `US-ADJ-06`, resuelta de hecho por `US-ADJ-37` (`UserMenu.tsx` muestra el
nombre real). Se cierra sin código.

**Orden:** `58` primero, porque completa el modo en vivo que valida `BL-011` y `56` depende del
estado `Cancelada`. Después `56`, que es lectura pura, y `57`, que toca los listados de varios
BCs y conviene hacerla con el resto ya estable. `08` y `07` cierran la iteración antes del
barrido documental.

## Decisiones de Víctor (2026-09-27): se aceptan las propuestas por defecto de cada spec

**`US-ADJ-58`**
1. `Cancelada` es un estado propio, no se reutiliza `Finalizada`.
2. Solo se cancela en `EnEspera`; una sesión `EnCurso` se termina con Finalizar.
3. Sin email a los estudiantes; alcanza con el aviso por el canal.
4. Al finalizar con la pregunta abierta, esta no se cierra: las respuestas ya dadas cuentan para el ranking y no se muestra el histograma.

**`US-ADJ-56`**
1. RF-17 y RF-20 a RF-23 no incluyen el vivo.
2. El acumulado de período abierto y el de vivo van separados.
3. Sin detalle pregunta por pregunta del vivo.

**`US-ADJ-57`**
1. `403` para los recursos de otro Docente.
2. Una actividad sin restricción de comisión la ve cualquier Docente asignado a una comisión de esa materia.
3. Los datos que ya existen se dejan como están; no se migra ni se borra nada.

**Decisión de diseño que surgió en el gate UX de `58`:** "Finalizar sesión" pide confirmación
solo con una pregunta abierta (pregunta sola o con opciones). Desde el histograma o el ranking
finaliza directo, porque ya no se corta nada.

## DoD de la iteración

- Las 4 US formales cerradas con su PR mergeado a `develop` y el Issue cerrado.
- Circuitos E2E (`frontend/e2e/`) ampliados con la cancelación y con finalizar a mitad de una pregunta.
- Barrido documental de §12 completo.
- Un solo pase de navegador real al cierre, con la base resembrada (mismo criterio que la Iteración 4 de `5-ADJ`).
