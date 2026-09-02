# US-3.3.1: Docente extiende (o intenta acortar) el plazo de una actividad vigente

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.3`
**Tipo**: `feat backend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **modificar la fecha de cierre de una actividad vigente** —extenderla siempre, o
acortarla solo si nadie está rindiendo en este momento—
para **responder a imprevistos (RF-11b) sin arriesgar el trabajo de un estudiante que ya está
en curso**.

---

## Contexto del dominio

### Problema

`ActividadEvaluativaPeriodoAbierto` (`US-3.1.2`) se crea con una `fecha_cierre` fija y hasta
ahora inmutable. RF-11b exige poder cambiarla en caliente sobre una actividad ya vigente — el
caso de uso típico es una caída del sistema o un imprevisto de clase que corre el horario. La
regla de negocio no es simétrica: extender el plazo es siempre seguro (nadie pierde nada),
pero acortarlo puede cortarle la evaluación a un estudiante que la está rindiendo en este
mismo momento — de ahí INV-AE-04, el caso límite que motivó explícitamente este RF.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (existente, gana comando) | `ActividadEvaluativaPeriodoAbierto` | Valida INV-AE-02/04/04b y produce `PeriodoDisponibilidadModificado` |
| Comando (nuevo) | `ModificarPeriodoDisponibilidad(actividad_id, nueva_fecha_cierre)` | Emitido por el Docente |
| Domain Event (nuevo) | `PeriodoDisponibilidadModificado` | Segundo evento posible del stream de la actividad (el primero es `ActividadEvaluativaCreada`) |
| Port de query (existente, reusado) | `EvaluacionActivaQueryPort` (`US-3.2.4`) | Resuelve `ContarEvaluacionesActivas(actividad_id)` — sostiene INV-AE-04 |

Esta es la primera vez que el stream de `ActividadEvaluativaPeriodoAbierto` recibe un segundo
evento — hasta acá (`US-3.1.2`/`US-3.1.3`/`US-3.2.*`) el aggregate se leía siempre desde su
único evento de creación. `reconstruir()` sobre este aggregate se implementa en esta US (no
existía todavía, ver "Decisiones de diseño").

---

## Especificacion del comportamiento

### Precondicion

- `US-3.1.1` a `US-3.2.4` implementadas (Iteraciones 1 y 2 completas) — existe
  `ActividadEvaluativaPeriodoAbierto` persistida y el read model de evaluaciones activas
  (`EvaluacionActivaQueryPort`).
- Docente autenticado (JWT, rol `docente`), dueño de la materia de la actividad.

### Postcondicion

- `nueva_fecha_cierre` > `fecha_cierre` actual (extender): siempre permitido, sin consultar
  evaluaciones activas.
- `nueva_fecha_cierre` < `fecha_cierre` actual (acortar): permitido solo si
  `ContarEvaluacionesActivas(actividad_id) == 0` (ninguna `Evaluacion` `EnCurso` o
  `Suspendida`); si no, se rechaza con `NoSePuedeAcortarConEvaluacionesActivas`.
- Evento `PeriodoDisponibilidadModificado` persistido en el stream de la actividad; la próxima
  lectura de `fecha_cierre` (incluida la Regla 2 del `VerificadorDeVencimientos`, `US-3.2.4`)
  refleja el valor nuevo.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-02 (reutilizada) | `fecha_apertura` < `nueva_fecha_cierre` — se revalida en cada modificación, no solo en la creación. |
| INV-AE-04 (nueva) | Acortar (`nueva_fecha_cierre` < `fecha_cierre` actual) se rechaza si existe alguna `Evaluacion` `EnCurso` o `Suspendida` para la actividad. Una `Suspendida` cuenta como "estudiante activo" a este efecto — puede reanudar sin volver a `IniciarEvaluacion`. |
| INV-AE-04b (nueva, compartida con `US-3.3.2`) | Rechaza el comando si `cerrada_manualmente == true`. |

### Decisiones de diseño

1. **`reconstruir()` sobre `ActividadEvaluativaPeriodoAbierto` — replay real, no solo el primer
   evento.** Hasta esta US el aggregate nunca necesitó reconstruirse desde más de un evento
   (nota dejada en `US-3.2.4`, Decisión de diseño 4). Esta US es la que introduce el segundo
   evento posible (`PeriodoDisponibilidadModificado`) — se implementa `reconstruir()` con
   dispatch por `event_type`, mismo patrón ya usado en `Evaluacion.reconstruir()`/
   `_aplicar_evento` (`US-3.2.2`), no una solución puntual para este único caso.
2. **La Regla 2 del `VerificadorDeVencimientos` deja de leer el primer evento directamente.**
   Consecuencia obligatoria del punto 1: `US-3.2.4` dejó documentado que la Regla 2 leía
   `fecha_cierre` del primer evento del stream porque no había otro. A partir de esta US, la
   Regla 2 debe reconstruir el aggregate completo (o leer `fecha_cierre`/`cerrada_manualmente`
   post-replay) para no operar sobre un valor desactualizado tras un
   `ModificarPeriodoDisponibilidad`. Se ajusta `EvaluacionActivaQueryPort`/
   `SQLAlchemyEvaluacionActivaQueryRepository` o el propio `VerificarVencimientosUseCase` para
   resolver `fecha_cierre` vigente vía `reconstruir()`, no vía el primer evento — sin tocar la
   firma pública del Use Case ni sus tests de `US-3.2.4` que no dependían de un segundo evento.
