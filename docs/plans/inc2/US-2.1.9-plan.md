# Plan de Implementación: US-2.1.9 - Docente ve el listado de materias y da de alta una nueva

**Patrón:** Clean Architecture BC-first (backend) + React 19 + TypeScript + Vite (frontend)
**Producto:** banco_preguntas
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-14

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Análisis de spec | 62s |
| 1 — Escenarios BDD | 25s |
| 2 — Plan de implementación | 43s |
| 3 — Implementación | 731s |
| 4 — Tests unitarios | 377s |
| 5 — Tests de integración | 381s |
| 6 — Validación BDD | 182s |
| 7 — Quality Gates | 211s |
| **Total (fases 0-7)** | **~33 min** |

> Sin comparación contra estimación humana (PRIN-001).

## Lecciones Aprendidas

- ✅ Actualizar el Issue de GitHub (#50) junto con la spec, no solo la spec, evitó que la
  fuente pública quedara desalineada con el alcance real acordado con Víctor.
- ✅ El `.feature` mixto (1 escenario backend + 3 frontend) funcionó bien usando
  `@scenario` (singular) de pytest-bdd para cargar solo el escenario backend, en vez de
  `scenarios()` (plural, que hubiera intentado ejecutar también los 3 escenarios frontend
  sin step defs y fallado la colección).
- ✅ Reutilizar `PreguntaRepositoryPort.filtrar()` para el conteo de preguntas activas
  (en vez de agregar un método de conteo dedicado) mantuvo ese puerto sin ensanchar,
  consistente con la decisión tomada en `US-2.1.7`.

## Componentes a Implementar

### 1. Backend — entities/ports
- [x] `src/banco_preguntas/entities/ports/materia_repository_port.py`
  - Método abstracto nuevo: `listar() -> list[Materia]`
- [x] `src/banco_preguntas/entities/ports/banco_repository_port.py`
  - Método abstracto nuevo: `obtener_por_materia_id(materia_id: UUID) -> Banco | None`

### 2. Backend — use_cases
- [x] `src/banco_preguntas/use_cases/listar_materias.py`
  - `ListarMateriasUseCase.execute() -> list[tuple[Materia, Banco, int]]` — por cada materia
    de `materia_repo.listar()`, resuelve su `Banco` (`banco_repo.obtener_por_materia_id()`) y
    cuenta preguntas activas reutilizando `pregunta_repo.filtrar(banco.id)` + `len(...)` (sin
    agregar método de conteo dedicado al puerto de preguntas)

### 3. Backend — interface_adapters
- [x] `src/banco_preguntas/interface_adapters/controllers/materias_controller.py`
  - Inyecta `ListarMateriasUseCase` además de `CrearMateriaUseCase` (ya existente)
  - Método nuevo: `listar_materias()`
- [x] `src/banco_preguntas/interface_adapters/gateways/materia_repository.py`
  - Implementa `listar()` (`SELECT` sin filtros sobre `MateriaModel`)
- [x] `src/banco_preguntas/interface_adapters/gateways/banco_repository.py`
  - Implementa `obtener_por_materia_id()` (`SELECT ... WHERE materia_id = :id`)

### 4. Backend — frameworks
- [x] `src/banco_preguntas/frameworks/api/schemas.py`
  - `MateriaListItemResponse` (id, nombre, banco_id, cantidad_preguntas_activas)
- [x] `src/banco_preguntas/frameworks/api/materias_router.py`
  - `GET /materias` (rol `docente`), `response_model=list[MateriaListItemResponse]`
- [x] `src/banco_preguntas/frameworks/dependencies.py`
  - `get_materias_controller` arma `MateriasController` con ambos use cases

### 5. Frontend — cliente API
- [x] `frontend/src/lib/banco-preguntas-api.ts`
  - `listarMaterias()` (excluida de `US-2.1.8` por este gap) — mapea
    `cantidad_preguntas_activas` a `cantidadPreguntasActivas`

### 6. Frontend — pantallas
- [x] `frontend/src/pages/Materias.tsx`
  - Grilla de materias (nombre + cantidad de preguntas activas), tarjeta "Nueva materia"
    (wireframe §2.1)
- [x] `frontend/src/pages/NuevaMateria.tsx`
  - Formulario de alta (campo nombre), error inline por nombre duplicado (409), vuelve al
    listado en éxito (wireframe §2.2)

### 7. Frontend — routing
- [x] `frontend/src/router.tsx`
  - Reemplazar el placeholder de `/materias` y `/materias/nueva` por las pantallas reales

**Estado:** 7/7 tareas completadas
