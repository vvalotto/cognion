# Plan de Implementación: US-2.1.7 - Docente filtra el banco por materia, unidad, tema, dificultad e importancia

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** banco_preguntas

## Decisión de diseño: controller nuevo, no ampliar `PreguntasController`

`PreguntasController` ya está en CBO = 10/10 (umbral de `[tool.designreviewer]`) tras
`US-2.1.6`, con 4 use cases inyectados de escritura (carga ×2, editar, eliminar). Sumar un 5°
(`FiltrarBancoUseCase`) repetiría el patrón de CRITICAL ya visto en `US-2.1.2`/`US-2.1.5`/
`US-2.1.6`. Además, el endpoint de la spec vive bajo el recurso `/bancos/{id}/preguntas`, no
`/preguntas` — separación natural por recurso, no solo por CBO. Se crea `BancosController`
(lectura) como componente nuevo, sin tocar `PreguntasController`.

## Componentes a Implementar

### 1. Entities — Puerto de consulta
- [x] `src/banco_preguntas/entities/ports/pregunta_repository_port.py`
  - Agregar método abstracto `filtrar(banco_id, unidad=None, tema=None, dificultad=None, importancia=None) -> list[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso]`
  - Solo preguntas con `activa = true`

### 2. Use Case
- [x] `src/banco_preguntas/use_cases/filtrar_banco.py`
  - `FiltrarBancoUseCase(banco_repo: BancoRepositoryPort, pregunta_repo: PreguntaRepositoryPort)`
  - `execute(banco_id, unidad=None, tema=None, dificultad=None, importancia=None)`
  - Valida que el `Banco` existe (`BancoNoExiste` si no) — reutiliza el error ya definido en `entities/errors.py`
  - Delega el filtro combinado (AND) en `pregunta_repo.filtrar(...)`

### 3. Interface Adapters
- [x] `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
  - Implementar `filtrar(...)`: `SELECT` sobre `PreguntaPlantillaModel` con `WHERE banco_id = :banco_id AND activa = true` + condiciones opcionales por cada filtro provisto
  - Mapear cada fila al aggregate concreto según `tipo` (reutiliza la lógica ya existente en `obtener_por_id`, extraída a un método privado `_a_entidad(modelo)` para no duplicarla)
- [x] `src/banco_preguntas/interface_adapters/controllers/bancos_controller.py` (nuevo)
  - `BancosController(filtrar_banco: FiltrarBancoUseCase)`
  - Método `filtrar_preguntas(banco_id, unidad=None, tema=None, dificultad=None, importancia=None)`

### 4. Frameworks
- [x] `src/banco_preguntas/frameworks/api/schemas.py`
  - Reutilizar `PreguntaOpcionMultipleResponse` / `PreguntaVerdaderoFalsoResponse` ya existentes (sin schema nuevo) — la respuesta es `list[PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse]`, mismo patrón de unión que `editar_pregunta`
- [ ] `src/banco_preguntas/frameworks/api/bancos_router.py` (nuevo)
  - `GET /bancos/{banco_id}/preguntas?unidad=&tema=&dificultad=&importancia=`
  - Rol `docente` (`require_docente`, mismo criterio que el resto del BC)
  - 404 si `BancoNoExiste`
- [x] `src/banco_preguntas/frameworks/dependencies.py`
  - `get_bancos_controller(session)`: arma `BancosController(FiltrarBancoUseCase(banco_repo, pregunta_repo))`
- [x] `src/app.py`
  - Registrar `bancos_router` con `app.include_router(...)`

**Estado:** ✅ COMPLETADO — 8/8 tareas completadas

## Métricas de Tiempo (tracking real, no comparado contra estimación humana — PRIN-001)

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 1min 38s |
| 1 — Escenarios BDD | 26s |
| 2 — Plan de Implementación | 2min 2s |
| 3 — Implementación (6 tareas) | 5min 20s |
| 4 — Tests Unitarios | 1min 20s |
| 5 — Tests de Integración | 1min 15s |
| 6 — Validación BDD | 56s |
| 7 — Quality Gates | 9min 26s |

## Lecciones Aprendidas

- ✅ Detectar a tiempo (en la Fase 2) que `PreguntasController` ya estaba en el umbral de CBO
  evitó repetir el patrón de CRITICAL de las tres US anteriores — crear `BancosController`
  como componente nuevo fue más simple que el parche de "tipar como `object`" ya usado tres
  veces.
- 💡 Extraer el mapeo fila→entidad a `_a_entidad()` en `SQLAlchemyPreguntaRepository` antes de
  agregar `filtrar()` evitó duplicar esa lógica entre `obtener_por_id()` y el nuevo método.
- ⚠️ El coverage con solo los tests de integración a nivel HTTP no llegó a las ramas de
  filtro por `unidad`/`tema` en el gateway — hizo falta un test de integración específico del
  repositorio para esas dos ramas del `WHERE` dinámico.
