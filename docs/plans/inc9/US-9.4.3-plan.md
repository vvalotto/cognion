# Plan de Implementación: US-9.4.3 - Identidad deja de leer `EventoModel` de Actividad Evaluativa

**Patrón:** clean-architecture-bc · **Producto:** cognion · **Capas:** `actividad_evaluativa` (entities/ports, frameworks/adapters) e `identidad` (frameworks/adapters)

## Diseño
`EvaluacionConsultaPortInProcess` (Identidad) consulta `EventoModel` directamente. Actividad Evaluativa pasa a exponer la pregunta por un puerto propio de consulta, con el mismo patrón que `EvaluacionEstudianteQueryPort`.

```
antes:  adaptador (identidad) ──select EventoModel──► tabla evento                            (viola ADR-026)
después: adaptador (identidad) ──► SQLAlchemyEstudianteEvaluacionesQueryRepository ──► tabla evento
                                    (implementa EstudianteEvaluacionesQueryPort, en actividad_evaluativa)
```

- Misma lógica de hoy (payload filtrado en memoria); sin operadores JSONB ni cambios de rendimiento.
- Puerto y gateway nuevos (no se ensancha `EvaluacionEstudianteQueryPort`, para no repetir el patrón de CBO de `US-2.1.2`/`US-2.1.5`).
- Sin cambios en `eliminar_cuenta`, API ni frontend.

## Componentes a Implementar

### 1. Proveedor — Actividad Evaluativa
- [ ] `src/actividad_evaluativa/entities/ports/estudiante_evaluaciones_query_port.py`: `EstudianteEvaluacionesQueryPort.tiene_evaluaciones_iniciadas(estudiante_id) -> bool`, con docstring.
- [ ] `src/actividad_evaluativa/frameworks/adapters/estudiante_evaluaciones_query_repository.py`: `SQLAlchemyEstudianteEvaluacionesQueryRepository` con la consulta actual sobre `EventoModel`.

### 2. Consumidor — Identidad
- [ ] `src/identidad/frameworks/adapters/evaluacion_consulta_port_in_process.py`: `tiene_evaluaciones` delega en el gateway; se quitan `EventoModel`, `select` y las constantes que queden sin uso; docstrings actualizados.

### 3. Regla de imports
- [ ] `pyproject.toml`: borrar la línea `ignore_imports` marcada `# #602`.

## Tests (Fases 4 y 5)
- **Primero, antes de tocar `src/` (caracterización, `tests/integration/inc9/test_us_9_4_3_evaluacion_consulta_integration.py`):** sin evaluaciones → `False`; con una iniciada → `True`; evaluaciones de otro estudiante no cuentan; eventos de otro tipo o agregado con el mismo `estudiante_id` no cuentan. Eventos cargados con `SQLAlchemyEventStore`. En verde antes y después. Primer commit.
- **Integración del gateway** (`tests/integration/inc9/test_us_9_4_3_estudiante_evaluaciones_query_integration.py`): mismos casos sobre el gateway nuevo.
- **Unitarios:** `tests/unit` completo (el fake `FakeEvaluacionConsultaPort` no cambia).
- `uv run lint-imports`, mypy y `designreviewer` en verde.

## Documentación (Fase 8)
- Spec `US-9.4.3` → `Implementada`; `ADR-026`: caso 3 migrado. El cierre de la iteración actualiza `CLAUDE.md`.

## Riesgos
- **Proveedor nuevo con consumidor de otro BC:** el import vive solo en `frameworks/adapters/` (permitido por el contrato).
- **CBO:** puerto y gateway pequeños; se mide en la Fase 7.
- **Constantes duplicadas** (`"Evaluacion"`, `"EvaluacionIniciada"`) entre gateways del proveedor: es el patrón vigente, no se unifica aquí.
