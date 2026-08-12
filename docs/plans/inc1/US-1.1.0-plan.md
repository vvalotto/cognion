# Plan de Implementación: US-1.1.0 - Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** Cognion — BC Identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-21

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (tiempos reales de ejecución del agente, no
comparables contra esfuerzo humano — ver nota PRIN-001 del skill `implement-us`).

| Fase | Tiempo real |
|---|---|
| 0 — Validación de Contexto | 1 min |
| 1 — Escenarios BDD | 1 min |
| 2 — Plan de Implementación | 8 min |
| 3 — Implementación | 30 min |
| 4 — Tests Unitarios | ~5 min |
| 5 — Tests de Integración | ~7 min |
| 6 — Validación BDD | ~7 min |
| 7 — Quality Gates | ~11 min |
| **Total (hasta cierre de Fase 7)** | **~72 min** |

## Lecciones Aprendidas

- ⚠️ `passlib` está sin mantenimiento desde 2020 y rompe con `bcrypt>=4.1` — usar `bcrypt`
  directo evita esa deuda desde el día uno en vez de heredarla del ADR original.
- ⚠️ SQLAlchemy no infiere el orden de inserción entre tablas relacionadas por FK cruda sin
  `relationship()` ORM — un flush intermedio es necesario y fácil de omitir sin un test
  end-to-end real.
- ⚠️ `pytest-bdd` 8.1.0 no soporta step functions `async def` — hay que envolver el cuerpo
  async con `asyncio.run()` explícito; el engine compartido necesita `NullPool` para tolerar
  múltiples event loops dentro del mismo proceso de test.
- 💡 Probar el flujo end-to-end contra Postgres real (curl manual + luego tests automatizados)
  antes de cerrar la Fase 3 detectó 2 bugs reales que ningún test unitario con fakes hubiera
  encontrado (orden de inserción, incompatibilidad de librerías).
- 💡 Revisar el plan en secciones agrupadas (en vez de archivo por archivo) mantuvo el ritmo
  sin perder control real sobre el diseño — validado por el usuario para esta US.

## Decisiones de esta US (registradas para no repetir la discusión)

- **Sin guard de rol todavía:** los 3 endpoints se implementan sin dependency de autorización JWT/RBAC — se agrega en `US-1.1.5` cuando exista el mecanismo real, sin tocar la lógica de negocio ya escrita aquí.
- **DB session compartida:** `src/shared/frameworks/db.py` centraliza engine async, `sessionmaker` y `Base` declarativa para todos los BC — evita duplicar pools de conexión por BC.
- **Perfil como entity subordinada:** `Docente`/`Administrador`/`Estudiante` son entidades propias (tabla propia, `id = usuario_id`), no un enum plano en `Usuario` — sienta la base para atributos propios de perfil en US futuras (ej. `Estudiante.comision_id` en `US-1.1.2`).
- **Bootstrap del primer Administrador:** script standalone `scripts/seed_admin.py` (no vía Alembic, no vía esta US ejecutada por un usuario) — documentado en ADR corto.

## Fase 5 — Tests de Integración (contra Postgres local real)

- Convención acordada: misma DB local (`cognion`) que desarrollo, limpieza de tablas de
  Identidad vía fixture `autouse` en `tests/integration/conftest.py` (no DB de test separada).
- `tests/integration/inc1/test_usuario_repository_integration.py` — 3 tests, `SQLAlchemyUsuarioRepository`
- `tests/integration/inc1/test_comision_repository_integration.py` — 2 tests, `SQLAlchemyComisionRepository`
- `tests/integration/inc1/test_usuarios_api_integration.py` — 2 tests, `POST /usuarios` vía `httpx.AsyncClient`
- `tests/integration/inc1/test_comisiones_api_integration.py` — 2 tests, flujo completo `POST /comisiones` + `POST /comisiones/{id}/docentes`

**Bug real encontrado y corregido:** `asyncio_mode = "auto"` sin `loop_scope` explícito hacía
que cada test async corriera en un event loop nuevo, pero el engine de SQLAlchemy en
`src/shared/frameworks/db.py` es un singleton de módulo cuyo pool de conexiones `asyncpg` queda
atado al primer loop — rompía en el segundo test con `InterfaceError`/`RuntimeError` de loop
cruzado. Corregido fijando `asyncio_default_fixture_loop_scope = "session"` y
`asyncio_default_test_loop_scope = "session"` en `pyproject.toml` — coherente con que la app
real corre en un único event loop durante toda su vida. Afecta a toda la suite del proyecto,
no solo a esta US; verificado que `tests/unit/inc0/test_health.py` (Incremento 0) sigue en
verde tras el cambio.

También se corrigió un warning de deprecación de FastAPI/Starlette
(`HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`) descubierto al correr la
suite de integración.

**Resultado:** 29/29 tests pasan en toda la suite del proyecto (20 unitarios + 9 integración).

## Fase 6 — Validación BDD

