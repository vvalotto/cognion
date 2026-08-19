# Plan de Implementación: US-2.2.3 - Administrador ve el detalle de una cuenta

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-19

## Métricas de Tiempo (tracking automático, tiempos de agente — ver PRIN-001 en `implement-us`)

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Contexto | 102s |
| Fase 1 — BDD | 55s |
| Fase 2 — Plan | 85s |
| Fase 3 — Implementación | 493s |
| Fase 4 — Tests unitarios | 102s |
| Fase 5 — Tests de integración | 355s |
| Fase 6 — Validación BDD | 86s |
| Fase 7 — Quality gates | 154s |
| **Total (hasta Fase 7)** | **~24 min** |

## Lecciones Aprendidas

- ✅ El pre-push gate no repitió el CBO CRITICAL de `US-2.2.2`: sumar un segundo método a
  `CuentasController` (1→2, lejos del umbral) y reutilizar `SQLAlchemyUsuarioRepository.
  obtener_por_id()` ya existente (en vez de acoplar tipos nuevos al gateway) evitó el mismo
  problema — confirma que la lección de `US-2.2.2` (separar por responsabilidad *antes* de
  que el CBO se dispare) aplicó correctamente acá.
- ⚠️ Agregar un campo nuevo (`creado_en`, `nullable=False`) a un modelo SQLAlchemy rompe
  cualquier test de integración que construya esa entidad ORM directamente (sin pasar por
  `Usuario.crear()`/`repo.guardar()`) — se detectó en
  `test_usuario_repository_integration.py::test_obtener_por_id_con_usuario_sin_perfil_retorna_none`,
  que instanciaba `UsuarioModel(...)` a mano para simular una fila huérfana. Revisar tests que
  construyen modelos ORM directamente cada vez que se agrega una columna `nullable=False`.
- 💡 Fijar `creado_en` en la propia entidad de dominio (`default_factory` en el dataclass,
  no solo `server_default` en la columna) mantiene la entidad y la fila consistentes sin
  depender del reloj de la base — el `server_default=func.now()` de la migración es solo
  para el backfill de filas preexistentes.

## Componentes a Implementar

### 1. Entities
- [x] `src/identidad/entities/usuario.py`
  - Agregar `creado_en: datetime` con `field(default_factory=_ahora)` (helper local, mismo
    patrón que `eventos.py`) — se fija en el momento de construir el `Usuario` (`crear()`/
    `crear_estudiante()`), no solo en la base
- [x] `src/identidad/entities/errors.py`
  - Agregar `UsuarioNoExiste(usuario_id: UUID)`

### 2. Use Case
- [x] `src/identidad/use_cases/obtener_cuenta.py`
  - `ObtenerCuentaUseCase` — recibe `UsuarioRepositoryPort`, `execute(usuario_id)` llama
    `obtener_por_id()` (ya existente) y lanza `UsuarioNoExiste` si es `None`; devuelve el
    `Usuario` completo (el `comision_id` ya viaja en `usuario.perfil` si es `Estudiante`, la
    respuesta lo extrae en el router, mismo patrón que `listar_cuentas`)

### 3. Interface Adapters
- [x] `src/identidad/interface_adapters/controllers/cuentas_controller.py`
  - Segundo use case inyectado: `obtener_cuenta: ObtenerCuentaUseCase`
  - Método nuevo `obtener_cuenta(usuario_id) -> Usuario`

### 4. Frameworks
- [x] `src/identidad/frameworks/api/schemas.py`
  - `CuentaDetalleResponse` nuevo (`id`, `nombre`, `email`, `perfil`, `bloqueada`,
    `creado_en`, `comision_id: UUID | None`) — distinto de `CuentaResponse` (listado, sin
    `creado_en`/`comision_id`)
- [x] `src/identidad/frameworks/api/cuentas_router.py`
  - `GET /usuarios/{usuario_id}` (rol `administrador`) — 404 si `UsuarioNoExiste`; arma
    `comision_id` con `usuario.perfil.comision_id if isinstance(usuario.perfil, Estudiante)
    else None`
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_cuentas_controller` arma también `ObtenerCuentaUseCase(usuario_repo)` (reutiliza
    `SQLAlchemyUsuarioRepository`, no `CuentaQueryPort` — `obtener_por_id` ya vive ahí)
- [x] `src/identidad/frameworks/db/models.py`
  - `UsuarioModel`: columna `creado_en: Mapped[datetime]` (`DateTime(timezone=True)`)
- [x] Migración Alembic nueva (`migrations/versions/`)
  - `add_column` de `creado_en` en `usuario`, `nullable=False` con `server_default=func.now()`
    (backfill: todas las filas existentes quedan con el timestamp único de la migración,
    decisión de Víctor confirmada en esta sesión)
- [x] `src/identidad/interface_adapters/gateways/usuario_repository.py`
  - `guardar()`: pasar `creado_en=usuario.creado_en` explícito al construir `UsuarioModel`
    (no depender solo del `server_default`, para que entidad y fila queden consistentes)
  - `_armar_usuario()`: hidratar `creado_en=usuario_model.creado_en`

## Integración
- [x] Ningún test double nuevo que actualizar — `FakeUsuarioRepository`/
  `FakeCuentaQueryRepository` en `tests/unit/inc1/_fakes.py` no necesitan cambios (el puerto
  no gana métodos nuevos, `Usuario.crear()` ya fija `creado_en` por su cuenta)

**Estado:** 8/8 tareas completadas
