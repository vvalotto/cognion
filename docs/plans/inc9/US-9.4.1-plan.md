# Plan de Implementación: US-9.4.1 - Banco de Preguntas deja de leer `ComisionModel` de Identidad

**Patrón:** clean-architecture-bc · **Producto:** cognion · **Capas:** `identidad` (entities/ports, interface_adapters/gateways) y `banco_preguntas` (frameworks/adapters)

## Diseño
`ComisionConsultaPortInProcess.tiene_comisiones` consulta `ComisionModel` directamente. Identidad pasa a exponer esa pregunta por su propio puerto de consulta, y el adaptador solo delega, igual que ya hace `esta_asignado_a_materia`.

```
antes:  adaptador (banco_preguntas) ──select ComisionModel──► tabla comision          (viola ADR-026)
después: adaptador (banco_preguntas) ──► ComisionQueryPort.existe_comision_en_materia ──► gateway de identidad ──► tabla comision
```

- El comportamiento observable no cambia: `True` si hay al menos una comisión, activa o no, con esa materia.
- Sin cambios en casos de uso (`eliminar_materia`), API ni frontend.

## Componentes a Implementar

### 1. Proveedor — Identidad
- [ ] `src/identidad/entities/ports/comision_query_port.py`: método abstracto `existe_comision_en_materia(materia_id) -> bool`, con docstring (activas o no).
- [ ] `src/identidad/interface_adapters/gateways/comision_query_repository.py`: implementación con `select(ComisionModel.id).where(materia_id == ...).limit(1)`.

### 2. Consumidor — Banco de Preguntas
- [ ] `src/banco_preguntas/frameworks/adapters/comision_consulta_port_in_process.py`: `tiene_comisiones` delega en `self._comision_query.existe_comision_en_materia`; se quitan los imports de `ComisionModel`, `select` y el atributo `_session` si queda sin uso; docstring del módulo y de la clase actualizados.

### 3. Regla de imports
- [ ] `pyproject.toml`: borrar la línea `ignore_imports` marcada `# #600`.

## Tests (Fases 4 y 5)
- **Primero, antes de tocar `src/` (caracterización, integración, `tests/integration/inc9/test_us_9_4_1_comision_consulta_integration.py`):** sobre el adaptador actual, materia sin comisiones → `False`; con una activa → `True`; solo con comisiones deshabilitadas → `True`; otra materia no afecta; `esta_asignado_a_materia` intacto. Debe pasar en verde **antes y después** de la migración. Es el primer commit de la US.
- **Integración del gateway** (`tests/integration/inc4/test_comision_query_repository.py`): casos de `existe_comision_en_materia`.
- **Unitarios:** `FakeComisionQueryRepository` (`tests/unit/inc1/_fakes.py`) y los demás fakes de `ComisionQueryPort` implementan el método nuevo; los tests existentes no cambian.
- **Regla de imports:** `uv run lint-imports` en verde sin la línea `# #600`; `tests/unit/inc9/test_guarda_arquitectura.py` sigue pasando.
- Integración con `DATABASE_URL` inline a una base descartable.

## Documentación (Fase 8)
- Spec `US-9.4.1`: estado → `Implementada`.
- `docs/adr/ADR-026`: marcar el caso 1 como migrado.
- `CLAUDE.md`: sin cambios hasta cerrar la iteración (hoy dice "tres excepciones pendientes, #600 a #602").

## Riesgos
- **CBO del gateway de Identidad** cerca del umbral: se mide recién en el pre-push; el método nuevo no suma dependencias.
- **Otros fakes de `ComisionQueryPort`:** si alguno queda sin el método, el test unitario falla al instanciarlo; se detecta en Fase 4.
- **Base de datos:** los tests de integración vacían la base de `DATABASE_URL`; solo con base descartable.
