# US-5.1.2: Notificación de apertura de una Actividad Evaluativa de período abierto

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto` (dispara, sin invariante nueva) — sin aggregate del lado de Notificaciones (`BC-notificaciones-modelo.md` §2)
**Bounded Context**: Actividad Evaluativa (dispara) + Notificaciones (envía)

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **recibir un email cuando el Docente crea una actividad de período abierto a la que
tengo acceso**,
para **enterarme de que hay una evaluación disponible sin depender de revisar el portal por mi
cuenta** (RF-14).

---

## Contexto del dominio

### Problema

`CrearActividadPeriodoAbiertoUseCase` (`US-3.1.2`) persiste `ActividadEvaluativaCreada` y
termina sin ningún efecto de borde adicional. `BC-notificaciones-modelo.md` §3/§5 define el
disparo: al final de ese Use Case, después de confirmar la persistencia, se invoca
`NotificacionPort.notificar_apertura(...)` (contrato ya declarado en `US-5.1.1`, sin
implementación cableada todavía). Esta US cablea la implementación in-process real y agrega el
primer Use Case de Notificaciones que resuelve destinatarios (`ComisionConsultaPort`,
`US-5.1.1`) y envía el email (`CanalEnvioPort`, `US-5.1.1`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Adapter (nuevo, Actividad Evaluativa) | `NotificacionPortInProcess` | Implementa `NotificacionPort` invocando `NotificarAperturaUseCase` de Notificaciones in-process — único punto de Actividad Evaluativa que importa `src.notificaciones` |
| Use Case (nuevo, Notificaciones) | `NotificarAperturaUseCase` | Resuelve destinatarios (`ComisionConsultaPort`), arma asunto/cuerpo, envía por `CanalEnvioPort` a cada destinatario, captura y loguea fallos de envío sin abortar el resto del roster |
| Use Case (modificado) | `CrearActividadPeriodoAbiertoUseCase` | Al final de `execute()`, después de persistir `ActividadEvaluativaCreada`, invoca `NotificacionPort.notificar_apertura(...)` — la creación de la actividad ya se confirmó, este paso no puede revertirla |

---

## Especificacion del comportamiento

### Precondicion

- `US-5.1.1` cerrada (puertos/adapters de infraestructura disponibles).
- Docente autenticado crea una actividad de período abierto (`POST /actividades`, `US-3.1.2`).

### Postcondicion

- Actividad creada con `comisiones_ids = [X, Y]` → se envía un email a cada estudiante de las
  comisiones X e Y (roster vía `ComisionConsultaPort.listar_destinatarios`).
- Actividad creada con `comisiones_ids = []` (sin restricción) → se envía a todos los
  estudiantes de todas las comisiones de la materia (`ComisionConsultaPort.listar_comisiones_por_materia`
  + `listar_destinatarios`).
- El asunto y cuerpo del email incluyen, como mínimo: título de la actividad, fecha de
  apertura, fecha de cierre y nombre de la materia — texto plano (`BC-notificaciones-modelo.md`
  §6, contenido exacto a definir en el plan de implementación de esta US).
- Si el envío a un destinatario falla (excepción de `CanalEnvioPort`), se loguea
  (`logging.warning`, incluye `estudiante_id`/`email`) y se continúa con el resto del roster —
  no se reintenta ni se acumula para un envío posterior.
- La respuesta HTTP de `POST /actividades` (201, `ActividadResponse`) es idéntica con o sin
  fallo de notificación — el estudiante/docente que interactúa con la API nunca ve un error de
  notificación.
- Actividad de período abierto **restringida por temario** (si existiera un caso sin
  `comisiones_ids`, hoy no existe — el filtro es exclusivamente por comisión, sin filtrar por
  otro criterio, mismo alcance que `BC-notificaciones-modelo.md` §4).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Ningún fallo de envío de email puede propagar una excepción hacia `CrearActividadPeriodoAbiertoUseCase` — `notificar_apertura` nunca lanza (`BC-notificaciones-modelo.md` §5). |
| — | El mismo conjunto de destinatarios se usa sin filtrar por estado individual del estudiante (ya cursa, ya rindió, etc.) — RF-14 es sobre el ciclo de la actividad, no sobre `Evaluacion`. |

---

## Criterios de aceptacion

```gherkin
Feature: Notificación de apertura de actividad (US-5.1.2)

  Scenario: Actividad restringida a comisiones específicas
    Given una materia con las comisiones A (2 estudiantes) y B (1 estudiante)
    When un Docente crea una actividad de período abierto restringida a [A, B]
    Then se envían 3 emails, uno por cada estudiante de A y B
    And cada email contiene el título, fecha de apertura, fecha de cierre y materia

  Scenario: Actividad sin restricción de comisión
    Given una materia con las comisiones A y B, sin ninguna otra comisión
    When un Docente crea una actividad de período abierto sin comisiones_ids
    Then se envían emails a todos los estudiantes de A y B

  Scenario: Fallo de envío a un destinatario no aborta el resto
    Given una actividad restringida a la comisión A con 2 estudiantes
    And el envío al primer estudiante falla (SMTP no disponible momentáneamente)
    When se dispara la notificación de apertura
    Then el segundo estudiante igual recibe su email
    And la creación de la actividad responde 201 igual

  Scenario: Materia sin comisiones
    Given una materia recién creada, sin ninguna comisión
    When un Docente crea una actividad de período abierto sin comisiones_ids
    Then no se envía ningún email
    And la creación de la actividad responde 201 igual
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — primer cableado real de una integración directa entre BCs disparada desde un Use
  Case de escritura (`ADR-006` ya cerrado, esta US lo instancia por primera vez). Vigilar CBO de
  `CrearActividadPeriodoAbiertoUseCase` al inyectar `NotificacionPort` — mismo patrón de
  CRITICAL ya visto repetidamente (`US-2.1.2`/`2.1.5`/`2.1.6`/`3.1.3`/`3.2.1`); si el pre-push
  gate lo detecta, resolver con el mismo criterio de separación por responsabilidad ya aplicado
  en esos casos (`BC-notificaciones-modelo.md` §6, pendiente listado).

