# US-6.2.3: Read models de ranking e histograma de la sesión en vivo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `infra backend` (técnica — sin comando de negocio propio, sin endpoint)
**Agregado principal afectado**: — (proyecciones CQRS de `ParticipacionEnVivo`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que el ranking y el histograma de respuestas estén siempre listos al cerrar una
pregunta**,
para **que aparezcan en la proyección de inmediato, sin esperar a que el sistema los calcule**.

---

## Contexto del dominio

### Problema

`RNF_v1.md` (Rendimiento, Escenario 1) exige **≤ 100 ms** de procesamiento server-side al cerrar
una pregunta con hasta 60 alumnos. El modelo (`BC-actividad-evaluativa-modelo.md` §15) lo resuelve
con dos read models **actualizados de forma incremental** con cada respuesta — el histograma
"no puede depender de una agregación calculada recién en ese momento".

Decisión de Víctor (2026-09-19, especificación de la Iteración 2): **tablas propias**, no una
query sobre `events` como en `US-3.2.4`/`US-6.1.3`. Esos casos no estaban en el camino de los
100 ms; este sí.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Tabla (nueva) | `ranking_por_sesion` `(sesion_id, estudiante_id, puntaje_acumulado, ultima_actualizacion)` | PK `(sesion_id, estudiante_id)` — puntaje acumulado por participante |
| Tabla (nueva) | `distribucion_por_pregunta` `(sesion_id, pregunta_id, opcion, cantidad)` | PK `(sesion_id, pregunta_id, opcion)` — respuestas por opción |
| Migración (nueva) | Alembic | Crea ambas tablas |
| Puerto de escritura (nuevo) | `ProyeccionesEnVivoPort` | `inicializar_participante`, `registrar_respuesta` — **sin `commit`** |
| Puerto de lectura (nuevo) | `ProyeccionesEnVivoQueryPort` | `ranking`, `distribucion`, `cantidad_respuestas` |
| Adapter SQL (nuevo) | `SQLAlchemyProyeccionesEnVivo` | Implementa ambos puertos con upserts atómicos |
| Use Case (modificado) | `UnirseASesionEnVivoUseCase` (`US-6.1.3`) | Inicializa la fila del ranking al unirse |

### Diseño de consistencia (punto central de esta US)

`SQLAlchemyEventStore.append` hace `commit` sobre la sesión (`US-3.1.1`, ADR-009). Para que el
evento y su proyección queden **atómicos** sin reabrir el event store:

1. El Use Case ejecuta primero la escritura de la proyección (queda **pendiente** en la sesión,
   sin `commit`).
2. Luego llama a `EventStorePort.append`, cuyo `commit` confirma **ambas** cosas.
3. Si `append` lanza `ConcurrenciaOptimistaError` (chequeo previo, sin `commit`), la sesión aún
   tiene la proyección pendiente: el Use Case debe hacer `rollback` antes de propagar/traducir el
   error, o el adapter debe descartar lo pendiente.

Esto se fija como **contrato del puerto** (docstring + test de integración), no como convención
implícita. Fase 2 de `/implement-us` puede refinarlo, pero no puede dejar evento y proyección
en transacciones distintas.

### Contención (60 alumnos respondiendo a la vez)

- `ranking_por_sesion`: cada alumno actualiza **su propia fila** — sin contención entre alumnos.
- `distribucion_por_pregunta`: varios alumnos incrementan la **misma fila** → se usa
  `INSERT ... ON CONFLICT DO UPDATE SET cantidad = cantidad + 1` (incremento atómico en la base),
  nunca leer-modificar-escribir en Python.

### Orden del ranking

Por `puntaje_acumulado` descendente; desempate por `ultima_actualizacion` ascendente (quien llegó
antes a ese puntaje va primero) y luego por `estudiante_id`, para que el orden sea determinístico.
La posición se calcula al leer (1, 2, 3…), no se persiste.

### Participantes sin respuestas

Todo participante unido aparece en el ranking, aun sin respuestas (puntaje 0) — coherente con
§17 punto 2 ("puntaje 0 en las anteriores" para la unión tardía). Por eso `UnirseASesionEnVivo`
inserta su fila con `ON CONFLICT DO NOTHING` **dentro de la misma transacción** del evento
`EstudianteUnido` (mismo contrato de arriba). Es una modificación acotada de `US-6.1.3`.

### Clave de `opcion` en el histograma

Texto: `str(opcion_indice)` para opción múltiple; `"verdadero"` / `"falso"` para Verdadero/Falso.

---

## Especificacion del comportamiento

### Precondicion

- `US-6.1.3` cerrada (existe el use case de unión que se modifica).

### Postcondicion

- Las tablas existen tras `alembic upgrade head` y se eliminan con `downgrade` (migración
  reversible verificada por round-trip, como `US-2.1.2`).
- `registrar_respuesta(sesion_id, estudiante_id, pregunta_id, opcion, puntaje)`: suma `puntaje` al
  acumulado del participante (creando la fila si faltara), actualiza `ultima_actualizacion` e
  incrementa en 1 el contador de esa opción — todo pendiente, sin `commit`.
- `ranking(sesion_id)`: lista ordenada con posición, `estudiante_id` y `puntaje_acumulado`.
- `distribucion(sesion_id, pregunta_id)`: cantidad por opción (solo opciones con respuestas).
- `cantidad_respuestas(sesion_id, pregunta_id)`: total de respuestas de esa pregunta.
- `UnirseASesionEnVivoUseCase` deja al participante en el ranking con 0 puntos, de forma
  idempotente (unirse dos veces no duplica ni reinicia su fila).

### Invariantes

Ninguna nueva de dominio. Contrato técnico: **evento y proyección se confirman juntos o ninguno**.

---

## Criterios de aceptacion

```gherkin
Feature: Read models de ranking e histograma (US-6.2.3)

  Scenario: Un participante que se une entra al ranking con 0 puntos
    Given una sesión en vivo
    When un Estudiante se une
    Then aparece en el ranking con puntaje_acumulado=0

  Scenario: Unirse dos veces no reinicia ni duplica la fila del ranking
    Given un Estudiante ya unido con puntaje acumulado 1500
    When intenta unirse de nuevo
    Then su fila sigue con 1500 y no hay una segunda fila

  Scenario: Registrar una respuesta suma puntaje e incrementa la opción elegida
    Given un Estudiante con 1000 puntos que elige la opción "2" y suma 500
    When se registra la respuesta
    Then su puntaje acumulado es 1500 y la opción "2" tiene 1 respuesta

  Scenario: Ranking ordenado con desempate determinístico
    Given tres participantes, dos de ellos empatados en puntaje
    When se consulta el ranking
    Then va primero el de mayor puntaje y, entre los empatados, quien llegó antes a ese puntaje

  Scenario: Incremento concurrente del histograma no pierde respuestas
    Given 60 respuestas simultáneas a la misma opción
    When se registran todas
    Then la opción tiene exactamente 60 respuestas

  Scenario: Evento y proyección son atómicos
    Given un registro de respuesta cuyo append al event store falla por concurrencia
    When se hace rollback
    Then ni el evento ni la proyección quedan persistidos

  Scenario: Migración reversible
    Given la base en el head anterior
    When se aplica y se revierte la migración
    Then las tablas se crean y se eliminan sin errores
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí, acotada — fija el contrato de atomicidad evento + proyección sobre un event store que
  hace `commit` en `append`. Si al implementar resulta insuficiente, se registra como ADR
  (`docs/adr/`) antes de cerrar la US.

**Capa(s) afectadas:**
- [x] Entities — puertos `ProyeccionesEnVivoPort` y `ProyeccionesEnVivoQueryPort`
  (`ParticipanteEnRanking`, `OpcionDistribuida`)
- [x] Use Cases — modificación de `UnirseASesionEnVivoUseCase` (5° puerto: **verificar CBO**)
- [x] Interface Adapters — ninguno
- [x] Frameworks — modelos ORM, adapter SQL, migración, wiring
- [ ] Frontend — no aplica

---

## Fuente de verdad UX

No aplica — backend puro. El ranking y el histograma se muestran en
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` (proyección), pendiente de frontend.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `migrations/versions/<rev>_read_models_sesion_en_vivo.py` | Crea `ranking_por_sesion` y `distribucion_por_pregunta` (reversible) |
| `src/actividad_evaluativa/entities/ports/proyecciones_en_vivo_port.py` | Puertos de escritura y de lectura + VOs (nuevo) |
| `src/actividad_evaluativa/frameworks/db/models.py` | Modelos ORM de ambas tablas |
| `src/actividad_evaluativa/frameworks/adapters/proyecciones_en_vivo_repository.py` | Adapter SQL con upserts atómicos (nuevo) |
| `src/actividad_evaluativa/use_cases/unirse_a_sesion_en_vivo.py` | Inicializa la fila del ranking antes del `append` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Wiring |
| `tests/unit/inc6/_fakes.py` | Fake en memoria de ambos puertos |
| `tests/integration/inc6/` | Adapter contra la DB real, concurrencia, atomicidad, migración |
| `tests/integration/inc6/conftest.py` | Limpiar también las tablas nuevas |

Sin `.feature` (`skip_bdd: true`, técnica): los escenarios quedan cubiertos por los tests de
integración.

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §15 (read models), §16
- RNF: `docs/rf/RNF_v1.md` Rendimiento, Escenario 1
- Precedente de separación command/query: `US-3.2.4` (`EvaluacionActivaQueryPort`)
- ADR: `ADR-009` (Unit of Work), `ADR-004` (PostgreSQL)
- Consumida por: `US-6.2.4`, `US-6.2.5`, `US-6.2.7`, `US-6.2.8`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