`tests/step_defs/inc1/test_us_1_1_0_steps.py` implementa los 5 escenarios del feature de
Fase 1 contra los endpoints FastAPI reales (Postgres real, misma convención de limpieza de
Fase 5).

**Bugs reales encontrados y corregidos:**
1. El `.feature` declaraba `# language: es` pero usaba keywords Gherkin en inglés
   (`Feature`/`Scenario`/`Given`/...) — el parser de `pytest-bdd` es estricto y fallaba con
   "Multiple features are not allowed". Se quitó el pragma incorrecto (el texto de negocio ya
   estaba en español; solo las keywords estructurales son inglesas, uso estándar).
2. `pytest-bdd` 8.1.0 no soporta step functions `async def` — las ejecuta sin awaitear la
   corrutina (`RuntimeWarning: coroutine was never awaited`, el estado nunca se poblaba).
   Corregido: steps síncronos que corren su cuerpo async vía `asyncio.run()`.
3. Consecuencia del punto 2: cada `asyncio.run()` crea un event loop nuevo, y el engine
   compartido (pool por defecto) retenía conexiones `asyncpg` atadas al loop anterior →
   `RuntimeError: ... attached to a different loop`. Corregido cambiando el engine compartido
   a `poolclass=NullPool` (`ADR-018`, con el trade-off de producción documentado y confirmado
   con el usuario).
4. Bug propio en el step glue: el escenario "email duplicado" usaba un email hardcodeado
   distinto entre el `Given` y el `When`, por lo que nunca se probaba la colisión real.
   Corregido pasando el email por `context`.

**Resultado:** 5/5 escenarios BDD pasan. Suite completa del proyecto: 34/34 tests, sin warnings.

## Fase 7 — Quality Gates

Reporte: `quality/reports/inc1/US-1.1.0-quality.json` — **estado APROBADO**.

| Métrica | Resultado | Umbral |
|---|---|---|
| Pylint | 9.72/10 | ≥ 8.0 |
| CC máx/función | 6 | ≤ 10 |
| MI mínimo | 50.56 (grado A) | > 20 |
| Coverage (entities+use_cases+interface_adapters) | 100% | ≥ 95% |

Se creó `.pylintrc` (no existía) con `fail-under=8.0` y `disable=C0114,C0115,C0116` — corrige
falsos positivos de "missing docstring", consistente con la convención del proyecto de no
escribir docstrings salvo que aporten algo no obvio. Se corrigieron 6 líneas que superaban
100 caracteres. Se agregaron 4 tests de integración adicionales para cubrir ramas defensivas
de los gateways (IDs inexistentes, usuario huérfano sin perfil) — coverage pasó de 98% a 100%.

`codeguard -a full` sobre `src/identidad/` corrió en background (~158s) y reportó 269
hallazgos; solo 4 son reales (timeouts de mypy/pylint por presupuesto de tiempo), el resto son
herramientas no instaladas (vulture, codespell) o duplican pylint/radon ya evaluados
directamente.

## Componentes a Implementar

### 1. Entities (`src/identidad/entities/`)
- [x] `src/identidad/entities/usuario.py`
  - `Usuario` (aggregate): `id`, `nombre`, `email`, `password_hash`, `perfil` (una de las subordinadas)
  - `Docente`, `Administrador`, `Estudiante` (entities subordinadas, `id = usuario_id`)
- [x] `src/identidad/entities/comision.py`
  - `Comision` (aggregate): `id`, `materia`, `horario`, `administrador_id`, `docentes_asignados: list[UUID]`
- [x] `src/identidad/entities/eventos.py`
  - `UsuarioCreado`, `ComisionCreada`, `DocenteAsignado` (dataclasses frozen, `ocurrido_en`)
- [x] `src/identidad/entities/errors.py`
  - `EmailYaRegistrado`, `UsuarioNoEsDocente` (excepciones de dominio)
- [x] `src/identidad/entities/ports/password_hasher_port.py`
  - `PasswordHasherPort` (ABC): `hash(password) -> str`, `verificar(password, hash) -> bool`
- [x] `src/identidad/entities/ports/usuario_repository_port.py`
  - `UsuarioRepositoryPort` (ABC): `existe_email`, `guardar`, `obtener_por_id`
- [x] `src/identidad/entities/ports/comision_repository_port.py`
  - `ComisionRepositoryPort` (ABC): `guardar`, `obtener_por_id`, `actualizar`

### 2. Use Cases (`src/identidad/use_cases/`)
- [x] `src/identidad/use_cases/crear_usuario.py`
  - `CrearUsuarioUseCase.execute(nombre, email, password, perfil)` — valida INV-ID-04 (email único), hashea con `PasswordHasherPort` (INV-ID-06), persiste `Usuario` + perfil atómicamente (INV-ID-09), emite `UsuarioCreado`
- [x] `src/identidad/use_cases/crear_comision.py`
  - `CrearComisionUseCase.execute(materia, horario, administrador_id)` — persiste `Comision` con `docentes_asignados` vacío, emite `ComisionCreada`