**Capa(s) afectadas:**
- [x] Use Cases (Actividad Evaluativa) — `CrearActividadPeriodoAbiertoUseCase` invoca `NotificacionPort` al final
- [x] Frameworks (Actividad Evaluativa) — `NotificacionPortInProcess`, cableado en `dependencies.py`
- [x] Use Cases (Notificaciones) — `NotificarAperturaUseCase` (nuevo)
- [ ] Entities (Notificaciones) — sin cambios, reutiliza los ports de `US-5.1.1`
- [ ] Frontend — no aplica, RF-14 no tiene pantalla propia

---

## Fuente de verdad UX

No aplica — BC sin pantalla propia.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` | Nuevo — implementa `NotificacionPort` |
| `src/actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py` | Invoca `notificar_apertura(...)` al final de `execute()` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Cablea `NotificacionPortInProcess` |
| `src/notificaciones/use_cases/notificar_apertura.py` | Nuevo — `NotificarAperturaUseCase` |
| `src/notificaciones/frameworks/dependencies.py` | Expone el Use Case nuevo al adapter in-process de Actividad Evaluativa |
| `tests/unit/inc5/`, `tests/integration/inc5/` | Tests del Use Case nuevo y del cableado end-to-end (con `CanalEnvioPort` fake) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-notificaciones-modelo.md` §3, §5, §6
- Depende de `US-5.1.1` (infraestructura)
- `US-3.1.2` (`CrearActividadPeriodoAbiertoUseCase`, evento `ActividadEvaluativaCreada`)
- Candidatas: `docs/plans/inc5/inc5-candidatas.md` §Iteración 1
- Issue: [#308](https://github.com/vvalotto/cognion/issues/308)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
