# US-ADJ-61: La actividad cerrada se ve como cerrada para el Estudiante

**Estado**: `Implementada` — Parte A (backend) 2026-10-04 (PR #483); Parte B (frontend, gate UX aprobado por Víctor el 2026-10-05)
**Iteracion / Sprint**: `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1`
(decisión de Víctor, 2026-10-02; el plan de corrección la prioriza P2 y exige gate UX)
**Tipo**: `fix` backend + frontend
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (solo lectura: read model del Estudiante)
**Bounded Context**: Actividad Evaluativa
**Origen**: UAT manual de cierre de alcance v1, hallazgo **#10** 🟡
(`quality/reports/uat/inc7/registro-hallazgos.md`, `plan-de-correccion.md` §3).

---

## Fuente de verdad UX

**Gate UX obligatorio y previo a `frontend/`.** Esta US cambia un diseño **ya aprobado**:
`docs/design/ux/wireframes-actividad-evaluativa.md` §3.1 (estados del `Badge`) y §3.2
(`#est-fuera-periodo`, mensaje único que no distingue el motivo) y el prototipo
`docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html` (`#est-actividades`,
`#est-fuera-periodo`). Hay que actualizarlos con: (1) un cuarto `Badge` "Cerrada", (2) el
mensaje propio de actividad cerrada en `#est-fuera-periodo`, y (3) el retiro de la nota al pie
que admite la ambigüedad. Sin la aprobación de Víctor no se toca `frontend/`. La **Parte A
(backend)** no depende de esto.

---

## Descripcion (lenguaje de negocio)

Como **Estudiante que no llegó a rendir una actividad que el Docente cerró (o que venció)**,
quiero **ver que está cerrada y no "pendiente de responder"**,
para **no pensar que todavía puedo hacerla ni quedarme esperando que "esté disponible"**.

---

## Contexto del dominio

### Problema (verificado en la UAT)

El Docente cerró "Parcial numero 1" a mano. Un Estudiante que no la había rendido siguió viendo
la actividad como **"Pendiente de responder"** (y "Mis materias" la contaba como "1 pendiente"), y
al entrar vio **"Todavía no está disponible — Volvé a entrar cuando la actividad esté
disponible"**: engañoso, porque no va a volver a estar disponible. El backend rechaza iniciar
correctamente (`FueraDePeriodo`).

### Causas (verificadas en el código)

- `_estado_para` (`listar_actividades_visibles.py`) tiene tres salidas y la última es un
  *catch-all*: `"pendiente"` para todo lo que no es finalizada ni futura. **No mira
  `cerrada_manualmente` ni `fecha_cierre`**, así que tanto una actividad **cerrada a mano** como
  una **vencida por fecha** se muestran "pendientes". Alcance real del hallazgo: son los dos
  casos, no solo el manual.
- El propio wireframe aprobado define "Pendiente de responder" como *"dentro del período, sin
  `Evaluacion` finalizada"* (§3.1). El código se apartó de esa definición: no es solo "fiel al
  prototipo", es un caso que el prototipo no resolvía.
- `#est-fuera-periodo` usa **un solo mensaje** para "todavía no abrió" y "ya cerró" (criterio de
  `US-3.0.2`, mismo que `US-1.1.3`), con una nota al pie que reconoce la ambigüedad.
- El lado del **Docente ya lo resuelve**: `actividades_router._estado_actividad` devuelve
  `cerrada` si `cerrada_manualmente or fecha_cierre <= ahora`. Se replica ese criterio.
- **No afectado (verificado en el código):** "Desempeño por comisión" del Docente. Sus
  "actividades pendientes" salen de `listar_actividades_abiertas`, que ya excluye las cerradas
  (`fecha_apertura ≤ ahora ≤ fecha_cierre` y `cerrada_manualmente = false`).

### Alcance del fix

**Parte A — Backend, BC Actividad Evaluativa:**

1. `EstadoVisible` gana `"cerrada"` (`"pendiente" | "todavia_no_abrio" | "cerrada" |
   "finalizada"`).
2. `_estado_para(resumen, finalizada, ahora)`, en este orden:
   1. `finalizada` → `"finalizada"` (gana siempre: la revisión sigue disponible aunque el período
      ya cerró, RF-13);
   2. `resumen.cerrada_manualmente or resumen.fecha_cierre <= ahora` → `"cerrada"`;
   3. `resumen.fecha_apertura > ahora` → `"todavia_no_abrio"`;
   4. en cualquier otro caso → `"pendiente"` (ahora sí, solo dentro del período).
3. `ActividadVisibleResponse.estado` ya es `str`: sin cambio de contrato más que el valor nuevo.
   No hace falta campo nuevo: `fecha_cierre` ya viaja.

**Parte B — Frontend (bloqueada por el gate UX):**

4. `EstadoVisible` (`actividad-evaluativa-api.ts`) gana `"cerrada"`; `MisActividades.tsx`:
   etiqueta **"Cerrada"** y variante nueva de `Badge` neutra (`visible-cerrada`,
   `components/ui/badge.tsx`).
5. `irA(actividad)`: una actividad `"cerrada"` navega a `/mis-actividades/:id/fuera-de-periodo`
   con `state { titulo, estado: "cerrada", fechaCierre }` (igual que `todavia_no_abrio` hoy).
6. `FueraDePeriodo.tsx`: según `state.estado`:
   - `"todavia_no_abrio"`: sin cambios (título "Todavía no está disponible", fecha de apertura);
   - `"cerrada"`: título **"Esta actividad ya cerró"**, texto con la fecha de cierre y "Ya no se
     puede rendir", sin invitar a volver;
   - sin `state` (llegada por el `422` de `IniciarEvaluacion`, deep link o carrera con el
     cierre): texto **neutro** ("Esta actividad no está disponible en este momento") — el `422`
     no dice cuál de los dos casos es.
   Se **retira la nota al pie** que reconocía la ambigüedad.
7. `MisMaterias.tsx` no necesita cambio de lógica: cuenta solo `estado === "pendiente"`, que
   ahora excluye las cerradas. Una materia con únicamente actividades cerradas muestra "Sin
   actividades disponibles", que es correcto.

**Fuera de alcance:**
- Distinguir al Estudiante entre cierre manual y vencimiento por fecha (los dos son "Cerrada").
- Hacer que el `422 FueraDePeriodo` informe el motivo.
- Cualquier cambio en los informes de Analytics o en las pantallas del Docente.

### Decisiones por defecto (a confirmar por Víctor)

1. **Nombre del badge "Cerrada"** y color neutro (gris), no de alerta: cerrar es un estado
   normal, no un error.
2. **Cerrada manual y vencida por fecha se muestran igual.**
3. **Prioridad `finalizada` > `cerrada`**: quien ya rindió sigue viendo "Finalizada — ver
   revisión".

---

## Especificacion del comportamiento

### Precondicion

- Una actividad con `cerrada_manualmente = true`, o con `fecha_cierre` ya pasada, y un Estudiante
  de su comisión **sin** `Evaluacion` finalizada.
- Hoy el listado le muestra "pendiente" y la pantalla de entrada dice "todavía no está
  disponible".

### Postcondicion

- El listado del Estudiante devuelve `estado = "cerrada"` para esa actividad.
- Una actividad vigente sigue `"pendiente"`; una que aún no abrió, `"todavia_no_abrio"`; una ya
  rendida, `"finalizada"` con su `evaluacion_id`.
- Al abrir una actividad cerrada el Estudiante ve "Esta actividad ya cerró" y no ve la nota al
  pie anterior.
- "Mis materias" no cuenta una actividad cerrada como pendiente.

### Invariantes

- **INV-AE-04b** (cierre manual) y el rechazo de `IniciarEvaluacion` fuera de período no cambian;
  esta US solo corrige cómo se **muestra** ese estado.

---

## Criterios de aceptacion

```gherkin
Feature: La actividad cerrada se ve como cerrada para el Estudiante (US-ADJ-61)

  Scenario: Una actividad cerrada manualmente y sin rendir se lista como cerrada
    Given una actividad con cerrada_manualmente = true
    And un Estudiante de su comisión sin Evaluacion finalizada
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "cerrada"

  Scenario: Una actividad vencida por fecha y sin rendir se lista como cerrada
    Given una actividad con fecha_cierre en el pasado y cerrada_manualmente = false
    And un Estudiante de su comisión sin Evaluacion finalizada
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "cerrada"

  Scenario: Una actividad vigente sigue pendiente
    Given una actividad con fecha_apertura en el pasado y fecha_cierre en el futuro
    When un Estudiante sin Evaluacion finalizada lista las actividades
    Then la actividad tiene estado "pendiente"

  Scenario: Una actividad que todavía no abrió sigue igual
    Given una actividad con fecha_apertura en el futuro
    When un Estudiante lista las actividades
    Then la actividad tiene estado "todavia_no_abrio"

  Scenario: Quien ya rindió ve finalizada aunque la actividad esté cerrada
    Given una actividad cerrada y un Estudiante con una Evaluacion finalizada de ella
    When el Estudiante lista las actividades
    Then la actividad tiene estado "finalizada" y trae su evaluacion_id

  Scenario: Los informes del Docente no cambian
    Given una actividad cerrada y un Estudiante que no la rindió
    When el Docente consulta "Desempeño por comisión"
    Then ese Estudiante no cuenta la actividad cerrada como pendiente

  Scenario: El listado muestra el badge "Cerrada" (frontend, tras el gate UX)
    Given una actividad cerrada que el Estudiante no rindió
    When abre "Actividades" de la materia
    Then veo el badge "Cerrada" y no "Pendiente de responder"

  Scenario: "Mis materias" no cuenta una actividad cerrada como pendiente (frontend)
    Given una materia cuya única actividad está cerrada y sin rendir
    When el Estudiante abre "Mis materias"
    Then la materia muestra "Sin actividades disponibles"

  Scenario: Abrir una actividad cerrada explica que ya cerró (frontend)
    Given una actividad cerrada que el Estudiante no rindió
    When la abre desde el listado
    Then veo "Esta actividad ya cerró" con su fecha de cierre
    And no veo "Volvé a entrar cuando la actividad esté disponible"

  Scenario: Llegar por el 422 sin contexto muestra un texto neutro (frontend)
    Given el Estudiante abre directamente la ruta de una actividad ya cerrada
    Then veo "Esta actividad no está disponible en este momento"
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — agrega un valor a un estado derivado de solo lectura; no cambia aggregates, eventos ni
  puertos.

**Capa(s) afectadas:**
- [x] Use Cases — `listar_actividades_visibles.py` (`EstadoVisible`, `_estado_para`)
- [x] Interface Adapters — sin cambio de contrato (`estado` ya es `str`)
- [x] Frontend — `actividad-evaluativa-api.ts`, `MisActividades.tsx`, `FueraDePeriodo.tsx`,
  `badge.tsx` (Parte B, tras el gate UX)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/use_cases/listar_actividades_visibles.py` | `EstadoVisible`, `_estado_para` (orden finalizada → cerrada → todavía no abrió → pendiente), docstring |
| tests unit/integration/BDD (patrón de `inc5-adj`/`inc6-adj`: `tests/features/inc7-adj/US-ADJ-61-*.feature`) | Matriz de `_estado_para` y listado por HTTP |
| tests existentes de `US-3.4.5` | Los que asumen "pendiente" para una actividad vencida |
| `frontend/src/lib/actividad-evaluativa-api.ts` | `EstadoVisible` |
| `frontend/src/pages/actividad-evaluativa/MisActividades.tsx`, `FueraDePeriodo.tsx`, `components/ui/badge.tsx` (+ tests) | Parte B |
| `docs/design/ux/wireframes-actividad-evaluativa.md` §3.1 y §3.2 + prototipo `actividad-evaluativa-periodo-abierto.html` | Gate UX |
| `docs/specs/inc3/US-3.4.5.md` | Nota "Enmendada por US-ADJ-61" (`US-3.4.5` fijó solo 3 badges) |

---

## Referencias

- Incremento: 7-ADJ — `docs/plans/inc7-adj/inc7-adj-candidatas.md`
- `quality/reports/uat/inc7/plan-de-correccion.md` §3 (`US-ADJ-61`)
- `quality/reports/uat/inc7/registro-hallazgos.md` hallazgo #10
- `docs/specs/inc3/US-3.4.5.md`, `US-3.4.6.md`, `US-3.0.2` (criterio del mensaje único)
- Issue: [#476](https://github.com/vvalotto/cognion/issues/476)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
