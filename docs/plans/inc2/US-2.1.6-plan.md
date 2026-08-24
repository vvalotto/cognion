# Plan de Implementación: US-2.1.6 - Docente elimina (baja lógica) una pregunta

**Patrón:** clean-architecture-bc (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Banco de Preguntas)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-12

## Métricas de Tiempo (tracking real, fases 0-8)

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 5 min 29s |
| 1 — Escenarios BDD | 20s |
| 2 — Plan de Implementación | 2 min 9s |
| 3 — Implementación | 7 min 29s |
| 4 — Tests Unitarios | 2 min 55s |
| 5 — Tests de Integración | 1 min 22s |
| 6 — Validación BDD | 1 min 52s |
| 7 — Quality Gates | 10 min 2s |
| **Total (fases 0-7)** | **~33 min** |

## Lecciones Aprendidas

- ✅ Reutilizar `obtener_por_id()`/`actualizar()` del puerto (ya agregados en `US-2.1.5`) evitó
  cualquier cambio en `PreguntaRepositoryPort` o en el gateway — la única pieza nueva de
  persistencia fue la entidad y el use case.
- ✅ Tipar el evento de retorno como `object` en el controller (mismo criterio preventivo de
  `US-2.1.5`) evitó repetir el CRITICAL de CBO en el pre-push gate — no volvió a aparecer.
- 💡 Acotar CodeGuard a los archivos modificados (convención vigente desde PR #64) expuso 2
  warnings de línea larga en archivos tocados por esta US, no relacionados al método nuevo;
  se corrigieron igual por estar en el alcance del diff.

## Componentes a Implementar

### 1. Entities
- [x] `src/banco_preguntas/entities/errors.py`
  - Agregar `PreguntaYaEliminada` — mismo patrón que `PreguntaInactiva` (guarda `pregunta_id`)
- [x] `src/banco_preguntas/entities/eventos.py`
  - Agregar `PreguntaEliminada` (frozen dataclass, `pregunta_id`, `banco_id`, `ocurrido_en`) —
    mismo shape que `PreguntaEditada`
- [x] `src/banco_preguntas/entities/pregunta_plantilla.py`
  - Método `eliminar()` en `PreguntaPlantillaVerdaderoFalso` y en `PreguntaPlantillaOpcionMultiple`
  - Levanta `PreguntaYaEliminada` si `not self.activa`; si no, `self.activa = False`
  - Sin invariantes de tipo — mismo comportamiento en ambos aggregates, se repite igual que
    `editar()` (no hay clase base común en el código actual)

### 2. Use Cases
- [x] `src/banco_preguntas/use_cases/eliminar_pregunta.py` (nuevo)
  - `EliminarPreguntaUseCase(pregunta_repositorio: PreguntaRepositoryPort)`
  - `execute(pregunta_id: UUID) -> tuple[PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso, PreguntaEliminada]`
  - Obtiene por id (`PreguntaNoExiste` si `None`), delega en `pregunta.eliminar()`, persiste
    con `actualizar()` (ya existe, reutilizado de `US-2.1.5`), emite `PreguntaEliminada`
  - No requiere cambios en `PreguntaRepositoryPort` — `obtener_por_id`/`actualizar` ya cubren
    el caso (misma forma de persistencia que `editar`)

### 3. Interface Adapters
- [x] `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`
  - Cuarto use case inyectado: `eliminar_pregunta: EliminarPreguntaUseCase`
  - Método `eliminar_pregunta(pregunta_id) -> tuple[..., object]` — evento tipado `object`,
    mismo criterio ya aplicado a `editar_pregunta` en `US-2.1.5` para no sumar el import de
    `PreguntaEliminada` al CBO del controller
- [x] `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
  - Sin cambios — `actualizar()` ya persiste el campo `activa` genéricamente (fix aplicado en
    `US-2.1.5` tras el bug de integración)

### 4. Frameworks
- [x] `src/banco_preguntas/frameworks/api/preguntas_router.py`
  - `DELETE /preguntas/{pregunta_id}`, rol `docente`, `204 No Content` en éxito (sin
    response body — la baja lógica no necesita devolver el recurso)
  - Rechazos: `PreguntaNoExiste` → 404, `PreguntaYaEliminada` → 409
- [x] `src/banco_preguntas/frameworks/dependencies.py`
  - `get_preguntas_controller` instancia también `EliminarPreguntaUseCase(pregunta_repo)`
- [x] `src/banco_preguntas/frameworks/api/schemas.py`
  - Sin cambios — no hay request/response body para este endpoint

### 5. Integración
- [x] Verificar que `US-2.1.7` (pendiente, no parte de este plan) podrá filtrar por
  `activa = true` sin cambios adicionales — ya es el comportamiento del modelo actual

**Riesgo a vigilar (heredado de `US-2.1.2` y `US-2.1.5`):** el pre-push gate
(`DesignReviewer`/`CBOAnalyzer`) puede detectar CRITICAL de CBO al sumar el cuarto use case al
controller. Si aparece, aplicar el mismo fix que en `US-2.1.5` (tipar el retorno como `object`
en el controller — ya adoptado en el punto 3 de este plan como medida preventiva).

**Estado:** 9/9 tareas completadas
