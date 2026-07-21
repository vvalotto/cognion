# Reporte de Implementación: US-1.1.0

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.0 - Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes
- **Puntos estimados:** 5
- **Tiempo real:** ~72 min (tracking de ejecución del agente, no comparable contra esfuerzo humano — ver nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-07-21

Primera US ejecutada de la Iteración 1 (BC Identidad) — precondición del resto de la
iteración: sin `Usuario` con perfil `Docente` ni `Comisión` con al menos un Docente asignado,
no hay forma de generar invitaciones (`US-1.1.1`) ni de probar el registro de punta a punta.

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `usuario.py` — aggregate `Usuario` + entities subordinadas `Docente`/`Administrador`/`Estudiante` (perfil creado atómicamente vía `Usuario.crear`, INV-ID-09)
- ✅ `comision.py` — aggregate `Comision`
- ✅ `eventos.py` — `UsuarioCreado`, `ComisionCreada`, `DocenteAsignado`
- ✅ `errors.py` — `EmailYaRegistrado`, `UsuarioNoEsDocente`, `ComisionNoExiste`
- ✅ `ports/password_hasher_port.py`, `usuario_repository_port.py`, `comision_repository_port.py`

### Use Cases (`src/identidad/use_cases/`)
- ✅ `CrearUsuarioUseCase` — valida INV-ID-04 (email único), hashea con `PasswordHasherPort` (INV-ID-06), emite `UsuarioCreado`
- ✅ `CrearComisionUseCase` — persiste `Comision` con `docentes_asignados` vacío, emite `ComisionCreada`
- ✅ `AsignarDocenteAComisionUseCase` — valida perfil `Docente` (INV-ID-08 vía `UsuarioNoEsDocente`) y existencia de la comisión, emite `DocenteAsignado`

### Interface Adapters (`src/identidad/interface_adapters/`)
- ✅ `controllers/usuarios_controller.py`, `comisiones_controller.py`
- ✅ `gateways/usuario_repository.py`, `comision_repository.py` — implementación SQLAlchemy de los ports

### Frameworks (`src/identidad/frameworks/`)
- ✅ `security/password_hasher.py` — `BcryptPasswordHasher` con `bcrypt` directo (`ADR-014`)
- ✅ `db/models.py` — modelos SQLAlchemy `UsuarioModel`, `DocenteModel`, `AdministradorModel`, `EstudianteModel`, `ComisionModel`, tabla asociativa `comision_docentes`
- ✅ `api/schemas.py`, `api/usuarios_router.py`, `api/comisiones_router.py`
- ✅ `dependencies.py` — dependency injection de repos/hasher/sesión

### Infraestructura compartida
- ✅ `src/shared/frameworks/db.py` — engine async (`NullPool`, `ADR-018`), `SessionLocal`, `get_session()` (`ADR-017`)

### Migraciones y bootstrap
- ✅ `migrations/env.py` — `target_metadata` apunta a `Base.metadata`
- ✅ `migrations/versions/0a0e4595d5cc_identidad_usuarios_y_comisiones.py` — aplicada contra Postgres local
- ✅ `scripts/seed_admin.py` — bootstrap del primer Administrador (`ADR-016`)

### Integración
- ✅ `src/app.py` — routers de `usuarios` y `comisiones` registrados

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/usuarios` | Crear Usuario (perfil Docente/Administrador/Estudiante) | ⚠️ Pendiente — sin guard todavía, se agrega en `US-1.1.5` |
| POST | `/comisiones` | Crear Comisión | ⚠️ Pendiente — ídem |
| POST | `/comisiones/{comision_id}/docentes` | Asignar Docente a Comisión | ⚠️ Pendiente — ídem |

**OpenAPI Docs:** `/docs`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.72/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 6 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 50.56 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc1/US-1.1.0-quality.json`. Coverage medido sobre
`entities`/`use_cases`/`interface_adapters` — `frameworks/` excluido del gate por convención
del proyecto (`pyproject.toml`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (20 tests) — `tests/unit/inc1/`
- `test_usuario.py`, `test_comision.py` — entities (4 + 3 tests)
- `test_crear_usuario_use_case.py`, `test_crear_comision_use_case.py`, `test_asignar_docente_a_comision_use_case.py` — use cases con fakes de los ports (2 + 1 + 3 tests)
- `test_usuarios_controller.py`, `test_comisiones_controller.py` — controllers (1 + 2 tests)
- `test_password_hasher.py` — hasher bcrypt (3 tests)

### Tests de Integración (11 tests) — `tests/integration/inc1/`
- `test_usuario_repository_integration.py` (4 tests), `test_comision_repository_integration.py` (4 tests) — gateways SQLAlchemy contra Postgres local real
- `test_usuarios_api_integration.py` (2 tests), `test_comisiones_api_integration.py` (2 tests) — endpoints FastAPI vía `httpx.AsyncClient`

### Escenarios BDD (5 escenarios) — `tests/features/inc1/US-1.1.0-*.feature` + `tests/step_defs/inc1/`
- Administrador crea un Docente
- Alta rechazada por email duplicado
- Administrador crea una Comisión
- Administrador asigna un Docente a una Comisión
- Rechazo al asignar un Usuario que no es Docente

**Todos los tests pasando:** ✅ 37/37 (suite completa del proyecto, incluyendo Incremento 0)

---

## Migraciones de Base de Datos

- ✅ `migrations/versions/0a0e4595d5cc_identidad_usuarios_y_comisiones.py`
  - Tablas: `usuario`, `docente`, `administrador`, `estudiante`, `comision`, `comision_docentes`
  - Aplicada contra PostgreSQL local (`alembic upgrade head`)

---

## Bugs Reales Encontrados y Corregidos

1. **`passlib` incompatible con `bcrypt>=4.1`** (sin mantenimiento desde 2020) — reemplazado por `bcrypt` directo. `pyproject.toml` actualizado.
2. **Orden de inserción `Usuario`/perfil sin `relationship()` ORM** violaba la FK en pruebas end-to-end reales — corregido con `flush()` intermedio en `SQLAlchemyUsuarioRepository`.
3. **`pytest-asyncio` sin `loop_scope` explícito** rompía el engine compartido entre tests con distintos event loops — fijado a `session` scope en `pyproject.toml` (afecta a toda la suite, no solo a esta US).
4. **`.feature` con `# language: es` pero keywords en inglés** — `pytest-bdd` fallaba el parseo; se quitó el pragma incorrecto.
5. **`pytest-bdd` 8.1.0 no soporta step functions `async def`** — steps reescritos como funciones síncronas que ejecutan su cuerpo async vía `asyncio.run()`; el engine compartido pasó a `NullPool` (`ADR-018`) para tolerar múltiples event loops en el mismo proceso.
6. **Bug propio en step glue BDD**: el escenario de email duplicado usaba un email hardcodeado distinto entre `Given` y `When` — nunca probaba la colisión real. Corregido pasando el valor por `context`.

---

## Decisiones Arquitectónicas Registradas

- `ADR-016` — Bootstrap del primer Administrador vía script standalone (`scripts/seed_admin.py`)
- `ADR-017` — Engine y sesión async de SQLAlchemy compartidos en `src/shared/frameworks/db.py`
- `ADR-018` — `NullPool` en el engine de SQLAlchemy (afecta también a producción — trade-off aceptado a la escala del proyecto)

---

## Archivos Creados/Modificados

**Producción:** `src/identidad/entities/**`, `src/identidad/use_cases/**`,
`src/identidad/interface_adapters/**`, `src/identidad/frameworks/**`,
`src/shared/frameworks/db.py`, `src/app.py`, `scripts/seed_admin.py`,
`migrations/env.py`, `migrations/versions/0a0e4595d5cc_*.py` — ~776 líneas.

**Tests:** `tests/unit/inc1/**`, `tests/integration/inc1/**`, `tests/integration/conftest.py`,
`tests/step_defs/inc1/**`, `tests/features/inc1/*.feature` — ~807 líneas.

**Configuración:** `pyproject.toml` (dependencia `bcrypt`, `asyncio_default_fixture/test_loop_scope`, `markers`), `.pylintrc` (nuevo).

**Documentación:** `docs/plans/inc1/US-1.1.0-{context,plan}.md`,
`docs/reports/inc1/US-1.1.0-report.md` (este archivo),
`quality/reports/inc1/US-1.1.0-{quality,coverage}.json`,
`docs/adr/ADR-016/017/018-*.md`, `docs/architecture/03-bounded-contexts.md`, `CHANGELOG.md`.

---

## Criterios de Aceptación

- [x] Administrador crea un Docente — `Usuario` + perfil en la misma transacción, password hasheado con bcrypt, evento `UsuarioCreado`
- [x] Alta rechazada por email duplicado — `EmailYaRegistrado`, ningún Usuario nuevo
- [x] Administrador crea una Comisión — `docentes_asignados` vacío, evento `ComisionCreada`
- [x] Administrador asigna un Docente a una Comisión — evento `DocenteAsignado`
- [x] Rechazo al asignar un Usuario que no es Docente — `UsuarioNoEsDocente`, sin cambios en `docentes_asignados`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-1.1.1` — Docente genera link de invitación para una Comisión (siguiente US de la Iteración 1)
- [ ] `US-1.1.5` — agregar el guard de rol `administrador` a los 3 endpoints de esta US, hoy sin protección
- [ ] Actualizar `docs/plans/CHECKLIST-INSTALACION.md` con el paso de `scripts/seed_admin.py` post-deploy (pendiente, señalado en `ADR-016`)

---

## Lecciones Aprendidas

- ⚠️ `passlib` sin mantenimiento desde 2020 rompe con `bcrypt>=4.1` — preferir `bcrypt` directo en proyectos nuevos.
- ⚠️ SQLAlchemy no infiere el orden de inserción entre tablas relacionadas por FK cruda sin `relationship()` ORM — se necesita un flush intermedio explícito, y solo un test end-to-end real lo detecta.
- ⚠️ `pytest-bdd` 8.1.0 no soporta step functions `async def` — hay que envolver el cuerpo async con `asyncio.run()`, y el engine compartido necesita `NullPool` para tolerar múltiples event loops.
- 💡 Probar el flujo end-to-end contra Postgres real (curl manual antes que tests automatizados) detectó 2 bugs reales que ningún test unitario con fakes hubiera encontrado.
- 💡 Revisar el plan en secciones agrupadas (en vez de archivo por archivo) mantuvo el ritmo sin perder control real sobre el diseño.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-21
