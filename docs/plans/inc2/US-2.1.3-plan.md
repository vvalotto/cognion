# Plan de Implementación: US-2.1.3 - Docente carga una pregunta de opción múltiple

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion / BC banco_preguntas
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-06

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Validación de Contexto | 4 min |
| Fase 1 — Escenarios BDD | 5 min |
| Fase 2 — Plan de Implementación | 2 min |
| Fase 3 — Implementación (13 tareas) | 8 min |
| Fase 4 — Tests Unitarios | 3 min |
| Fase 5 — Tests de Integración | 3 min |
| Fase 6 — Validación BDD | 1 min |
| Fase 7 — Quality Gates | 6 min |
| **Total (Fases 0–7)** | **~36 min** |

> Sin comparación contra estimaciones humanas (`PRIN-001`, `.claude/skills/implement-us/skill.md`) — tiempos registrados por `tracker_cli.py`.

## Lecciones Aprendidas

- ✅ Delegar la validación de INV-BP-02/03 al factory de la entidad (`PreguntaPlantillaOpcionMultiple.crear`) mantuvo el use case simple — un solo punto de verdad para las invariantes estructurales de `opciones`.
- 💡 `unidad_tematica` (nombre completo del atributo en `BC-banco-preguntas-modelo.md`) en vez de `unidad` (shorthand del comando en la spec) evitó ambigüedad en el modelo de datos.
- ⚠️ La spec sugería `src/.../frameworks/db/migrations/` para la migración Alembic; la convención real del proyecto es `migrations/versions/` en la raíz — verificado contra `US-2.1.1`/`US-2.1.2` antes de generarla.

## Componentes a Implementar

### 1. Entities

- [x] `src/banco_preguntas/entities/opcion.py`
  - `Opcion` — value object `frozen dataclass` (`texto: str`, `es_correcta: bool`)
  - Nota de implementación: también se crearon `entities/dificultad.py` e
    `entities/importancia.py` (`StrEnum` Alto/Medio/Bajo), requeridos por el aggregate según
    `BC-banco-preguntas-modelo.md` §4 pero no desglosados como archivo aparte en este plan.
- [x] `src/banco_preguntas/entities/pregunta_plantilla.py`
  - `PreguntaPlantillaOpcionMultiple` — dataclass con `id`, `banco_id`, `texto`, `opciones: list[Opcion]`, `unidad_tematica`, `tema`, `dificultad`, `importancia`, `activa`
  - Factory `crear(banco_id, texto, opciones, unidad_tematica, tema, dificultad, importancia)`:
    valida INV-BP-02 (exactamente una `es_correcta`) e INV-BP-03 (mínimo 2 opciones), levanta
    `OpcionesInvalidas` si se incumple alguna. Estas son invariantes puras de la estructura de
    `opciones` — no requieren repositorio, se validan en la entidad (mismo criterio que
    `Banco.crear`/`Materia.crear`).
  - Nota: se usó `unidad_tematica` (nombre del atributo en `BC-banco-preguntas-modelo.md` §4)
    en vez de `unidad` (shorthand usado en la spec/comando) — mismo campo, nombre completo.
- [x] `src/banco_preguntas/entities/errors.py` (editado)
  - `OpcionesInvalidas` — INV-BP-02/03
  - `BancoNoExiste` — precondición (`banco_id` debe referenciar un `Banco` existente)
- [x] `src/banco_preguntas/entities/eventos.py` (editado)
  - `PreguntaCargada(pregunta_id, banco_id, ocurrido_en)`
- [x] `src/banco_preguntas/entities/ports/pregunta_repository_port.py`
  - `PreguntaRepositoryPort.guardar(pregunta: PreguntaPlantillaOpcionMultiple) -> None`
- [x] `src/banco_preguntas/entities/ports/banco_repository_port.py` (editado)
  - `BancoRepositoryPort.obtener_por_id(banco_id: UUID) -> Banco | None` — necesario para
    validar la precondición de `banco_id` existente (mismo patrón que
    `MateriaRepositoryPort.obtener_por_id`)

### 2. Use Cases

- [x] `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py`
  - `CargarPreguntaOpcionMultipleUseCase.execute(banco_id, texto, opciones, unidad_tematica, tema, dificultad, importancia)`
  - Verifica que el `Banco` existe (`BancoNoExiste` si no); delega la validación de
    INV-BP-02/03 a `PreguntaPlantillaOpcionMultiple.crear` (propaga `OpcionesInvalidas`);
    persiste vía `PreguntaRepositoryPort`; devuelve `(pregunta, PreguntaCargada)`

### 3. Interface Adapters

- [x] `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`
  - `PreguntasController.cargar_pregunta_opcion_multiple(...)` — delega en el use case
- [x] `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
  - `SQLAlchemyPreguntaRepository` implementa `PreguntaRepositoryPort`; `obtener_por_id` se
    agregó directamente a `SQLAlchemyBancoRepository` existente (no una clase nueva)

### 4. Frameworks

- [x] `src/banco_preguntas/frameworks/db/models.py` (editado)
  - `PreguntaPlantillaModel` — tabla `pregunta_plantilla`, columna discriminadora `tipo`
    (`"opcion_multiple"` en esta US, deja lugar a `"verdadero_falso"` en `US-2.1.4`),
    `opciones` como `JSONB` (lista de `{texto, es_correcta}` — sin tabla aparte, coherente con
    el event store JSONB append-only ya usado en el proyecto), `unidad_tematica`, `tema`,
    `dificultad`, `importancia`, `activa`, `banco_id` FK
- [x] `src/banco_preguntas/frameworks/api/schemas.py` (editado)
  - `OpcionSchema`, `CargarPreguntaOpcionMultipleRequest`, `PreguntaOpcionMultipleResponse`
- [x] `src/banco_preguntas/frameworks/api/preguntas_router.py`
  - `POST /preguntas/opcion-multiple` — requiere rol `docente` (`require_docente`), 201 en
    éxito, 404 si `banco_id` no existe, 422 si `OpcionesInvalidas`
- [x] `src/banco_preguntas/frameworks/dependencies.py` (editado)
  - `get_preguntas_controller(session)` — arma `PreguntasController` con sus dependencias
- [x] `migrations/versions/b0e03a73f699_pregunta_plantilla.py` — migración Alembic para la
  tabla `pregunta_plantilla`, aplicada contra PostgreSQL local (`alembic upgrade head`)
  (convención real del proyecto: `migrations/versions/`, no `src/.../frameworks/db/migrations/`
  como sugiere la spec — se ajusta a la estructura ya usada por `US-2.1.1`/`US-2.1.2`)

### 5. Integración

- [x] `src/app.py` — registrado `preguntas_router` con `app.include_router(...)`

**Estado:** 13/13 tareas completadas
