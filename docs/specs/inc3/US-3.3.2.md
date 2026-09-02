# US-3.3.2: Docente cierra una actividad manualmente antes de tiempo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.3`
**Tipo**: `feat backend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (+ cascada sobre `Evaluacion`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **cerrar una actividad antes de su fecha de cierre programada, finalizando de inmediato
cualquier evaluación que siga en curso**,
para **cortar la actividad cuando ya no tiene sentido seguir esperando** (ej. respondieron
todos, o se decidió invalidarla) **sin tener que esperar al vencimiento pasivo del período**.

---

## Contexto del dominio

### Problema

`BC-actividad-evaluativa-modelo.md` §3 describe `CerrarActividad` como una medida **opcional**
del docente, no un paso obligatorio del ciclo de vida — la mayoría de las actividades nunca lo
usan y llegan a `fecha_cierre` naturalmente (Regla 2 del `VerificadorDeVencimientos`,
`US-3.2.4`). Existe para cuando el docente quiere terminar ahora, no dentro de la próxima
pasada del job periódico (§6b: "el docente quiere terminar la actividad ahora... no dentro de
1–5 minutos"). A diferencia de `ModificarPeriodoDisponibilidad` (`US-3.3.1`), es una decisión
deliberada y **terminal**: no admite reabrir.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (existente, gana comando) | `ActividadEvaluativaPeriodoAbierto` | Valida INV-AE-04b y produce `ActividadEvaluativaCerrada` |
| Comando (nuevo) | `CerrarActividad(actividad_id)` | Emitido por el Docente |
| Domain Event (nuevo) | `ActividadEvaluativaCerrada` | Marca `cerrada_manualmente = true` |
| Use Case (existente, reutilizado) | `FinalizarEvaluacionUseCase` con `actor="sistema"` (`US-3.2.4`) | Invocado en cascada, dentro de la misma Unit of Work, una vez por cada `Evaluacion` activa de la actividad |
| Port de query (existente, reusado) | `EvaluacionActivaQueryPort` (`US-3.2.4`) | Resuelve qué `Evaluacion` de la actividad están `EnCurso`/`Suspendida` para la cascada |

Esta US implementa la **Regla 3** del `VerificadorDeVencimientos` (`BC-actividad-evaluativa-
modelo.md` §6b) — a diferencia de las Reglas 1 y 2, que corren en el background task periódico,
la Regla 3 es **síncrona**: vive dentro del propio `CerrarActividadUseCase`, en la misma Unit
of Work que emite `ActividadEvaluativaCerrada` (`ADR-009`), no en el job de `US-3.2.4`.

---

## Especificacion del comportamiento

### Precondicion

- `US-3.1.1` a `US-3.2.4` implementadas (Iteraciones 1 y 2 completas) — existe
  `FinalizarEvaluacionUseCase` con soporte de `actor="sistema"` y el read model de evaluaciones
  activas.
- Docente autenticado (JWT, rol `docente`), dueño de la materia de la actividad.

### Postcondicion

- `ActividadEvaluativaPeriodoAbierto.cerrada_manualmente` pasa a `true`, evento
  `ActividadEvaluativaCerrada` persistido.
- Toda `Evaluacion` `EnCurso`/`Suspendida` de esa actividad queda `Finalizada` de inmediato,
  cada una con su propio `EvaluacionFinalizada` (`actor = "sistema"`) — mismo efecto que la
  Regla 2, pero disparado sincrónicamente, no en la próxima pasada del job.
- Repetir `CerrarActividad` sobre una actividad ya cerrada no reemite el evento
  (`ActividadYaCerrada`).
- `ModificarPeriodoDisponibilidad` (`US-3.3.1`) sobre la misma actividad, después de este
  comando, se rechaza con `ActividadYaCerrada`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-04b (nueva, compartida con `US-3.3.1`) | `CerrarActividad` es terminal: una vez `cerrada_manualmente = true`, ni `ModificarPeriodoDisponibilidad` ni un segundo `CerrarActividad` tienen efecto. A diferencia de INV-AE-04, `CerrarActividad` **no** requiere ausencia de `Evaluacion` activas — es justamente la vía para terminar con estudiantes todavía respondiendo. |
| INV-AE-11/INV-AE-12 (reutilizadas, vía `FinalizarEvaluacionUseCase`) | Protegen cada `FinalizarEvaluacion` individual de la cascada exactamente igual que si lo disparara la Regla 2 o el propio estudiante. |

### Decisiones de diseño

1. **Cascada síncrona dentro del mismo Use Case, no un evento de dominio disparando otro
   Use Case.** `CerrarActividadUseCase.execute()` hace, en una única Unit of Work: (a) carga y
   valida `ActividadEvaluativaPeriodoAbierto` (INV-AE-04b), (b) emite
   `ActividadEvaluativaCerrada`, (c) consulta `EvaluacionActivaQueryPort` para esa
   `actividad_id`, (d) invoca `FinalizarEvaluacionUseCase.execute(evaluacion_id,
   actor="sistema")` por cada resultado. No hay un mecanismo de eventos/handlers separado —
   mismo nivel de infraestructura que el resto del proyecto (`ADR-009`, sin bus de eventos).
2. **Sin transacción única para las N finalizaciones + el cierre.** Cada `Evaluacion` conserva
   su propia Unit of Work (mismo criterio que ya aplica `US-3.2.1`/`ADR-009` a nivel de
   aggregate) — si una finalización individual fallara, no revierte el cierre de la actividad
   ni las finalizaciones ya aplicadas; se documenta como aceptable a esta escala (30-60
   alumnos) y consistente con que la Regla 2 del propio `VerificadorDeVencimientos` tampoco es
   atómica entre evaluaciones.
3. **No valida si la actividad no tiene ninguna `Evaluacion` activa.** Cerrar una actividad sin
   evaluaciones en curso es válido y trivial (cero iteraciones de la cascada) — no es un caso de
   error.

---

## Criterios de aceptacion

```gherkin
Feature: Docente cierra una actividad manualmente antes de tiempo (US-3.3.2)

  Scenario: Cerrar una actividad sin evaluaciones activas
    Given una ActividadEvaluativaPeriodoAbierto vigente sin ninguna Evaluacion EnCurso o Suspendida
    When el Docente ejecuta CerrarActividad
    Then se emite ActividadEvaluativaCerrada
    And cerrada_manualmente pasa a true

  Scenario: Cerrar una actividad finaliza en cascada las evaluaciones EnCurso
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existen dos Evaluacion EnCurso de esa actividad
    When el Docente ejecuta CerrarActividad
    Then se emite ActividadEvaluativaCerrada
    And ambas Evaluacion pasan a Finalizada
    And cada una emite EvaluacionFinalizada con actor "sistema"

  Scenario: Cerrar una actividad finaliza en cascada las evaluaciones Suspendidas tambien
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existe una Evaluacion Suspendida de esa actividad
    When el Docente ejecuta CerrarActividad
    Then la Evaluacion pasa a Finalizada

  Scenario: Cerrar una actividad ya cerrada es rechazado
    Given una ActividadEvaluativaPeriodoAbierto con cerrada_manualmente = true
    When el Docente ejecuta CerrarActividad de nuevo
    Then se rechaza con ActividadYaCerrada
    And no se emite un segundo ActividadEvaluativaCerrada

  Scenario: Modificar el periodo despues de un cierre manual es rechazado
    Given una ActividadEvaluativaPeriodoAbierto con cerrada_manualmente = true
    When el Docente ejecuta ModificarPeriodoDisponibilidad
    Then se rechaza con ActividadYaCerrada

  Scenario: Cerrar una actividad inexistente se rechaza
    When el Docente ejecuta CerrarActividad sobre un actividad_id que no existe
    Then se rechaza con ActividadNoExiste