3. **Sin invariante propia sobre cuántas veces se puede modificar el período.** El modelo no
   limita la cantidad de `PeriodoDisponibilidadModificado` en el stream — extender o acortar
   (dentro de INV-AE-04) puede repetirse cuantas veces el docente lo pida mientras la actividad
   no esté cerrada manualmente.

---

## Criterios de aceptacion

```gherkin
Feature: Docente modifica el periodo de disponibilidad de una actividad vigente (US-3.3.1)

  Scenario: Extender el plazo siempre se permite
    Given una ActividadEvaluativaPeriodoAbierto vigente con fecha_cierre en el futuro
    And existe una Evaluacion EnCurso de esa actividad
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre posterior
    Then el comando se acepta
    And se emite PeriodoDisponibilidadModificado

  Scenario: Acortar el plazo sin evaluaciones activas se permite
    Given una ActividadEvaluativaPeriodoAbierto vigente sin ninguna Evaluacion EnCurso o Suspendida
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior
    Then el comando se acepta
    And se emite PeriodoDisponibilidadModificado

  Scenario: Acortar el plazo con una evaluacion EnCurso se rechaza
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existe una Evaluacion EnCurso de esa actividad
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior
    Then se rechaza con NoSePuedeAcortarConEvaluacionesActivas
    And no se emite ningun evento

  Scenario: Acortar el plazo con una evaluacion Suspendida tambien se rechaza
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existe una Evaluacion Suspendida de esa actividad
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior
    Then se rechaza con NoSePuedeAcortarConEvaluacionesActivas

  Scenario: nueva_fecha_cierre anterior a fecha_apertura se rechaza
    Given una ActividadEvaluativaPeriodoAbierto vigente
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior a fecha_apertura
    Then se rechaza con PeriodoInvalido

  Scenario: Modificar una actividad ya cerrada manualmente se rechaza
    Given una ActividadEvaluativaPeriodoAbierto con cerrada_manualmente = true
    When el Docente ejecuta ModificarPeriodoDisponibilidad
    Then se rechaza con ActividadYaCerrada

  Scenario: Modificar una actividad inexistente se rechaza
    When el Docente ejecuta ModificarPeriodoDisponibilidad sobre un actividad_id que no existe
    Then se rechaza con ActividadNoExiste
```

---

## Fuera de alcance de esta US

- **`CerrarActividad`** — `US-3.3.2`, misma iteración pero US independiente.
- **Endpoint/pantalla de frontend** — Iteración 4 (`US-3.4.4`).
- **Notificación al estudiante de que el plazo cambió** — BC Notificaciones, fuera de este
  incremento.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí, menor — introducir `reconstruir()` real sobre `ActividadEvaluativaPeriodoAbierto` y
  ajustar cómo la Regla 2 de `US-3.2.4` lee `fecha_cierre`/`cerrada_manualmente` (Decisión de
  diseño 2) es un cambio acotado a este BC, reversible, no amerita ADR (mismo umbral aplicado
  en `US-3.2.4`).

**Capa(s) afectadas:**
- [x] Entities/Ports — `ActividadEvaluativaPeriodoAbierto.reconstruir()`/dispatch por evento
  (nuevo), método `modificar_periodo_disponibilidad()` (INV-AE-02/04/04b), evento
  `PeriodoDisponibilidadModificado`, errores `PeriodoInvalido`/
  `NoSePuedeAcortarConEvaluacionesActivas`/`ActividadYaCerrada` (los que no existan ya)
- [x] Use Cases — `ModificarPeriodoDisponibilidadUseCase` (nuevo), inyecta
  `EvaluacionActivaQueryPort` para `ContarEvaluacionesActivas`
- [x] Frameworks — ajuste en `VerificarVencimientosUseCase`/
  `SQLAlchemyEvaluacionActivaQueryRepository` (`US-3.2.4`) para leer `fecha_cierre` vigente vía
  replay en vez del primer evento
- [x] Interface Adapters — endpoint HTTP (método y ruta a definir en Fase 2 de
  `/implement-us`, ej. `PATCH /actividades/{id}/periodo`), rol `docente`
- [ ] Frontend — no aplica a esta US (Iteración 4, `US-3.4.4`)

---

## Fuente de verdad UX

No aplica todavía — el endpoint de esta US se consume recién en `US-3.4.4`
(`wireframes-actividad-evaluativa.md` §2.4 `#doc-extender-plazo`), fuera del alcance de esta
US de backend.

---

## Referencias

- Depende de: `US-3.1.2` (`ActividadEvaluativaPeriodoAbierto`), `US-3.2.4`
  (`EvaluacionActivaQueryPort`, nota de diseño 4 sobre `reconstruir()` pendiente)
- Independiente de: `US-3.3.2` (ambas solo dependen de la Iteración 2)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §4 (comandos), §5
  (INV-AE-02/04/04b), §9 punto 2
- Candidatas: `docs/plans/inc3/inc3-candidatas.md` (Iteración 3)
- Issue: [#163](https://github.com/vvalotto/cognion/issues/163)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
