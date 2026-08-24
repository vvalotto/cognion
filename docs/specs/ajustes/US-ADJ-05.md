# US-ADJ-05: Paginar el listado de cuentas

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ-01` (misma iteración de ajuste que `US-ADJ-01`/`US-ADJ-03`)
**Tipo**: `feature backend + frontend`
**Agregado principal afectado**: — (consulta de solo lectura, sin cambios de Aggregate)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el listado de cuentas paginado, en vez de una sola tabla con todas las cuentas
que matchean los filtros**
para **poder navegarlo cuando el sistema tiene muchas cuentas registradas, sin que la
pantalla cargue y renderice todas de una vez**.

---

## Contexto del dominio

### Problema

`GET /usuarios` (`US-2.2.2`, `ListarCuentasUseCase` → `CuentaQueryPort.listar()`) devuelve
siempre la lista completa de cuentas que matchean los filtros (rol/estado/búsqueda), sin
límite. `Cuentas.tsx` (`US-2.2.6`) renderiza esa lista entera en una sola tabla — mismo
problema que motivó `US-ADJ-03` para el banco de preguntas, esta vez sobre el listado de
cuentas.

Pedido explícito de Víctor (2026-08-22): mismo criterio de paginación que `US-ADJ-03` —
página de tamaño fijo, orden estable, reset a página 1 al cambiar filtros, UI de números de
página + Anterior/Siguiente, reutilizando el mismo componente visual de paginación que
introduce `US-ADJ-03` (no duplicar la UI de controles).

### Modelo involucrado

A diferencia de `US-ADJ-03`, **no hace falta agregar ninguna columna ni migración**:
`Usuario.creado_en` ya existe (agregado en `US-2.2.3`) y sirve directamente como criterio de
orden estable — es la misma simplificación que ya evitó ese gap en `CuentaDetalle.tsx`.

`CuentaQueryPort.listar()` cambia de firma: agrega `pagina: int = 1`,
`tamanio_pagina: int = 20`, y el retorno pasa de `list[Usuario]` a una estructura con
`cuentas: list[Usuario]` + `total: int` (total de cuentas que matchean los filtros, sin
paginar).

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| (reutilizado) | `Usuario.creado_en` | Ya existe (`US-2.2.3`) — criterio de orden estable, sin migración |
| Value Object / DTO nuevo | `ResultadoPaginado` (o tupla `(cuentas, total)`) | Devuelve la página pedida junto con el total de resultados — mismo patrón que `US-ADJ-03` |
| Componente frontend reutilizado | `Pagination` (introducido por `US-ADJ-03`) | Controles de números de página + Anterior/Siguiente — no se duplica, se reusa |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.2.2` (`GET /usuarios` con filtros) y `US-2.2.6` (`Cuentas.tsx`) implementadas y
  mergeadas.
- `US-ADJ-03` implementada y mergeada — provee el componente `Pagination` que esta US reusa
  para no duplicar la UI de controles ni el criterio visual.

### Postcondicion

- `GET /usuarios` acepta `pagina` (default `1`) y `tamanio_pagina` (default `20`, fijo — no
  configurable desde el cliente en esta US) como query params opcionales, además de los
  filtros existentes (`rol`, `estado`, `busqueda`).
- La respuesta trae la página pedida (máximo 20 cuentas) ordenada por `creado_en` ascendente,
  más el `total` de cuentas que matchean los filtros (sin paginar).
- `Cuentas.tsx` muestra los mismos controles de paginación que `Banco.tsx` (`US-ADJ-03`),
  calculados a partir de `total` y el tamaño de página fijo.
- Cambiar cualquier filtro (rol, estado, búsqueda) vuelve la página a 1.
- Pedir una página fuera de rango devuelve lista vacía, no error — mismo criterio que
  `US-ADJ-03`.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio nuevas — la paginación es un detalle de la consulta, no una regla de negocio de `Usuario`. |

---

## Criterios de aceptacion