```

---

## Fuera de alcance de esta US

- **`ModificarPeriodoDisponibilidad`** — `US-3.3.1`, misma iteración pero US independiente.
- **Endpoint/pantalla de frontend** — Iteración 4 (`US-3.4.4`).
- **Notificación al estudiante de que su evaluación fue finalizada por cierre manual** — BC
  Notificaciones, fuera de este incremento.
- **Reabrir una actividad cerrada manualmente** — decisión de diseño explícita (INV-AE-04b, no
  reversible); no hay comando para deshacer el cierre.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí, menor — la cascada síncrona multi-aggregate dentro de un único Use Case (Decisión de
  diseño 1) es un patrón nuevo en el proyecto (hasta ahora cada Use Case tocaba un solo
  aggregate), pero acotado a este BC y reversible; no amerita ADR, mismo umbral que
  `US-3.2.4`/`US-3.3.1`.

**Capa(s) afectadas:**
- [x] Entities/Ports — `ActividadEvaluativaPeriodoAbierto.cerrar()` (INV-AE-04b), evento
  `ActividadEvaluativaCerrada`, error `ActividadYaCerrada` (compartido con `US-3.3.1`, no
  duplicar si ya existe)
- [x] Use Cases — `CerrarActividadUseCase` (nuevo): valida, emite `ActividadEvaluativaCerrada`,
  consulta `EvaluacionActivaQueryPort` e invoca `FinalizarEvaluacionUseCase` en cascada
- [x] Interface Adapters — endpoint HTTP (método y ruta a definir en Fase 2 de
  `/implement-us`, ej. `POST /actividades/{id}/cerrar`), rol `docente`
- [ ] Frameworks — sin cambios nuevos más allá de lo ya construido en `US-3.2.4`
  (`EvaluacionActivaQueryPort`)
- [ ] Frontend — no aplica a esta US (Iteración 4, `US-3.4.4`)

---

## Fuente de verdad UX

No aplica todavía — el endpoint de esta US se consume recién en `US-3.4.4`
(`wireframes-actividad-evaluativa.md` §2.5 `#doc-cerrar-actividad`), fuera del alcance de esta
US de backend.

---

## Referencias

- Depende de: `US-3.1.2` (`ActividadEvaluativaPeriodoAbierto`), `US-3.2.3`
  (`FinalizarEvaluacionUseCase`), `US-3.2.4` (modo `actor="sistema"`, `EvaluacionActivaQueryPort`)
- Independiente de: `US-3.3.1` (ambas solo dependen de la Iteración 2)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3 (Regla 3, §6b),
  §4 (comandos), §5 (INV-AE-04b), §9 punto 5
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` (Iteración 3)
- Issue: [#164](https://github.com/vvalotto/cognion/issues/164)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
