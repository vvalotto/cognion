# US-3.1.2: Docente crea una actividad de período abierto

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-3.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `ActividadEvaluativaPeriodoAbierto`
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **crear una actividad de período abierto indicando la materia, la ventana de
disponibilidad, la cantidad de preguntas y los intentos permitidos por pregunta**
para **habilitar a mis estudiantes a rendir una evaluación de forma asincrónica dentro de esa
ventana (RF-11)**.

---

## Contexto del dominio

### Problema

Es la primera operación de negocio del BC — sin una `ActividadEvaluativaPeriodoAbierto` no hay
nada sobre lo que un estudiante pueda iniciar una `Evaluacion` (`US-3.1.3`). Depende de
`US-3.1.1` (event store) para persistir el aggregate, y de los puertos hacia BC Banco de
Preguntas / BC Identidad para validar `materia_id` y la cantidad de preguntas disponibles.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate (nuevo, primer evento de su stream) | `ActividadEvaluativaPeriodoAbierto` | `id`, `materia_id`, `fecha_apertura`, `fecha_cierre`, `cantidad_preguntas`, `cantidad_intentos_permitidos`, `cerrada_manualmente` (`false` por defecto) |
| Command | `CrearActividadPeriodoAbierto(materia_id, fecha_apertura, fecha_cierre, cantidad_preguntas, cantidad_intentos_permitidos)` | Crea el aggregate y su primer evento |
| Domain Event | `ActividadEvaluativaCreada` | Señala el alta — único evento de esta US |
| Port (nuevo) | `PreguntaConsultaPort` → BC Banco de Preguntas | Cuenta preguntas `activa = true` de la materia (INV-AE-01) — reutiliza `PreguntaRepositoryPort.filtrar` por adapter propio, sin ensanchar ese puerto (mismo criterio de `US-2.1.9`) |
| Port (nuevo) | `MateriaConsultaPort` → BC Banco de Preguntas | Valida que `materia_id` existe |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- `US-3.1.1` implementada (`EventStorePort` disponible).
- `materia_id` corresponde a una `Materia` existente con `Banco` (BC Banco de Preguntas).

### Postcondicion

- `ActividadEvaluativaPeriodoAbierto` persistida como primer evento de su propio stream
  (`EventStorePort.append`, `sequence_number = 1`).
- Evento `ActividadEvaluativaCreada` con el payload completo del aggregate recién creado.
- `cerrada_manualmente = false` por defecto.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-AE-01 | `cantidad_preguntas` ≤ cantidad de `PreguntaPlantilla` activas de la materia (consulta vía `PreguntaConsultaPort`) — `PreguntasInsuficientes` si no. |
| INV-AE-02 | `fecha_apertura` < `fecha_cierre` — `PeriodoInvalido` si no. |
| INV-AE-03 | `cantidad_intentos_permitidos` ≥ 1 — `CantidadIntentosInvalida` si no. |

---

## Criterios de aceptacion

```gherkin
Feature: Creación de actividad de período abierto (US-3.1.2)

  Scenario: Docente crea una actividad válida
    Given un Docente autenticado
    And la materia "Ingeniería de Software" tiene 20 preguntas activas en su banco
    When ejecuta CrearActividadPeriodoAbierto(materia_id, fecha_apertura, fecha_cierre,
      cantidad_preguntas=10, cantidad_intentos_permitidos=1)
    Then el sistema persiste ActividadEvaluativaPeriodoAbierto con cerrada_manualmente=false
    And se emite el evento ActividadEvaluativaCreada

  Scenario: Rechazo por preguntas insuficientes
    Given una materia con solo 5 preguntas activas en su banco
    When un Docente ejecuta CrearActividadPeriodoAbierto(..., cantidad_preguntas=10, ...)
    Then el sistema rechaza la operación con PreguntasInsuficientes
    And no se persiste ninguna actividad

  Scenario: Rechazo por período inválido
    Given un Docente autenticado
    When ejecuta CrearActividadPeriodoAbierto con fecha_apertura posterior a fecha_cierre
    Then el sistema rechaza la operación con PeriodoInvalido

  Scenario: Rechazo por cantidad de intentos inválida
    Given un Docente autenticado
    When ejecuta CrearActividadPeriodoAbierto con cantidad_intentos_permitidos=0
    Then el sistema rechaza la operación con CantidadIntentosInvalida

  Scenario: Rechazo por materia inexistente
    Given un materia_id que no existe en BC Banco de Preguntas
    When un Docente ejecuta CrearActividadPeriodoAbierto(materia_id=<inexistente>, ...)
    Then el sistema rechaza la operación con MateriaNoExiste
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — usa el event store de `US-3.1.1` y el patrón de puerto ya ratificado (`ADR-006`,
  `MateriaPort` de `US-2.1.2`) para integrarse con BC Banco de Preguntas.

**Capa(s) afectadas:**
- [x] Entities — `ActividadEvaluativaPeriodoAbierto`, `ActividadEvaluativaCreada`,
  `PreguntaConsultaPort`, `MateriaConsultaPort` (`entities/ports/`)
- [x] Use Cases — `CrearActividadPeriodoAbiertoUseCase` (valida INV-AE-01/02/03, arma el evento,
  invoca `EventStorePort.append`)
- [x] Interface Adapters — `ActividadesController`,
  `PreguntaConsultaPortInProcess`/`MateriaConsultaPortInProcess` (adapters de los puertos)
- [x] Frameworks — endpoint FastAPI `POST /actividades` (requiere rol `docente`)
- [ ] Frontend — cubierto por `US-3.4.3` (Iteración 4)

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#doc-nueva-actividad`) se
especifica en `US-3.4.3`, wireframe ya aprobado en
`docs/design/ux/wireframes-actividad-evaluativa.md` §2.2.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py` | Aggregate `ActividadEvaluativaPeriodoAbierto` |
| `src/actividad_evaluativa/entities/eventos.py` | `ActividadEvaluativaCreada` |
| `src/actividad_evaluativa/entities/errors.py` | `PreguntasInsuficientes`, `PeriodoInvalido`, `CantidadIntentosInvalida`, `MateriaNoExiste` |
| `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` | Puerto nuevo — consulta preguntas activas de una materia |
| `src/actividad_evaluativa/entities/ports/materia_consulta_port.py` | Puerto nuevo — valida existencia de `Materia` |
| `src/actividad_evaluativa/use_cases/crear_actividad_periodo_abierto.py` | Orquesta INV-AE-01/02/03, arma `ActividadEvaluativaCreada`, invoca `EventStorePort.append` |
| `src/actividad_evaluativa/interface_adapters/controllers/actividades_controller.py` | Validación de entrada, mapeo a use case |
| `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py` | Implementación — llama a BC Banco de Preguntas (`PreguntaRepositoryPort.filtrar`) |
| `src/actividad_evaluativa/frameworks/adapters/materia_consulta_port_in_process.py` | Implementación — llama a BC Banco de Preguntas (`obtener_materia`) |
| `src/actividad_evaluativa/frameworks/api/actividades_router.py` | Endpoint `POST /actividades` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Registra el nuevo use case y sus adapters |

---

## Referencias

- Depende de: `US-3.1.1` (event store)
- Relacionada con: `US-3.1.3` (consume la actividad creada aquí), `US-3.3.1`/`US-3.3.2`
  (modifican/cierran esta misma actividad), `US-2.1.2` (precedente de puerto entre BCs)
- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §3, §4, §5
  (`ActividadEvaluativaPeriodoAbierto`), §7 (puertos)
- Candidatas: `docs/plans/inc3/inc3-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