```gherkin
Feature: Paginación del listado de cuentas (US-ADJ-05)

  Scenario: Listado con más de una página de resultados
    Given más de 20 cuentas registradas que matchean los filtros activos
    When un Administrador abre el listado de cuentas
    Then ve las primeras 20 cuentas, ordenadas por fecha de creación
    And los controles de paginación muestran la cantidad de páginas correspondiente

  Scenario: Cambiar de página
    Given un Administrador viendo la página 1 de un listado con más de una página
    When hace clic en "Siguiente" (o en el número de página 2)
    Then ve las cuentas 21 a 40
    And el botón "Anterior" queda habilitado

  Scenario: Cambiar un filtro reinicia la paginación
    Given un Administrador viendo la página 2 filtrado por rol "Estudiante"
    When cambia el filtro de Estado
    Then vuelve a la página 1 con el nuevo filtro combinado aplicado

  Scenario: Listado con una sola página
    Given menos de 20 cuentas que matchean los filtros
    When un Administrador lo abre
    Then ve todas las cuentas sin controles de paginación (o con "Anterior"/"Siguiente" deshabilitados)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí — agrega una columna nueva o requiere migración.
- [x] No — `Usuario.creado_en` ya existe; sin cambio de contrato hacia otros BCs; reusa el
  componente `Pagination` ya introducido por `US-ADJ-03`.

**Capa(s) afectadas:**
- [x] Backend — `entities/ports/cuenta_query_port.py` (firma de `listar()`),
  `interface_adapters/gateways/cuenta_query_repository.py` (`ORDER BY creado_en, id`
  desempate estable, `LIMIT`/`OFFSET`, query de `total`), `use_cases/listar_cuentas.py`,
  `interface_adapters/controllers/cuentas_controller.py`,
  `frameworks/api/cuentas_router.py` (query params `pagina`/`tamanio_pagina`, schema de
  respuesta con `total`). Sin migración Alembic.
- [x] Frontend — `frontend/src/lib/cuentas-api.ts` (`FiltrosCuentas`/respuesta con `total`),
  `frontend/src/pages/Cuentas.tsx` (estado de página, reusa `Pagination` de `US-ADJ-03`,
  reset a página 1 al cambiar filtros).

---

## Fuente de verdad UX

`docs/design/ux/wireframes-cuentas-administracion.md` no contempla paginación — requiere
actualización análoga a la de `docs/design/ux/wireframes-banco-preguntas.md` en `US-ADJ-03`
(gate de diseño UX, `CLAUDE.md`), reusando el mismo diseño de controles (números de página +
"Anterior"/"Siguiente") ya acordado con Víctor para `US-ADJ-03`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/ports/cuenta_query_port.py` | `listar()` agrega `pagina`/`tamanio_pagina`, retorno con `total` |
| `src/identidad/interface_adapters/gateways/cuenta_query_repository.py` | `ORDER BY creado_en, id`, `LIMIT`/`OFFSET`, query de conteo |
| `src/identidad/use_cases/listar_cuentas.py` | Pasa `pagina`/`tamanio_pagina` al puerto |
| `src/identidad/interface_adapters/controllers/cuentas_controller.py` | Firma actualizada |
| `src/identidad/frameworks/api/cuentas_router.py` | Query params `pagina`/`tamanio_pagina`, `total` en la respuesta |
| `frontend/src/lib/cuentas-api.ts` | Tipos y llamada con `pagina`/`tamanio_pagina`, respuesta con `total` |
| `frontend/src/pages/Cuentas.tsx` | Estado de página, reusa `Pagination` (`US-ADJ-03`), reset a página 1 al cambiar filtros |
| `docs/design/ux/wireframes-cuentas-administracion.md` | Agregar sección de paginación (gate UX previo a Fase 3) |

---

## Referencias

- Relacionada con: `US-2.2.2` (`GET /usuarios`, endpoint que esta US extiende), `US-2.2.6`
  (`Cuentas.tsx`, pantalla que esta US extiende), `US-ADJ-03` (mismo patrón de paginación,
  aplicado antes al Banco de Preguntas — **dependencia**: implementar después de `US-ADJ-03`
  para reusar su componente `Pagination` en vez de duplicarlo), `US-ADJ-04` (mismo lenguaje
  visual de tags/cards en las mismas pantallas — coordinar si se implementan en el mismo
  ciclo para no tocar `Cuentas.tsx` dos veces)
- Candidatas: `SP-ADJ-01`, a implementar después de `US-ADJ-03`

---

*Basado en el template de `docs/specs/ajustes/US-ADJ-03.md`, adaptado a Identidad. US de
ajuste (`SP-ADJ-01`, `docs/plans/PLAN-CM.md` §12).*
