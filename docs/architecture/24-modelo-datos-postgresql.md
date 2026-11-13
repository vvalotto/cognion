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
| Analytics | Sin persistencia propia — calcula al consultar a partir de `events` y los read models de Actividad Evaluativa, y de los metadatos del Banco (`ADR-026`) | — |

Identidad y Banco de Preguntas resuelven su modelo como tablas con FKs, en el estilo
relacional tradicional. Actividad Evaluativa es distinto: no tiene una tabla por aggregate
(no existe `actividad_evaluativa` ni `evaluacion`) — tiene **una única tabla `events`**,
append-only, donde cada fila es un evento de dominio ya ocurrido. El aggregate se reconstruye
en memoria haciendo replay del stream (`aggregate_type` + `aggregate_id`), no se lee como fila.

## Propiedad de las tablas (14)

| Tabla | BC dueño | Quién escribe | Quién la lee de otro BC |
|---|---|---|---|
| `usuario`, `administrador`, `docente`, `estudiante` | Identidad | Identidad | Los demás BC, por los gateways de Identidad |
| `comision`, `comision_docentes` | Identidad | Identidad | Banco, Actividad Evaluativa, Analytics y Notificaciones, por gateways |
| `invitacion`, `token_recuperacion_password` | Identidad | Identidad | — |
| `materia`, `banco`, `pregunta_plantilla` | Banco de Preguntas | Banco | Identidad y Actividad Evaluativa (casos de uso y gateways); Analytics lee `pregunta_plantilla` por su modelo ORM (`ADR-026`) |
| `events` | Actividad Evaluativa | Solo `SQLAlchemyEventStore` (se agrega, nunca se modifica ni se borra) | Analytics (modelo ORM, `ADR-026`) |
| `ranking_por_sesion`, `distribucion_por_pregunta` | Actividad Evaluativa | Los casos de uso del modo en vivo, en la misma transacción que el evento | Analytics (`ranking_por_sesion`) |

Notificaciones y Analytics no tienen tablas. Hay 19 migraciones en `migrations/versions/`; `alembic downgrade base` funciona y hay una guarda que impide que vuelva a romperse (`US-8.3.4`).


## Cómo se sostiene el aislamiento entre BC sin frontera física

1. **FK real solo dentro del mismo BC.** Ejemplo: `pregunta_plantilla.banco_id` referencia
   `banco.id` (mismo BC, `banco_preguntas`) con `ForeignKey` real. En cambio
   `comision.materia_id` (Identidad) apunta a `materia` (Banco de Preguntas) — BC distinto —
   y **no tiene `ForeignKey` en el modelo ORM**: es un UUID plano, resuelto en tiempo de
   ejecución contra un puerto (`US-2.1.2`, refactor explícito para eliminar el import directo
   entre BCs).

2. **Comunicación cruzada = puertos in-process, no JOIN SQL entre BC.** Cuando un BC necesita datos de otro, llama a un puerto de su propio `entities/ports/`, implementado por un adaptador en `frameworks/adapters/` que conoce el otro BC. La lista completa de cruces, adaptador por adaptador, está en `20-context-map-integrations.md`. **Excepción** (`ADR-026`): solo Analytics puede leer los modelos ORM de otro BC (`EventoModel`, `RankingPorSesionModel`, `PreguntaPlantillaModel`), y solo en adaptadores de lectura; `import-linter` lo hace cumplir en el CI.

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
`US-ADJ-19.md`. Mismo bug explica por qué `LayerViolationsAnalyzer` nunca reporta nada: por eso la regla de capas y el aislamiento entre BC los hace cumplir **`import-linter`** en el CI (`uv run lint-imports`, Incremento 9), no ese chequeo.

## Fuente de verdad

- Modelos ORM: `src/<bc>/frameworks/db/models.py` (Identidad, Banco de Preguntas),
  `src/actividad_evaluativa/frameworks/db/models.py` (event store).
- Motor/sesión compartidos: `src/shared/frameworks/db.py`.
- Historial de evolución del esquema: `migrations/versions/` (Alembic) — este documento
  describe el estado vigente, no repite el historial migración por migración.