- [x] `src/identidad/use_cases/asignar_docente_a_comision.py`
  - `AsignarDocenteAComisionUseCase.execute(comision_id, docente_id)` — valida que el `Usuario` referenciado tiene perfil `Docente` (si no, `UsuarioNoEsDocente`), valida existencia de la `Comision` (si no, `ComisionNoExiste` — agregada durante la implementación, no estaba en la spec original), agrega a `docentes_asignados`, emite `DocenteAsignado`

### 3. Interface Adapters (`src/identidad/interface_adapters/`)
- [x] `src/identidad/interface_adapters/controllers/usuarios_controller.py`
  - Orquesta `CrearUsuarioUseCase` desde el router, mapea excepciones de dominio
- [x] `src/identidad/interface_adapters/controllers/comisiones_controller.py`
  - Orquesta `CrearComisionUseCase` y `AsignarDocenteAComisionUseCase`
- [x] `src/identidad/interface_adapters/gateways/usuario_repository.py`
  - `SQLAlchemyUsuarioRepository(UsuarioRepositoryPort)`
- [x] `src/identidad/interface_adapters/gateways/comision_repository.py`
  - `SQLAlchemyComisionRepository(ComisionRepositoryPort)`

### 4. Frameworks (`src/identidad/frameworks/`)
- [x] `src/identidad/frameworks/security/password_hasher.py`
  - `BcryptPasswordHasher(PasswordHasherPort)` usando `bcrypt` directo (`ADR-014`) — **cambio respecto al plan original**: se descartó `passlib.CryptContext` por incompatibilidad real entre `passlib==1.7.4` (sin mantenimiento desde 2020) y `bcrypt>=4.1` (removió `__about__`, usado internamente por passlib). `ADR-014` ya permitía "bcrypt (o passlib[bcrypt])"; se actualizó `pyproject.toml` reemplazando `passlib[bcrypt]` por `bcrypt>=4.0.0`.
- [x] `src/identidad/frameworks/db/models.py`
  - Modelos SQLAlchemy: `UsuarioModel`, `DocenteModel`, `AdministradorModel`, `EstudianteModel`, `ComisionModel`, tabla asociativa `comision_docentes`
- [x] `src/identidad/frameworks/api/schemas.py`
  - Pydantic: `CrearUsuarioRequest/Response`, `CrearComisionRequest/Response`, `AsignarDocenteRequest` — `email` como `str` (no `EmailStr`: evita sumar dependencia `email-validator` no instalada; unicidad ya la valida INV-ID-04 en el dominio)
- [x] `src/identidad/frameworks/api/usuarios_router.py`
  - `POST /usuarios` (sin guard de rol todavía — ver decisiones)
- [x] `src/identidad/frameworks/api/comisiones_router.py`
  - `POST /comisiones`, `POST /comisiones/{comision_id}/docentes`
- [x] `src/identidad/frameworks/dependencies.py`
  - Dependency injection: repos, hasher, sesión de BD

### 5. Infraestructura compartida (`src/shared/frameworks/`)
- [x] `src/shared/frameworks/db.py`
  - Engine async (`asyncpg`), `async_sessionmaker`, `Base` declarativa, dependency `get_session()`

### 6. Migraciones y bootstrap
- [x] `migrations/env.py` — apuntar `target_metadata` a `Base.metadata` (importando `src.identidad.frameworks.db.models` para registrar las tablas)
- [x] `migrations/versions/0a0e4595d5cc_identidad_usuarios_y_comisiones.py` — crea `usuario`, `docente`, `administrador`, `estudiante`, `comision`, `comision_docentes` (autogenerada con Alembic y aplicada contra Postgres local)
- [x] `scripts/seed_admin.py` — crea el primer Administrador vía `CrearUsuarioUseCase`, credenciales por variables de entorno
- [x] `docs/adr/ADR-016-bootstrap-primer-administrador.md` — ADR corto documentando la decisión de seed/fixture
- [x] `docs/adr/ADR-017-db-session-compartida.md` — ADR corto documentando `src/shared/frameworks/db.py`

### 7. Integración
- [x] `src/app.py` — registrar `usuarios_router` y `comisiones_router`

## Bug encontrado y corregido durante la Fase 3

**`SQLAlchemyUsuarioRepository.guardar`** insertaba `UsuarioModel` y el modelo de perfil
(`AdministradorModel`/`DocenteModel`/`EstudianteModel`) en el mismo flush sin una
`relationship()` ORM declarada entre ambos — SQLAlchemy no infería el orden desde la FK cruda
y en la prueba end-to-end (`scripts/seed_admin.py` contra Postgres real) insertó el perfil
antes que el usuario, violando la foreign key. Corregido agregando un `await
self._session.flush()` intermedio entre ambos `add()`. Verificado con los 5 escenarios BDD
ejecutados vía `curl` contra un servidor `uvicorn` real + Postgres local — los 5 pasan.

**Estado:** 22/22 tareas completadas
