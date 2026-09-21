# US-6.3.3: Estado completo de la sesión para reconectar la proyección

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feature backend` (consulta — ampliación aditiva de `US-6.2.8`)
**Agregado principal afectado**: — (lectura sobre `ActividadEvaluativaEnVivo` y los read models)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que si recargo la pantalla de proyección vuelva exactamente al punto de la clase**,
para **no perder el histograma, el ranking ni el conteo de respuestas frente al aula**.

---

## Contexto del dominio

### Problema

`GET /sesiones-en-vivo/{id}` (`US-6.2.8`) alcanza para que un **Estudiante** se ponga al día, pero **no para
reconstruir la proyección del Docente**: le falta lo que hoy solo viaja por broadcast.

| Pantalla de proyección | Dato que necesita | ¿Está en `GET estado`? |
|---|---|---|
| `#stage-pregunta-opciones` | `N / total ya respondieron` | **No** — `cantidad_respuestas` solo viaja por `conteo_respuestas_actualizado` y el denominador solo por `participantes_actualizados` |
| `#stage-histograma` | distribución de respuestas | **No** — solo en el broadcast `pregunta_cerrada` |
| `#stage-ranking` | ranking tras el cierre | **No** — solo en `pregunta_cerrada` (hay `GET .../ranking`, pero sin saber que corresponde al cierre) |

Sin esta US, un F5 del Docente entre "cerrar" y "siguiente" deja la proyección sin histograma ni ranking.

### Campos nuevos (aditivos, `GET /sesiones-en-vivo/{id}`)

| Campo | Para quién | Contenido |
|---|---|---|
| `total_participantes` | Docente y Estudiante | Cantidad de Estudiantes unidos (`ParticipantesSesionQueryPort`) |
| `cantidad_respuestas` | Docente y Estudiante | Respuestas registradas a la pregunta actual (`0` sin pregunta) — es la **suma de la distribución** de la pregunta actual (`ProyeccionesEnVivoQueryPort.distribucion`), sin puerto nuevo |
| `resultado_pregunta` | **Solo Docente**, y solo con `pregunta_actual_cerrada = true` | `{ distribucion: [{opcion, cantidad}], ranking: [{posicion, estudiante_id, nombre, puntaje_acumulado}] }` — mismo contenido que `pregunta_cerrada` |

`resultado_pregunta` es **`null`** para el Estudiante: el ranking sigue reservado al resultado final (`§17` punto 10).
`nombre` en el ranking sale de `US-6.3.1`.

---

## Especificacion del comportamiento

### Precondicion

- `US-6.2.8` y `US-6.3.1` cerradas.

### Postcondicion

- Ninguna escritura. Los campos existentes no cambian (compatibilidad con `US-6.2.8`).

### Excepciones

Sin excepciones nuevas (`SesionNoExiste` → 404, ya existente).

---

## Criterios de aceptacion

```gherkin
Feature: Estado completo de la sesión para reconectar la proyección (US-6.3.3)

  Scenario: El conteo de respuestas y el total de participantes
    Given una sesión con 5 participantes y 3 respuestas a la pregunta actual
    When el Docente consulta el estado
    Then total_participantes es 5 y cantidad_respuestas es 3

  Scenario: Sin pregunta actual el conteo es cero
    Given una sesión EnEspera
    When se consulta el estado
    Then cantidad_respuestas es 0 y resultado_pregunta es nulo

  Scenario: Con la pregunta cerrada el Docente recupera histograma y ranking
    Given una pregunta cerrada con respuestas registradas
    When el Docente consulta el estado
    Then resultado_pregunta trae la distribución y el ranking con nombres

  Scenario: Con la pregunta abierta no hay resultado todavía
    Given una pregunta con las opciones mostradas y sin cerrar
    When el Docente consulta el estado
    Then resultado_pregunta es nulo

  Scenario: El Estudiante nunca recibe el ranking
    Given una pregunta cerrada
    When un Estudiante consulta el estado
    Then resultado_pregunta es nulo

  Scenario: El estado anterior sigue funcionando
    Given un cliente que consume solo los campos de US-6.2.8
    When consulta el estado
    Then recibe los mismos campos de siempre
```

---

## Impacto arquitectonico

- [ ] No — extiende un use case de lectura existente con puertos ya inyectados o de la misma familia.

**Capa(s) afectadas:**
- [x] Use Cases — `ObtenerEstadoSesionUseCase` gana dependencias de lectura (`ProyeccionesEnVivoQueryPort`, `ParticipantesSesionQueryPort`): **vigilar CBO** — resolver `resultado_pregunta` en una función de módulo
- [x] Frameworks — schema y armado de la respuesta en el router
- [ ] Entities / Interface Adapters — sin cambios de estructura
- [ ] Frontend — consume `US-6.3.6` y `US-6.3.7`

---

## Fuente de verdad UX

No aplica — backend. Motivada por `wireframes-actividad-evaluativa-en-vivo.md` §2.4 (conteo), §2.5 (histograma), §2.6 (ranking).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/use_cases/obtener_estado_sesion.py` | Campos nuevos y `resultado_pregunta` |
| `src/actividad_evaluativa/frameworks/api/schemas.py`, `sesiones_en_vivo_router.py`, `dependencies.py` | Schema, armado y wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.3.3*.feature` + step defs | Unitarios, HTTP, BDD |

---

## Referencias

- Base: `docs/specs/inc6/US-6.2.8.md`
- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §15, §16, §17 punto 10
- Depende de: `US-6.2.8`, `US-6.3.1`
- Consumida por: `US-6.3.6`, `US-6.3.7`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
