# US-ADJ-03: Paginar el listado del banco de preguntas

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ` (sin incremento asignado todavía — ver UAT de carga masiva de
contenido real, 2026-08-18)
**Tipo**: `feature backend + frontend`
**Agregado principal afectado**: `PreguntaPlantillaOpcionMultiple` / `PreguntaPlantillaVerdaderoFalso`
(agrega el atributo `fecha_creacion`, sin invariantes nuevas)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver el banco de preguntas de una materia paginado, en vez de una sola tabla con todas
las preguntas activas**
para **poder navegarlo cuando la materia tiene decenas o cientos de preguntas, sin que la
pantalla cargue y renderice todo de una vez**.

---

## Contexto del dominio

### Problema

Detectado en UAT manual (2026-08-18) al cargar un banco real de 70 preguntas para la materia
"Ingeniería de Software": `GET /bancos/{id}/preguntas` (`US-2.1.7`) devuelve siempre la lista
completa de preguntas activas que matchean los filtros, sin límite. `Banco.tsx` (`US-2.1.10`)
renderiza esa lista entera en una sola tabla. Con bancos de ese tamaño (o mayores, a medida que
se cargan los contenidos reales de la materia) la tabla se vuelve difícil de recorrer.

Decisión de Víctor (2026-08-18): paginar del lado del backend, tamaño de página fijo de 20,
orden estable por fecha de creación (columna nueva, no existe hoy en `pregunta_plantilla`), la
página vuelve a 1 cada vez que cambia algún filtro, UI de números de página + Anterior/Siguiente.

### Modelo involucrado

Agrega `fecha_creacion: datetime` a `PreguntaPlantillaOpcionMultiple` y
`PreguntaPlantillaVerdaderoFalso` — se fija una única vez al crear la pregunta (en
`CargarPreguntaOpcionMultipleUseCase`/`CargarPreguntaVerdaderoFalsoUseCase`), inmutable en
`editar()`. Es el criterio de orden estable para la paginación; no participa de ninguna
invariante de negocio.

`PreguntaRepositoryPort.filtrar()` cambia de firma: agrega `pagina: int = 1`,
`tamanio_pagina: int = 20`, y el retorno pasa de `list[...]` a una estructura con
`preguntas: list[...]` + `total: int` (total de preguntas activas que matchean los filtros,
sin paginar — necesario para calcular la cantidad de páginas en el frontend).

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Atributo nuevo | `PreguntaPlantilla*.fecha_creacion` | Timestamp de alta, fijado una sola vez, usado como criterio de orden estable de paginación |
| Value Object / DTO nuevo | `ResultadoPaginado` (o tupla `(preguntas, total)`) | Devuelve la página pedida junto con el total de resultados que matchean los filtros |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.7` (`GET /bancos/{id}/preguntas` con filtros) y `US-2.1.10` (`Banco.tsx`)
  implementadas y mergeadas.
- Banco con más de 20 preguntas activas para poder verificar más de una página (el banco
  cargado en UAT del 2026-08-18 sirve como fixture real: 71 preguntas).

### Postcondicion

- `GET /bancos/{id}/preguntas` acepta `pagina` (default `1`) y `tamanio_pagina` (default `20`,
  fijo — no configurable desde el cliente en esta US) como query params opcionales, además de
  los filtros existentes (`unidad`, `tema`, `dificultad`, `importancia`).
- La respuesta trae la página pedida (máximo 20 preguntas) ordenada por `fecha_creacion`
  ascendente, más el `total` de preguntas activas que matchean los filtros (sin paginar).
- `Banco.tsx` muestra controles de paginación (números de página + "Anterior"/"Siguiente")
  debajo de la tabla, calculados a partir de `total` y el tamaño de página fijo.
- Cambiar cualquier filtro (unidad, tema, dificultad, importancia) vuelve la página a 1.
- Pedir una página fuera de rango (p. ej. `pagina=99` con solo 4 páginas de resultados)
  devuelve lista vacía, no error — mismo criterio de "sin resultados" que ya usa el filtrado.
- Las preguntas cargadas antes de esta US (sin `fecha_creacion` real) se migran con backfill —
  ver "Impacto arquitectónico".

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio nuevas — `fecha_creacion` es metadata de auditoría/orden, no una regla de negocio de `PreguntaPlantilla`. |

---

## Criterios de aceptacion

