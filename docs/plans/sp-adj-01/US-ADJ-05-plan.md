# Plan de Implementación: US-ADJ-05 - Paginar el listado de cuentas

**Patrón:** Clean Architecture BC-first (backend, BC Identidad) + React 19/TypeScript/Vite (frontend)
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-22
**Tiempo real (tracker):** 62 min (Fases 0 a 8)

## Diferencia con US-ADJ-03 (verificado en Fase 2)

A diferencia de `PreguntaRepositoryPort.filtrar()` (reusado por 5 pantallas distintas),
`CuentaQueryPort.listar()` tiene **un único consumidor** a cada lado: `ListarCuentasUseCase`
(backend) y `Cuentas.tsx` vía `listarCuentas()` (frontend) — verificado por grep, sin otros
call-sites. No hace falta el diseño opt-in de `US-ADJ-03`: `pagina`/`tamanio_pagina` se
agregan con default fijo (`pagina=1`, `tamanio_pagina=20`) siempre aplicado, sin riesgo de
romper otro consumidor. Tampoco hace falta migración: `Usuario.creado_en` ya existe desde
`US-2.2.3`.

## Componentes a Implementar

### 1. Backend — Port y Gateway

- [x] `src/identidad/entities/ports/cuenta_query_port.py`
  - `listar()` agrega `pagina: int = 1`, `tamanio_pagina: int = 20`
  - Retorno cambia de `list[Usuario]` a `ResultadoPaginadoCuentas` (dataclass nuevo:
    `cuentas: list[Usuario]`, `total: int`) — nuevo archivo
    `src/identidad/entities/resultado_paginado_cuentas.py`
- [x] `src/identidad/interface_adapters/gateways/cuenta_query_repository.py`
  - `ORDER BY creado_en, id` (desempate estable)
  - `LIMIT`/`OFFSET` según `pagina`/`tamanio_pagina`
  - Query de `total` separada con los mismos filtros (sin `LIMIT`/`OFFSET`)

### 2. Backend — Use Case, Controller, Router

- [x] `src/identidad/use_cases/listar_cuentas.py`
  - `execute()` agrega `pagina: int = 1`, `tamanio_pagina: int = 20`, pasa ambos al puerto,
    retorna `ResultadoPaginadoCuentas`
- [x] `src/identidad/interface_adapters/controllers/cuentas_controller.py`
  - `listar_cuentas()` agrega `pagina`/`tamanio_pagina`, devuelve `ResultadoPaginadoCuentas`
- [x] `src/identidad/frameworks/api/schemas.py`
  - `CuentasPaginadasResponse` nuevo: `cuentas: list[CuentaResponse]`, `total: int`
- [x] `src/identidad/frameworks/api/cuentas_router.py`
  - Query params `pagina: int = 1`, `tamanio_pagina: int = 20`
  - `response_model=CuentasPaginadasResponse`

### 3. Frontend

- [x] `frontend/src/lib/cuentas-api.ts`
  - `listarCuentas()` acepta `pagina?`/`tamanioPagina?` opcionales (default 1/20 igual que el
    backend), retorna `{ cuentas: CuentaResponse[]; total: number }`
- [x] `frontend/src/pages/Cuentas.tsx`
  - Estado `pagina` (reset a 1 al cambiar cualquier filtro)
  - Pasa `pagina`/`tamanioPagina=20` a `listarCuentas()`
  - Renderiza `<Pagination>` (ya existe, `US-ADJ-03`) debajo de la tabla con `total` de la
    respuesta — sin crear un componente nuevo

### 4. Ajuste de tests existentes

- [x] Tests backend de `listar_cuentas`/`cuentas_controller`/`cuentas_router` (unit +
  integración) — agregar casos de paginación (orden estable, `LIMIT`/`OFFSET`, página fuera
  de rango), ajustar los que asuman `list[Usuario]` plano
- [x] `Cuentas.test.tsx` — ajustar mocks de `fetch` a la nueva forma
  `{ cuentas, total }`, agregar casos de paginación (más de una página, cambiar de página,
  filtro reinicia paginación, una sola página)

**Estado:** 9/9 tareas completadas
