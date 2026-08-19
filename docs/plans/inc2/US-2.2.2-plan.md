# Plan de Implementación: US-2.2.2 - Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-19

## Métricas de Tiempo (tracking automático, tiempos de agente — ver PRIN-001 en `implement-us`)

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Contexto | 89s |
| Fase 1 — BDD | 145s |
| Fase 2 — Plan | 104s |
| Fase 3 — Implementación | 560s |
| Fase 4 — Tests unitarios | 162s |
| Fase 5 — Tests de integración | 89s |
| Fase 6 — Validación BDD | 94s |
| Fase 7 — Quality gates | 564s |
| **Total (hasta Fase 7)** | **~29 min** |

## Lecciones Aprendidas

- 💡 FastAPI permite que dos routers distintos (`usuarios_router.py`, `cuentas_router.py`)
  compartan el mismo `prefix` mientras el método+path no colisione — verificado vía el
  schema OpenAPI, no hace falta forzar un único router por resource.
- ⚠️ `coverage.py` no traza de forma confiable el cuerpo de un bucle `for` async inmediatamente
  posterior a un `await self._session.execute(...)` de SQLAlchemy — el código se ejecuta
  correctamente (verificado con una llamada real end-to-end) pero las líneas aparecen como no
  cubiertas. No perder tiempo intentando "cubrir" ese patrón con más tests — es un artefacto
  de instrumentación, no un gap real; documentarlo en el quality report y seguir.
- ✅ Separar `CuentasController` (queries administrativas) de `UsuariosController` (creación)
  aunque ambos operen sobre `Usuario` deja lugar para que `US-2.2.3`/`US-2.2.4` sumen métodos
  sin re-litigar la decisión de diseño.

## Componentes a Implementar

### 1. Puerto y Gateway
- [x] `src/identidad/entities/ports/usuario_repository_port.py`
  - Agregar método abstracto `listar(rol: TipoPerfil | None, estado: str | None, busqueda: str | None) -> list[Usuario]`
- [x] `src/identidad/interface_adapters/gateways/usuario_repository.py`
  - Implementado `listar()`: `SELECT` con `join()` a la tabla de perfil según `rol` (reutiliza
    `_MODEL_POR_PERFIL`), `bloqueada` según `estado` (`activa`→`False`, `bloqueada`→`True`),
    `ILIKE` (`or_`) contra `nombre`/`email` según `busqueda`; cada fila se resuelve con
    `_armar_usuario()` ya existente

### 2. Use Case
- [x] `src/identidad/use_cases/listar_cuentas.py`
  - `ListarCuentasUseCase` — delega directo en `repositorio.listar(...)`, sin lógica adicional

### 3. Interface Adapters
- [x] `src/identidad/interface_adapters/controllers/cuentas_controller.py`
  - `CuentasController` nuevo (no se reutiliza `UsuariosController`, que ya está dedicado a
    la creación de cuentas desde `US-1.1.0`/`US-1.1.9` — separación de responsabilidad
    command/query, consistente con el resto de specs de esta Iteración: `US-2.2.3`/`US-2.2.4`
    también suman métodos a este mismo `CuentasController`)
  - Método `listar_cuentas(rol, estado, busqueda) -> list[Usuario]`

### 4. Frameworks
- [x] `src/identidad/frameworks/api/schemas.py`
  - `CuentaResponse` nuevo (`id`, `nombre`, `email`, `perfil`, `bloqueada`) — distinto de
    `UsuarioResponse` (que no expone `bloqueada`, usado solo en la respuesta de alta)
- [x] `src/identidad/frameworks/api/cuentas_router.py`
  - `GET /usuarios?rol=&estado=&busqueda=` (rol `administrador`, reutiliza la dependency
    `require_administrador` ya existente en `dependencies.py`) — mismo path base `/usuarios`
    que `usuarios_router.py` (`POST /usuarios`), en un router distinto: verificado vía
    OpenAPI schema que ambos métodos conviven sin conflicto (`GET`/`POST` en `/usuarios`)
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_cuentas_controller(session)` — arma `CuentasController(ListarCuentasUseCase(repo))`
- [x] `src/app.py`
  - Registrado `cuentas_router` con `app.include_router(...)`

## Integración
- [x] `tests/unit/inc1/_fakes.py` — `FakeUsuarioRepository` gana `listar()` (nueva obligación
  del puerto)

**Estado:** 7/7 tareas completadas
