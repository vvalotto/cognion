# Modelo de datos — implementación en PostgreSQL

## Propósito

Describe cómo queda implementado el modelo de datos de Cognión en PostgreSQL: qué tablas
existen, cómo se relacionan y — sobre todo — cómo se sostiene el aislamiento entre Bounded
Contexts (BC) cuando la base de datos física **no** impone esa frontera.

No repite el detalle de entidades por BC — eso vive en `24a-modelo-datos-identidad.md`,
`24b-modelo-datos-banco-preguntas.md` y `24c-modelo-datos-actividad-evaluativa.md`. Tampoco
repite el modelado de dominio (agregados, invariantes, eventos) — eso vive en
`docs/design/domain/BC-<nombre>-modelo.md`. Este documento es la vista de *persistencia*.

## Principio central: un solo esquema físico, aislamiento por convención

Cognión es un monolito modular. Todos los BC comparten:

- **una sola base PostgreSQL**, sin schemas separados (todo vive en `public`);
- **una sola clase `Base`** declarativa de SQLAlchemy (`src/shared/frameworks/db.py`), de la
  que heredan los modelos ORM de todos los BC;
- **un solo motor/engine** async, con `NullPool` (`ADR-018`) — sin pool de conexiones
  persistente entre requests.

Esto significa que **el Bounded Context no es una frontera de base de datos** — es una
frontera de código (`entities → use_cases → interface_adapters → frameworks`, ver
`docs/architecture/03-bounded-contexts.md`). Dos tablas de BC distintos pueden convivir en el
mismo `SELECT` sin que Postgres lo impida; lo que impide mezclarlas es la regla de imports:
cada BC arma su propio composition root en `frameworks/dependencies.py`, y nunca importa el
de otro BC.

## Dos paradigmas de persistencia conviviendo

| BC | Paradigma | Detalle |
|----|-----------|---------|
| Identidad | Relacional clásico | `24a-modelo-datos-identidad.md` |
| Banco de Preguntas | Relacional clásico | `24b-modelo-datos-banco-preguntas.md` |
| Actividad Evaluativa | Event Sourcing + CQRS (`ADR-002`) | `24c-modelo-datos-actividad-evaluativa.md` |
| Notificaciones | Sin persistencia propia — BC reactivo puro | — |
| Analytics | Sin persistencia propia — proyecta sobre `events` de Actividad Evaluativa | — |

Identidad y Banco de Preguntas resuelven su modelo como tablas con FKs, en el estilo
relacional tradicional. Actividad Evaluativa es distinto: no tiene una tabla por aggregate
(no existe `actividad_evaluativa` ni `evaluacion`) — tiene **una única tabla `events`**,
append-only, donde cada fila es un evento de dominio ya ocurrido. El aggregate se reconstruye
en memoria haciendo replay del stream (`aggregate_type` + `aggregate_id`), no se lee como fila.

## Cómo se sostiene el aislamiento entre BC sin frontera física

1. **FK real solo dentro del mismo BC.** Ejemplo: `pregunta_plantilla.banco_id` referencia
   `banco.id` (mismo BC, `banco_preguntas`) con `ForeignKey` real. En cambio
   `comision.materia_id` (Identidad) apunta a `materia` (Banco de Preguntas) — BC distinto —
   y **no tiene `ForeignKey` en el modelo ORM**: es un UUID plano, resuelto en tiempo de
   ejecución contra un puerto (`US-2.1.2`, refactor explícito para eliminar el import directo
   entre BCs).

2. **Comunicación cruzada = puertos in-process, nunca JOIN SQL.** Cuando un BC necesita datos
   de otro, no hace una consulta contra la tabla del otro BC — llama a un puerto definido en su
   propio `entities/ports/`, implementado por un adapter in-process que sí conoce el otro BC
   por dentro. Puertos cruzados existentes a la fecha:

   | Puerto | BC consumidor → BC provisto | Origen |
   |--------|------------------------------|--------|
   | `MateriaPort` | Identidad → Banco de Preguntas | `US-2.1.2` |
   | `ComisionConsultaPort` (Analytics) | Analytics → Identidad | `US-4.2.2` |
   | `PreguntaMetadatoConsultaPort` | Analytics → Banco de Preguntas | `US-4.2.3` |
   | `ComisionConsultaPort` (Notificaciones) | Notificaciones → Identidad | Incremento 5 |
   | `ComisionConsultaPort` (Banco de Preguntas) | Banco de Preguntas → Identidad | Paso 8, estabilización |
   | `EvaluacionConsultaPort` | Identidad → Actividad Evaluativa | Paso 8, estabilización |
   | `ComisionConsultaPort` (Actividad Evaluativa en vivo) | Actividad Evaluativa → Identidad | `US-6.0.1` |

   Nota: varios puertos se llaman `ComisionConsultaPort` en BC distintos — son interfaces
   independientes, cada una definida en el `entities/ports/` de su propio BC consumidor, no
   una interfaz compartida.

3. **Cada BC arma su propio composition root.** `frameworks/dependencies.py` de cada BC
   importa de `shared/`, nunca de otro BC directamente.

## Por qué `ArchitectAnalyst` no ve esto como un problema (ni lo detectaría bien si lo fuera)

La "Zone of Pain" que reporta `ArchitectAnalyst` en cada cierre de baseline (un CRITICAL por
paquete raíz de BC) es un **falso positivo aceptado permanentemente**, con causa raíz
documentada en `US-ADJ-13` y corregida en `US-ADJ-19`: un bug de `DependencyGraphBuilder`
(`vvalotto/software_limpio#77`) deja `Ca=Ce=0` para *todos* los módulos del proyecto, no solo
entre BC, porque no normaliza el prefijo `src.` de los imports reales (`from src.<bc>...`).
Con eso, la métrica de distancia colapsa y marca CRITICAL en cualquier paquete de baja
abstracción — sin relación real con el acoplamiento de este modelo de datos. El detalle
completo vive en `CLAUDE.md` §Quality gates y en `docs/specs/ajustes/US-ADJ-13.md` /
`US-ADJ-19.md`. Mismo bug explica por qué `LayerViolationsAnalyzer` nunca reporta nada: la
regla de capas (`entities → use_cases → interface_adapters → frameworks`) se sostiene por
revisión humana/asistida, no por ese chequeo automatizado, hasta que se resuelva upstream.

## Fuente de verdad

- Modelos ORM: `src/<bc>/frameworks/db/models.py` (Identidad, Banco de Preguntas),
  `src/actividad_evaluativa/frameworks/db/models.py` (event store).
- Motor/sesión compartidos: `src/shared/frameworks/db.py`.
- Historial de evolución del esquema: `migrations/versions/` (Alembic) — este documento
  describe el estado vigente, no repite el historial migración por migración.
