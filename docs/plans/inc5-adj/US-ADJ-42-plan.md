# Plan de Implementación: US-ADJ-42 - Autoregistro de Estudiante (endpoint público)

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-13

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 45 s |
| 1 — Escenarios BDD | 33 s |
| 2 — Plan de Implementación | 75 s |
| 3 — Implementación Guiada por Tareas | 116 s |
| 4 — Tests Unitarios | 70 s |
| 5 — Tests de Integración | 4 s |
| 6 — Validación BDD | 135 s |
| 7 — Quality Gates | 182 s |
| **Total (Fases 0-7)** | **~11 min** |

## Lecciones Aprendidas

- ✅ Reutilizar el patrón exacto de `US-ADJ-41` (mismo shape de use case, controller, router,
  dependencies) redujo la implementación a extender archivos existentes — sin componentes
  nuevos fuera de lo previsto en el plan.
- ✅ `FakeComisionRepository` ya existía en `tests/unit/inc1/_fakes.py` — sin necesidad de
  crear un fake nuevo para el test unitario.
- 💡 `codeguard` requiere el PATH con `.venv/bin` para que `vulture`/`codespell` resuelvan
  correctamente — invocado como `.venv/bin/codeguard` directo sin `PATH` ajustado, ambos
  checks fallan silenciosamente con "not installed" aunque estén instalados en el venv.

## Componentes a Implementar

### 1. Use Case
- [x] `src/identidad/use_cases/autoregistrar_estudiante.py`
  - `AutoregistrarEstudianteUseCase(usuario_repo, hasher, comision_repo)`
  - `execute(nombre, email, password, comision_id) -> tuple[Usuario, UsuarioAutoregistrado]`
  - Orden de validación: `existe_email` → `EmailYaRegistrado`; `comision_repo.obtener_por_id()`
    → `ComisionNoExiste` si `None` (INV-ID-14); `Usuario.validar_password_nueva()` → INV-ID-11
    ampliada; `Usuario.crear_estudiante(nombre, email, password_hash, comision_id)` (INV-ID-16,
    activa de inmediato); `usuario_repo.guardar()`.
  - Reutiliza el evento `UsuarioAutoregistrado` de `US-ADJ-41` (mismo shape, sin `comision_id`
    en el payload).
  - Mismo criterio de "dos comandos separados" que `AutoregistrarDocenteUseCase` — no se
    generaliza con un parámetro `perfil`.

### 2. Interface Adapters
- [x] `src/identidad/interface_adapters/controllers/autoregistro_controller.py`
  - Constructor gana el segundo caso de uso: `autoregistrar_estudiante: AutoregistrarEstudianteUseCase`.
  - Método nuevo `autoregistrar_estudiante(nombre, email, password, comision_id)` — delega en
    el caso de uso, mismo patrón que `autoregistrar_docente`.

### 3. Frameworks
- [x] `src/identidad/frameworks/api/schemas.py`
  - `AutoregistrarEstudianteRequest(BaseModel)`: `nombre: str`, `email: str`, `password: str`
    (mismos `Field` que `AutoregistrarDocenteRequest`), `comision_id: UUID`.
  - Reutiliza `AutoregistroResponse` existente — sin campo `comision_id` en la respuesta (la
    spec solo pide "los datos del Usuario creado"; mismo criterio que `UsuarioAutoregistrado`
    sin ese dato en el payload del evento).
- [x] `src/identidad/frameworks/api/autoregistro_router.py`
  - Endpoint nuevo `POST /identidad/autoregistro/estudiante`, público, `201 Created`.
  - Manejo de excepciones: `EmailYaRegistrado` → 409; `ComisionNoExiste` → 422;
    `PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente` → 422 (excepto propio para
    `ComisionNoExiste`, separado del de password).
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_autoregistro_controller` gana `comision_repo = SQLAlchemyComisionRepository(session)`
    (ya importado en el módulo, usado por `get_registro_controller`) y cablea
    `AutoregistrarEstudianteUseCase(usuario_repo, hasher, comision_repo)` como segundo
    argumento de `AutoregistroController`.

### 4. Integración
- [x] Ninguna integración nueva entre BCs — todos los puertos (`UsuarioRepositoryPort`,
  `PasswordHasherPort`, `ComisionRepositoryPort`) ya están inyectados en otros use cases del
  mismo BC Identidad.

**Estado:** 4/4 tareas completadas