```gherkin
Feature: Paginación del banco de preguntas (US-ADJ-03)

  Scenario: Banco con más de una página de resultados
    Given un banco con 71 preguntas activas y tamaño de página 20
    When un Docente abre el banco de esa materia
    Then ve las primeras 20 preguntas, ordenadas por fecha de creación
    And los controles de paginación muestran 4 páginas y el botón "Siguiente" habilitado

  Scenario: Cambiar de página
    Given un Docente viendo la página 1 de un banco con 4 páginas
    When hace clic en "Siguiente" (o en el número de página 2)
    Then ve las preguntas 21 a 40
    And el botón "Anterior" queda habilitado

  Scenario: Cambiar un filtro reinicia la paginación
    Given un Docente viendo la página 3 de un banco filtrado por "Unidad 2"
    When cambia el filtro de Dificultad
    Then vuelve a la página 1 con el nuevo filtro combinado aplicado

  Scenario: Banco con una sola página
    Given un banco con 5 preguntas activas
    When un Docente lo abre
    Then ve las 5 preguntas sin controles de paginación (o con "Anterior"/"Siguiente" deshabilitados)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — agrega una columna nueva a `pregunta_plantilla` (`fecha_creacion`), lo que requiere
  migración Alembic con backfill. Decisión de Víctor (2026-08-18): las preguntas existentes se
  completan con el timestamp de la migración, igual para todas — el orden relativo entre ellas
  dentro de una misma página queda indefinido (desempate estable adicional por `id` en el
  `ORDER BY` del gateway para que la paginación no repita ni salte filas en ese subconjunto).
  No amerita ADR nuevo — es una extensión de un Aggregate existente, no un cambio de estilo
  arquitectónico.
- [ ] No requiere cambio de contrato hacia otros BCs — el endpoint sigue siendo consumido solo
  por el frontend.

**Capa(s) afectadas:**
- [x] Backend — `entities/pregunta_plantilla.py` (atributo nuevo),
  `entities/ports/pregunta_repository_port.py` (firma de `filtrar()`),
  `interface_adapters/gateways/pregunta_repository.py` (`ORDER BY fecha_creacion`, `LIMIT`/
  `OFFSET`, query de `total`), `use_cases/filtrar_banco.py`,
  `use_cases/cargar_pregunta_opcion_multiple.py`/`cargar_pregunta_verdadero_falso.py` (fijar
  `fecha_creacion` al crear), `interface_adapters/controllers/bancos_controller.py` (query
  params `pagina`/`tamanio_pagina`, schema de respuesta con `total`), migración Alembic nueva.
- [x] Frontend — `frontend/src/lib/banco-preguntas-api.ts` (`FiltrosBanco`/respuesta con
  `total`), `frontend/src/pages/Banco.tsx` (estado de página, controles de paginación,
  reset a página 1 al cambiar filtros).

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` no contempla paginación — requiere actualización
antes de tocar `frontend/` (gate de diseño UX, `CLAUDE.md`). Diseño acordado con Víctor
(2026-08-18): números de página + "Anterior"/"Siguiente" debajo de la tabla, mismo lenguaje
visual que el resto de los controles del banco (`US-ADJ-01`). Pendiente: agregar la sección
correspondiente al wireframe antes de iniciar la Fase 3 de `/implement-us`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/pregunta_plantilla.py` | Atributo `fecha_creacion: datetime` en ambos aggregates |
| `src/banco_preguntas/entities/ports/pregunta_repository_port.py` | `filtrar()` agrega `pagina`/`tamanio_pagina`, retorno con `total` |
| `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` | `ORDER BY fecha_creacion, id` (desempate estable), `LIMIT`/`OFFSET`, query de conteo |
| `src/banco_preguntas/use_cases/filtrar_banco.py` | Pasa `pagina`/`tamanio_pagina` al puerto |
| `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py` | Fija `fecha_creacion` al crear |
| `src/banco_preguntas/use_cases/cargar_pregunta_verdadero_falso.py` | Fija `fecha_creacion` al crear |
| `src/banco_preguntas/interface_adapters/controllers/bancos_controller.py` | Query params `pagina`/`tamanio_pagina`, `total` en la respuesta |
| `src/shared/frameworks/db/migrations/` (nuevo) | Migración Alembic: columna `fecha_creacion` + backfill |
| `frontend/src/lib/banco-preguntas-api.ts` | Tipos y llamada con `pagina`/`tamanio_pagina`, respuesta con `total` |
| `frontend/src/pages/Banco.tsx` | Estado de página, controles de paginación, reset a página 1 al cambiar filtros |
| `docs/design/ux/wireframes-banco-preguntas.md` | Agregar sección de paginación (gate UX previo a Fase 3) |

---

## Referencias

- Relacionada con: `US-2.1.7` (`GET /bancos/{id}/preguntas`, endpoint que esta US extiende),
  `US-2.1.10` (`Banco.tsx`, pantalla que esta US extiende), `US-ADJ-01` (mismo lenguaje visual
  de controles), carga masiva de contenido real de "Ingeniería de Software" (UAT 2026-08-18,
  71 preguntas — motivó el hallazgo)
- Candidatas: sin incremento asignado — a decidir junto con `US-ADJ-01`/`US-ADJ-02`

---

*Basado en el template de `docs/specs/inc2/US-2.1.13.md` — adaptado a capas
`entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`). US de ajuste (`SP-ADJ`,
`docs/plans/PLAN-CM.md` §12) — sin Issue de GitHub ni branch hasta que se decida el incremento
de implementación.*
