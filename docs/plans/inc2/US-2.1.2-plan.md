# Plan de Implementación: US-2.1.2 - Comisión referencia Materia por puerto (refactor técnico)

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion

## Componentes a Implementar

### 1. Banco de Preguntas — lectura de `Materia` por id (nuevo, solo lectura)

- [x] `src/banco_preguntas/entities/ports/materia_repository_port.py`
  - Agregar `obtener_por_id(materia_id: UUID) -> Materia | None` al puerto existente
- [x] `src/banco_preguntas/interface_adapters/gateways/materia_repository.py`
  - Implementar `obtener_por_id` en `SQLAlchemyMateriaRepository`
- [x] `src/banco_preguntas/use_cases/obtener_materia.py` (nuevo)
  - `ObtenerMateriaUseCase.execute(materia_id) -> Materia | None` — caso de uso de solo
    lectura que el adaptador de Identidad invocará in-process

### 2. Identidad — entities

- [x] `src/identidad/entities/comision.py`
  - `Comision.materia: str` → `Comision.materia_id: UUID`
  - `Comision.crear(materia_id, horario, administrador_id)`
- [x] `src/identidad/entities/ports/materia_port.py` (nuevo)
  - `MateriaDTO` (dataclass frozen: `id`, `nombre`) — evita que Identidad dependa de la
    Entity `Materia` de otro BC
  - `MateriaPort(ABC)` con `obtener(materia_id: UUID) -> MateriaDTO | None`
- [x] `src/identidad/entities/errors.py`
  - Agregar `MateriaNoExiste(materia_id)` — mismo estilo que las excepciones existentes
- [x] `src/identidad/entities/eventos.py`
  - `ComisionCreada.materia: str` → `ComisionCreada.materia_id: UUID`

### 3. Identidad — use_cases

- [x] `src/identidad/use_cases/crear_comision.py`
  - Recibe `MateriaPort` además del repositorio
  - Valida `materia_id` contra el puerto antes de crear la `Comision`; `MateriaNoExiste` si
    no resuelve
- [x] `src/identidad/use_cases/registrar_estudiante.py`
  - Recibe `MateriaPort` además de sus dependencias actuales
  - Resuelve el nombre de la materia vía `MateriaPort.obtener(comision.materia_id).nombre`
    para mantener el contrato actual de `RegistroResponse.materia` (str, user-facing) sin
    exponer `materia_id` crudo en el registro del Estudiante

### 4. Identidad — interface_adapters

- [x] `src/identidad/interface_adapters/gateways/comision_repository.py`
  - `SQLAlchemyComisionRepository`: mapear `materia_id` en `guardar`/`obtener_por_id`
- [x] `src/identidad/interface_adapters/controllers/comisiones_controller.py`
  - `crear_comision(materia_id: UUID, ...)` en vez de `materia: str`

### 5. Identidad — frameworks

- [x] `src/identidad/frameworks/db/models.py`
  - `ComisionModel.materia: str` → `ComisionModel.materia_id: UUID` (columna UUID simple,
    sin `ForeignKeyConstraint` entre esquemas de BCs — mismo criterio que la ausencia de
    imports directos)
- [x] `src/identidad/frameworks/adapters/materia_port_in_process.py` (nuevo)
  - `MateriaPortInProcess(MateriaPort)`: recibe la `AsyncSession` de Identidad, arma
    `SQLAlchemyMateriaRepository(session)` de Banco de Preguntas y llama a
    `ObtenerMateriaUseCase` — mismo criterio que `ADR-006` (integración directa entre BCs
    documentada como acoplamiento consciente)
- [x] `src/identidad/frameworks/api/schemas.py`
  - `CrearComisionRequest.materia: str` → `materia_id: UUID`
  - `ComisionResponse.materia: str` → `materia_id: UUID`
- [x] `src/identidad/frameworks/api/comisiones_router.py`
  - Actualizar el uso de `body.materia`/`comision.materia` → `materia_id`
