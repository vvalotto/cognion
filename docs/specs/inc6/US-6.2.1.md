# US-6.2.1: Cálculo de puntaje server-side de una respuesta en vivo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `domain service backend` (técnica — sin comando de negocio propio, sin endpoint)
**Agregado principal afectado**: — (servicio de dominio puro, lo consume `ParticipacionEnVivo` en `US-6.2.4`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que el puntaje de cada respuesta en la sesión en vivo lo calcule el sistema con una
regla única y conocida**,
para **que el ranking premie acertar rápido y las preguntas más difíciles o importantes, sin
que ningún cliente pueda alterar el resultado**.

---

## Contexto del dominio

### Problema

RF-10 quedó abierto en el plan original ("algoritmo exacto pendiente"). El spike del
2026-09-17 lo resolvió con Víctor (`docs/plans/inc6/inc6-candidatas.md` §Spike RF-10). Esta US
lo implementa como una **función de dominio pura**, sin I/O, para poder probarla exhaustivamente
y reutilizarla desde `US-6.2.4` sin acoplarla a la persistencia ni al canal en vivo.

Además `RespuestaEnVivo` necesita conocer **dificultad e importancia** de la pregunta al momento
de responder, y hoy `PreguntaConsultaPort` (Actividad Evaluativa → Banco de Preguntas) no las
expone. Se agrega la operación al puerto — el adapter in-process es el único lugar que conoce los
enums de Banco de Preguntas, mismo criterio que `evaluar_correccion` (INV-AE-10).

### Fórmula (spike RF-10, confirmada sin ajuste)

```
Puntaje = 1000 × FactorTiempo × FactorDificultad × FactorImportancia   (si es correcta; si no, 0)

FactorTiempo      = 0.5 + 0.5 × (1 − tiempo_respuesta / tiempo_limite)      → [0.5, 1.0]
FactorDificultad  = {BAJO: 1.0, MEDIO: 1.5, ALTO: 2.0}
FactorImportancia = {BAJO: 1.0, MEDIO: 1.5, ALTO: 2.0}
```

Rango por pregunta: **500** (correcta, justo al límite, BAJO/BAJO) a **4000** (correcta,
instantánea, ALTO/ALTO). Una respuesta incorrecta vale **0**, sin penalización.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Enum (nuevo) | `NivelPregunta` (`BAJO`/`MEDIO`/`ALTO`) | Vocabulario propio de Actividad Evaluativa — el BC no importa los enums de `banco_preguntas` |
| Servicio de dominio (nuevo) | `calcular_puntaje(es_correcta, tiempo_respuesta_segundos, tiempo_limite_segundos, dificultad, importancia) -> int` | Función pura; redondea al entero más cercano |
| VO (nuevo) | `NivelesDePregunta(dificultad, importancia)` | Resultado de la consulta al puerto |
| Puerto (ampliado) | `PreguntaConsultaPort.obtener_niveles(pregunta_id) -> NivelesDePregunta` | Dificultad e importancia vigentes de la pregunta |

---

## Especificacion del comportamiento

### Precondicion

- `US-6.1.x` cerradas (el BC ya tiene `PreguntaConsultaPort` y su adapter in-process).

### Postcondicion

- `calcular_puntaje` devuelve un `int` determinístico según la fórmula.
- `PreguntaConsultaPort.obtener_niveles` devuelve los niveles vigentes de la pregunta.

### Reglas de la función

| Caso | Resultado |
|---|---|
| `es_correcta = False` | `0`, sin importar tiempo ni niveles |
| `tiempo_respuesta` < 0 | se toma como `0` (respuesta instantánea) |
| `tiempo_respuesta` > `tiempo_limite` | se toma como `tiempo_limite` (`FactorTiempo = 0.5`) — el rechazo por `TiempoAgotado` es responsabilidad de `US-6.2.4` (INV-AEV-08), no de esta función |
| `tiempo_limite <= 0` | `ValueError` — no debería llegar (INV-AEV-02 ya lo impide al crear la sesión) |
| Redondeo | al entero más cercano (`round`) del valor exacto, **una sola vez al final** |

### Invariantes

Ninguna nueva de dominio — implementa la fórmula del spike RF-10. INV-AEV-02 (`tiempo_limite > 0`)
ya está garantizada por `US-6.1.2`.

---

## Criterios de aceptacion

```gherkin
Feature: Cálculo de puntaje de una respuesta en vivo (US-6.2.1)

  Scenario: Respuesta correcta e instantánea en una pregunta de máxima dificultad e importancia
    Given una respuesta correcta con tiempo_respuesta=0 sobre un límite de 30 s, dificultad ALTO e importancia ALTO
    When se calcula el puntaje
    Then el resultado es 4000

  Scenario: Respuesta correcta justo al límite en una pregunta de mínima dificultad e importancia
    Given una respuesta correcta con tiempo_respuesta=30 sobre un límite de 30 s, dificultad BAJO e importancia BAJO
    When se calcula el puntaje
    Then el resultado es 500

  Scenario: Respuesta correcta a mitad de tiempo con dificultad MEDIO e importancia BAJO
    Given una respuesta correcta con tiempo_respuesta=15 sobre un límite de 30 s, dificultad MEDIO e importancia BAJO
    When se calcula el puntaje
    Then el resultado es 1125

  Scenario: Respuesta incorrecta
    Given una respuesta incorrecta, sin importar el tiempo ni los niveles
    When se calcula el puntaje
    Then el resultado es 0

  Scenario: Tiempo fuera de rango se acota
    Given una respuesta correcta con tiempo_respuesta mayor al límite
    When se calcula el puntaje
    Then se usa FactorTiempo=0.5, igual que en el límite exacto

  Scenario: Consulta de niveles de una pregunta
    Given una PreguntaPlantilla con dificultad "alto" e importancia "medio"
    When se consultan sus niveles por el puerto
    Then se obtiene NivelPregunta.ALTO y NivelPregunta.MEDIO
```

> `1125 = 1000 × (0.5 + 0.5 × 0.5) × 1.5 × 1.0 = 1000 × 0.75 × 1.5`.

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — función pura de dominio más una operación nueva en un puerto ya existente, mismo
  patrón que `evaluar_correccion`/`obtener_contenido`.

**Capa(s) afectadas:**
- [x] Entities — `puntaje_en_vivo.py` (`NivelPregunta`, `NivelesDePregunta`, `calcular_puntaje`),
  `PreguntaConsultaPort.obtener_niveles`
- [ ] Use Cases — ninguno (lo consume `US-6.2.4`)
- [ ] Interface Adapters — ninguno
- [x] Frameworks — `PreguntaConsultaPortInProcess.obtener_niveles` (mapea los enums de Banco)
- [ ] Frontend — no aplica

---

## Fuente de verdad UX

No aplica — backend puro, sin pantalla propia.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/puntaje_en_vivo.py` | `NivelPregunta`, `NivelesDePregunta`, `calcular_puntaje` (nuevo) |
| `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` | Método `obtener_niveles` |
| `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py` | Implementación |
| `tests/unit/inc3/_fakes.py` | `FakePreguntaConsultaPort.niveles` (precarga) y `obtener_niveles` |
| `tests/unit/inc6/test_puntaje_en_vivo.py` | Tests unitarios de la función (tabla de casos, bordes, redondeo) |
| `tests/integration/inc6/test_pregunta_consulta_niveles.py` | Adapter contra la DB real |

Sin `.feature`: como `US-3.1.1`/`US-6.1.1` (técnica), los escenarios de arriba quedan cubiertos
uno a uno por los tests unitarios y de integración (`skip_bdd: true`).

---

## Referencias

- Spike: `docs/plans/inc6/inc6-candidatas.md` §Spike RF-10
- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §14 (`RespuestaEnVivo.puntaje`), §17
- Precedente de puerto: `evaluar_correccion` / `obtener_contenido` en `PreguntaConsultaPort`
- Consumida por: `US-6.2.4`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
