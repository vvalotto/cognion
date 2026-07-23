# Plan de Implementación: US-1.1.2 - Estudiante se registra con un link de invitación válido

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Identidad)
**Alcance:** backend completo. Frontend diferido a una US-IEDD separada (ver `US-1.1.2-context.md`).
**Estado:** ✅ COMPLETADO — 2026-07-23

## Métricas de Tiempo

| Fase | Real |
|------|------|
| 0 — Validación de Contexto | 52s |
| 1 — Escenarios BDD | 58s |
| 2 — Plan de Implementación | 294s |
| 3 — Implementación | 484s |
| 4 — Tests Unitarios | 101s |
| 5 — Tests de Integración | 208s |
| 6 — Validación BDD | 268s |
| 7 — Quality Gates | 222s |
| **Total (fases 0-7)** | **~28 min** |

Sin comparación estimado/real — no se registraron estimaciones previas por fase (PRIN-001,
el tracking mide tiempo real, no varianza contra esfuerzo humano).

## Lecciones aprendidas

- ⚠️ El orden de `DELETE FROM` en la limpieza de tablas de tests de integración/BDD
  (`tests/integration/conftest.py`, `test_us_1_1_0_steps.py`, `test_us_1_1_1_steps.py`) no
  consideraba la nueva FK `estudiante.comision_id → comision.id` — rompió 3 suites de tests
  hasta reordenar `estudiante` antes de `comision`. Corregido en Fase 5/6.
- ⚠️ Restringir `Usuario.crear()` para que rechace `TipoPerfil.ESTUDIANTE` tuvo efecto
  colateral en un fixture de `US-1.1.0` (`test_us_1_1_0_steps.py`, escenario "usuario que no
  es Docente") que usaba el endpoint genérico `POST /usuarios` con `perfil=estudiante` —
  ahora imposible sin `comision_id`. Se resolvió creando el Estudiante directo por
  repositorio en el fixture, sin tocar el lenguaje del escenario Gherkin.
- 💡 Reutilizar el mismo criterio de US-1.1.1 (endpoint público sin guard JWT) evitó una
  decisión de alcance nueva — la dependencia de `US-1.1.4`/`US-1.1.5` quedó documentada una
  sola vez y replicada por precedente.

## Componentes a Implementar

### 1. Entities
- [x] `src/identidad/entities/usuario.py`
  - Agregar `comision_id: UUID` a `Estudiante` (INV-ID-05: nunca existe sin comisión)
  - Agregar `Usuario.crear_estudiante(nombre, email, password_hash, comision_id)` — único
    camino de construcción de un `Estudiante`
  - Restringir `Usuario.crear()` genérico a `Administrador`/`Docente` — lanza `ValueError`
    si se pide `TipoPerfil.ESTUDIANTE` (ese perfil solo se crea vía invitación)
- [x] `src/identidad/entities/invitacion.py`
  - Método `Invitacion.es_vigente(ahora) -> bool` (INV-ID-01, INV-ID-03)
  - Método `Invitacion.aceptar(ahora) -> None` — marca `usada_en`, valida vigencia primero
- [x] `src/identidad/entities/errors.py`
  - `InvitacionNoValida` — guard genérico para token inexistente/vencido/usado en esta US;
    `US-1.1.3` la refina en las tres excepciones específicas de su propio alcance
- [x] `src/identidad/entities/eventos.py`
  - `InvitacionAceptada(invitacion_id, comision_id, usuario_id)`
  - `UsuarioRegistrado(usuario_id, email, comision_id)`
- [x] `src/identidad/entities/ports/invitacion_repository_port.py`
  - `obtener_por_token(token) -> Invitacion | None`
  - `actualizar(invitacion) -> None`

### 2. Use Cases
- [x] `src/identidad/use_cases/registrar_estudiante.py`
  - `RegistrarEstudianteUseCase(invitacion_repo, usuario_repo, hasher)`
  - `execute(token, nombre, email, password) -> (Usuario, InvitacionAceptada, UsuarioRegistrado)`
  - Orden: 1) validar invitación vigente, 2) validar email libre, 3) hashear password,
    4) crear Usuario+Estudiante, 5) marcar invitación usada, 6) emitir eventos

### 3. Interface Adapters
- [x] `src/identidad/interface_adapters/controllers/registro_controller.py`
  - `RegistroController.registrar_estudiante(token, nombre, email, password)`
- [x] `src/identidad/interface_adapters/gateways/invitacion_repository.py`
  - Implementar `obtener_por_token`, `actualizar`
- [x] `src/identidad/interface_adapters/gateways/usuario_repository.py`
  - Ajustar `guardar`/`_resolver_perfil` para persistir y reconstruir `comision_id` de
    `EstudianteModel` (no aplica a Administrador/Docente)

### 4. Frameworks
- [x] `src/identidad/frameworks/db/models.py`
  - `EstudianteModel.comision_id` (FK a `comision.id`, `nullable=False`)
- [x] Migración Alembic — agrega columna `comision_id` a `estudiante` (aplicada localmente)
- [x] `src/identidad/frameworks/api/schemas.py`
  - `RegistrarEstudianteRequest(token, nombre, email, password)`
  - `RegistroResponse(id, nombre, email, comision_id)`
- [x] `src/identidad/frameworks/api/registro_router.py`
  - `POST /identidad/registro` — público, sin guard JWT (decisión confirmada, igual que
    `US-1.1.1`). Mapea `EmailYaRegistrado` → 409, `InvitacionNoValida` → 422
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_registro_controller(session)`
- [x] `src/app.py` — registrar `registro_router`

### 5. Integración
- [x] Registrar el nuevo router en la app FastAPI
- [x] Verificar que `AsignarDocenteAComisionUseCase` y sus tests no se rompen por la
  restricción de `Usuario.crear()` sobre `TipoPerfil.ESTUDIANTE` (actualizado el fixture de
  ese test a `Usuario.crear_estudiante`; también `test_usuario.py`)

**Estado:** 14/14 tareas completadas

## Nota de implementación

`FakeInvitacionRepository` (`tests/unit/inc1/_fakes.py`) se extendió con `obtener_por_token` y
`actualizar` para seguir implementando `InvitacionRepositoryPort` — no estaba en el plan
original pero era necesario porque la clase abstracta ahora exige esos dos métodos.
