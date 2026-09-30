# US-5.1.3: Notificación de cierre manual de una Actividad Evaluativa de período abierto

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (dispara, sin invariante nueva) — sin aggregate del lado de Notificaciones (`BC-notificaciones-modelo.md` §2)
**Bounded Context**: Actividad Evaluativa (dispara) + Notificaciones (envía)

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **recibir un email cuando el Docente cierra manualmente una actividad de período
abierto a la que tengo acceso**,
para **enterarme de que ya no puedo rendirla, sin depender de revisar el portal** (RF-14).

---

## Contexto del dominio

### Problema

`CerrarActividadUseCase` (`US-3.3.2`) persiste `ActividadEvaluativaCerrada` solo cuando el
Docente cierra manualmente antes de tiempo — **no** cuando el período vence naturalmente
(`_estado_actividad` pasa a "cerrada" sin que se dispare ningún evento ni Use Case,
`BC-notificaciones-modelo.md` §6 decisión 1). Esta US agrega el segundo y último disparo de
RF-14, simétrico a `US-5.1.2`: al final de `CerrarActividadUseCase.execute()`, después de
persistir `ActividadEvaluativaCerrada`, invoca `NotificacionPort.notificar_cierre(...)`.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Use Case (nuevo, Notificaciones) | `NotificarCierreUseCase` | Resuelve destinatarios (`ComisionConsultaPort`, mismo criterio que `US-5.1.2`), arma asunto/cuerpo de cierre, envía por `CanalEnvioPort`, captura y loguea fallos sin abortar el resto del roster |
| Use Case (modificado) | `CerrarActividadUseCase` | Al final de `execute()`, después de persistir `ActividadEvaluativaCerrada`, invoca `NotificacionPort.notificar_cierre(...)` |
| Adapter (extendido, Actividad Evaluativa) | `NotificacionPortInProcess` (`US-5.1.2`) | Implementa también `notificar_cierre`, invocando `NotificarCierreUseCase` de Notificaciones |

No hay elementos nuevos del lado de infraestructura — reutiliza `ComisionConsultaPort` y
`CanalEnvioPort` de `US-5.1.1` sin cambios.

---

## Especificacion del comportamiento

### Precondicion

- `US-5.1.1` y `US-5.1.2` cerradas.
- Docente autenticado cierra manualmente una actividad de período abierto vigente
  (`POST /actividades/{id}/cerrar`, `US-3.3.2`).

### Postcondicion

- Cierre manual de una actividad con `comisiones_ids = [X, Y]` → se envía un email a cada
  estudiante de las comisiones X e Y.
- Cierre manual de una actividad sin restricción (`comisiones_ids = []`) → se envía a todos los
  estudiantes de todas las comisiones de la materia.
- El asunto y cuerpo del email de cierre incluyen, como mínimo: título de la actividad y
  materia (texto plano, contenido exacto a definir en el plan de implementación de esta US,
  mismo criterio que `US-5.1.2`).
- **El vencimiento natural del período (`fecha_cierre` alcanzada sin cierre manual) no dispara
  ningún email** — `VerificarVencimientosUseCase` (`US-3.2.4`) no se modifica, no invoca
  `NotificacionPort` en ningún punto.
- **El cierre en cascada de `Evaluacion`es en curso que hace `CerrarActividadUseCase` al
  finalizar automáticamente (`actor="sistema"`, `US-3.3.2`) tampoco dispara ningún email
  adicional** — el único disparo de este Use Case hacia Notificaciones es el de cierre de la
  Actividad en sí, una vez.
- Si el envío a un destinatario falla, se loguea y se continúa con el resto del roster — mismo
  criterio que `US-5.1.2`. El cierre de la actividad responde 200 igual, con o sin fallo de
  notificación.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Ningún fallo de envío de email puede propagar una excepción hacia `CerrarActividadUseCase` — `notificar_cierre` nunca lanza. |
| — | Solo `ActividadEvaluativaCerrada` disparado por cierre manual del Docente dispara este flujo — ningún otro camino de cierre (vencimiento natural, cascada de `Evaluacion`es) agrega un disparo propio. |

---

## Criterios de aceptacion

```gherkin
Feature: Notificación de cierre manual de actividad (US-5.1.3)

  Scenario: Cierre manual de actividad restringida a comisiones específicas
    Given una actividad vigente restringida a las comisiones A (2 estudiantes) y B (1 estudiante)
    When el Docente la cierra manualmente
    Then se envían 3 emails, uno por cada estudiante de A y B
    And cada email contiene el título y la materia

  Scenario: Cierre manual de actividad sin restricción
    Given una actividad vigente sin comisiones_ids, en una materia con las comisiones A y B
    When el Docente la cierra manualmente
    Then se envían emails a todos los estudiantes de A y B

  Scenario: Vencimiento natural del período no dispara notificación
    Given una actividad vigente cuya fecha_cierre ya pasó, sin cierre manual del Docente
    When VerificarVencimientosUseCase corre su verificación periódica
    Then la actividad pasa a estado cerrado
    And no se envía ningún email

  Scenario: Fallo de envío a un destinatario no aborta el resto
    Given una actividad restringida a la comisión A con 2 estudiantes
    And el envío al primer estudiante falla (SMTP no disponible momentáneamente)
    When el Docente cierra la actividad manualmente
    Then el segundo estudiante igual recibe su email de cierre
    And el cierre responde 200 igual
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — segundo y simétrico cableado de la integración de `ADR-006`, mismo patrón de riesgo
  de CBO en `CerrarActividadUseCase` que `US-5.1.2` señaló para `CrearActividadPeriodoAbiertoUseCase`
  — vigilar en el pre-push gate y resolver con el mismo criterio si aparece.

**Capa(s) afectadas:**
- [x] Use Cases (Actividad Evaluativa) — `CerrarActividadUseCase` invoca `NotificacionPort` al final
- [x] Frameworks (Actividad Evaluativa) — `NotificacionPortInProcess` gana `notificar_cierre`
- [x] Use Cases (Notificaciones) — `NotificarCierreUseCase` (nuevo)
- [ ] Frontend — no aplica, RF-14 no tiene pantalla propia

---

## Fuente de verdad UX

No aplica — BC sin pantalla propia.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/use_cases/cerrar_actividad.py` | Invoca `notificar_cierre(...)` al final de `execute()` |
| `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` | Implementa también `notificar_cierre` |
| `src/notificaciones/use_cases/notificar_cierre.py` | Nuevo — `NotificarCierreUseCase` |
| `src/notificaciones/frameworks/dependencies.py` | Expone el Use Case nuevo |
| `tests/unit/inc5/`, `tests/integration/inc5/` | Tests del Use Case nuevo, del cableado, y del no-disparo por vencimiento natural |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-notificaciones-modelo.md` §3, §5, §6
- Depende de `US-5.1.1` y `US-5.1.2`
- `US-3.3.2` (`CerrarActividadUseCase`, evento `ActividadEvaluativaCerrada`), `US-3.2.4`
  (`VerificarVencimientosUseCase`, no modificado por esta US)
- Candidatas: `docs/plans/inc5/inc5-candidatas.md` §Iteración 1 — **cierra completa la
  Iteración 1 del Incremento 5**
- Issue: [#309](https://github.com/vvalotto/cognion/issues/309)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