- [x] `src/identidad/frameworks/dependencies.py`
  - Instanciar `MateriaPortInProcess(session)` e inyectarlo en `CrearComisionUseCase` y en
    `RegistrarEstudianteUseCase` dentro de `get_comisiones_controller` / `get_registro_controller`

### 6. Migración de datos y esquema

- [x] `migrations/versions/295bc74948c3_comision_materia_id.py` (down_revision = `099d86aa5d0d`)
  - `upgrade()`:
    1. Agregar columna `comision.materia_id UUID` nullable
    2. `UPDATE comision SET materia_id = materia.id FROM materia WHERE comision.materia = materia.nombre`
    3. Alterar `materia_id` a `NOT NULL`
    4. Eliminar columna `comision.materia`
  - `downgrade()`: inverso (agregar `materia` nullable, backfill por join inverso, `NOT NULL`,
    eliminar `materia_id`)

### 7. Integración

- [x] Verificar en `comisiones_router.py` y `registro_router.py` que no queda ningún uso de
  `comision.materia` como string
- [x] Confirmar (grep) que `src/identidad/` no importa ningún módulo de `src/banco_preguntas/`
  fuera de `MateriaPortInProcess` — y que ese archivo vive en `frameworks/`, no en `entities/`
  ni `use_cases/`

**Estado:** ✅ COMPLETADO — 17/17 tareas completadas
**Fecha completado:** 2026-08-05

## Métricas de Tiempo (tracking real, `.claude/tracking/US-2.1.2-tracking.json`)

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Validación de contexto | 5 min 23s |
| Fase 1 — Escenarios BDD | 1 min 22s |
| Fase 2 — Plan de implementación | 6 min 41s |
| Fase 3 — Implementación (17 tareas) | 44 min 34s |
| Fase 4 — Tests unitarios | 10 min 31s |
| Fase 5 — Tests de integración | 5 min 12s |
| Fase 6 — Validación BDD | 11 min 47s |
| Fase 7 — Quality gates | 5 min 48s |
| **Total (Fases 0–7)** | **1h 34min** |

> Sin estimaciones humanas previas (PRIN-001) — tracking registra tiempos reales de ejecución
> del agente, no comparables contra estimación humana de 3 puntos.

## Lecciones Aprendidas

- ⚠️ El alcance real fue mayor al descripto en la spec original: `RegistrarEstudianteUseCase`
  también dependía de `Comision.materia` (para `RegistroResponse.materia`, user-facing), no
  solo `CrearComisionUseCase`. Detectado en Fase 2 (planning) antes de escribir código —
  evitó una regresión no cubierta en la spec original.
- ⚠️ Blast radius de tests fue mayor al anticipado: 4 step_defs de Identidad preexistentes
  (`US-1.1.0` a `US-1.1.4`) usaban `POST /comisiones` con `"materia"` string y necesitaron
  crear una `Materia` real primero. Ninguno estaba listado en la spec de `US-2.1.2` por ser
  de una US distinta — encontrados por corrida completa de la suite en Fase 6, no por grep
  previo.
- ✅ La ausencia de `ForeignKeyConstraint` entre `comision.materia_id` y `materia.id` (decisión
  explícita de la spec, "sin FK de base entre BCs") simplificó los tests unitarios/integración
  a nivel de repositorio: no fue necesario crear una `Materia` real para testear
  `SQLAlchemyComisionRepository` de forma aislada, solo para los flujos que pasan por
  `CrearComisionUseCase` (que sí valida contra `MateriaPort`).
- 💡 Migración verificada con round-trip real (`alembic upgrade head` → `downgrade -1` →
  `upgrade head`) contra Postgres local antes de dar la tarea por completada — detectó
  temprano que el backfill SQL (`UPDATE ... FROM ... WHERE`) era sintácticamente correcto
  antes de escribir el resto del código que depende de la columna.
