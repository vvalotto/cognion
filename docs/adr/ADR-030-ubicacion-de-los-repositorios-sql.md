# ADR-030 — Los repositorios SQL viven en `frameworks/repositories/`

**Estado:** Aceptado
**Fecha:** 2026-11-25
**Origen:** Issue [#667](https://github.com/vvalotto/cognion/issues/667), hallazgo `CA-01` de la revisión de diseño (`docs/revision-diseno-2026-11/`); decidido con Víctor en la Iteración 2 del Incremento 12. Relacionado con `ADR-006` (integración entre BC), `ADR-017` (sesión de base compartida) y `ADR-026` (acoplamiento entre BC por datos). Lo implementa `US-12.2.3` (Issue [#670](https://github.com/vvalotto/cognion/issues/670)).

---

## Contexto

La pregunta "¿dónde va un repositorio SQL?" tiene hoy **tres respuestas**:

| Dónde | Qué hay |
|---|---|
| Identidad y Banco de Preguntas | `interface_adapters/gateways/`: 11 archivos, 10 de los cuales importan los modelos ORM de `frameworks/db/models.py` |
| Actividad Evaluativa | `frameworks/adapters/`: 7 archivos `*_repository.py`, mezclados con los adaptadores entre contextos (`*_port_in_process.py`) y el de SMTP; el event store está aparte, en `frameworks/event_store/` |
| El perfil de `/implement-us` (`clean-architecture-bc.json`) | `frameworks/repositories/` para un `Repository` y `interface_adapters/gateways/` para un `Gateway`. **La carpeta `frameworks/repositories/` no existe en ningún contexto**, y la fase 3 de la skill dice "Repositories / Gateways (`frameworks/`)" |

La primera obliga a una excepción en el contrato de capas de `import-linter`: `"src.*.interface_adapters.gateways.** -> src.*.frameworks.db.models"`. Una capa interna depende de una externa, que es lo que la regla prohíbe.

Hay además una tensión que el informe no registró. El contrato de aislamiento entre contextos dice que **solo `frameworks/adapters/` puede importar de otro contexto** (`ADR-006`). Si los repositorios van a esa carpeta, comparten el permiso con los adaptadores entre contextos y un repositorio podría importar de otro contexto sin que nada falle. Hoy ninguno de los 7 de Actividad Evaluativa lo hace, pero nada lo impide.

Medición del 2026-11-25 de lo que costaría mover:

| Qué | Archivos | Imports en `src` | Archivos de test que los importan |
|---|---|---|---|
| Repositorios de Identidad y Banco (`interface_adapters/gateways/`) | 11 | 27 (25 desde `frameworks/` de varios contextos —también de Actividad Evaluativa, Analytics y Notificaciones— y 2 entre ellos) | 87 |
| Repositorios de Actividad Evaluativa (`frameworks/adapters/*_repository.py`) | 7 | 7 | 11 |

## Opciones Consideradas

| Opción | Qué es | Costo y riesgo |
|---|---|---|
| **A1. Identidad y Banco a `frameworks/adapters/`** | Como ya hacen Actividad Evaluativa y Analytics; es lo que recomienda el informe | 11 archivos, 27 imports, ~87 tests. No toca Actividad Evaluativa. Los repositorios siguen junto a los adaptadores entre contextos, sin la protección del contrato, y el perfil de `/implement-us` queda inconsistente |
| **A2. Todos los repositorios a `frameworks/repositories/`** | La convención que el perfil ya declara, para los 18 | 18 archivos, 34 imports, ~98 tests; todo es cambio de ruta |
| **B. Aceptar la excepción** | Un gateway SQL puede conocer su ORM; no se mueve nada | Costo cero, pero quedan tres convenciones y la excepción en el contrato para siempre |
| **C. Mover los modelos ORM a `interface_adapters/`** | Para que los gateways no crucen la capa | Descartada: un modelo ORM es del framework, no de un adaptador de interfaz |

## Decisión

**Todo repositorio SQL (el que implementa un puerto de persistencia con SQLAlchemy y conoce los modelos ORM) vive en `src/<bc>/frameworks/repositories/`. En `frameworks/adapters/` quedan solo los adaptadores entre contextos (`*_port_in_process`) y los de infraestructura (SMTP); el event store sigue en `frameworks/event_store/`. `interface_adapters/` deja de tener gateways SQL.**

## Justificación

- **Una sola regla** para toda la base de código, que además coincide con lo que el perfil de `/implement-us` ya escribió. Hoy cada contexto responde distinto según cuándo se escribió.
- **Borra la excepción del contrato de capas** en vez de normalizarla: el criterio de salida de la iteración es que el contrato no tenga `ignore_imports`.
- **Mantiene útil el contrato entre contextos:** con los repositorios fuera de `frameworks/adapters/`, esa carpeta contiene solo lo que sí debe cruzar contextos. Se agrega un contrato que prohíbe a `frameworks/repositories/` importar de otro contexto, que hoy ya se cumple.
- **Se descarta A1** porque deja a los repositorios bajo el permiso de cruzar contextos y la convención del perfil sin cumplir; ahorra tocar Actividad Evaluativa, pero esos 7 archivos solo cambian de ruta. **Se descarta B** por dejar tres convenciones y la excepción para siempre. **Se descarta C** por llevar un detalle del framework a una capa interna.
- **El riesgo es bajo:** son cambios de ruta sin tocar lógica, y los 2544 tests, Playwright e `import-linter` los protegen.

## Impacto en Configuración

- `pyproject.toml`: se borra `"src.*.interface_adapters.gateways.** -> src.*.frameworks.db.models"` de `ignore_imports` del contrato de capas, y se agrega un contrato que prohíbe a `src.*.frameworks.repositories` importar de otro contexto.
- `src/identidad/` y `src/banco_preguntas/`: `interface_adapters/gateways/*` pasa a `frameworks/repositories/` (con `git mv`, para conservar el historial), incluido el auxiliar `email_unico.py`. `src/actividad_evaluativa/`: los 7 `*_repository.py` de `frameworks/adapters/` pasan a `frameworks/repositories/`.
- Los imports en `src` (34) y en los tests (unos 98 archivos) se actualizan a las rutas nuevas.
- `.claude/skills/implement-us/customizations/clean-architecture-bc.json` y `phases/phase-3-implementation.md`: el repositorio va en `frameworks/repositories/` y no se menciona un gateway SQL en `interface_adapters/`.
- `tests/unit/inc12/test_guardas_con_excepciones.py`: `GATEWAYS_QUE_IMPORTAN_MODELOS` pasa a la lista vacía y la excepción de capas de `IGNORE_IMPORTS_POR_CONTRATO` desaparece.
- `CLAUDE.md` (la excepción de los gateways de la regla de capas), `docs/architecture/` (`03-bounded-contexts.md`, `10`, `11`, `12`, `20-context-map-integrations.md`, `50-development-view.md`) y los `docs/design/domain/`.
- **Orden:** `US-12.2.3` va después de `US-12.2.1`, que cambia los `commit()` de esos mismos repositorios por `flush()` (`ADR-028`): conviene hacer ese cambio en la ruta vieja y mover después.

## Consecuencias

- ✅ Una sola respuesta a "¿dónde va un repositorio?", y el perfil de `/implement-us` deja de contradecir al código.
- ✅ El contrato de capas queda sin excepciones y una capa interna deja de depender de una externa.
- ✅ El permiso de importar de otro contexto queda acotado a `frameworks/adapters/`, y los repositorios no lo tienen.
- ⚠️ **Es un cambio grande en cantidad de archivos** (18 movidos, 34 imports y unos 98 archivos de test), aunque mecánico. Se hace en un solo PR para no dejar el repositorio a medias, y no conviene tener otras ramas abiertas que toquen esos archivos.
- ⚠️ **Toca Actividad Evaluativa solo en la ruta de 7 archivos**: su lógica no cambia, pero es el contexto de tiempo real, así que la corrida completa de Playwright es obligatoria antes de mergear.
- ⚠️ El relevamiento del `ADR-026` cita rutas viejas (`interface_adapters/gateways`); no se reescribe, porque es histórico, pero esta decisión lo supera en cuanto a esas rutas.
- ⚠️ Los `*_query_repository.py` de solo lectura y los repositorios de escritura van juntos en la misma carpeta; si más adelante conviene separarlos (consultas y comandos), es otra decisión.
