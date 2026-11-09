# Plan de Implementación: US-9.4.2 - Actividad Evaluativa deja de leer `UsuarioModel` de Identidad

**Patrón:** clean-architecture-bc · **Producto:** cognion · **Capas:** `identidad` (entities/ports, interface_adapters/gateways) y `actividad_evaluativa` (frameworks/adapters)

## Diseño
`EstudianteConsultaPortInProcess.obtener_nombres` hace `select(UsuarioModel.id, UsuarioModel.nombre).where(id.in_(ids))`. Pasa a delegar en el puerto de consultas de cuentas de Identidad.

```
antes:  adaptador (actividad_evaluativa) ──select UsuarioModel──► tabla usuario                 (viola ADR-026)
después: adaptador ──► CuentaQueryPort.obtener_nombres ──► SQLAlchemyCuentaQueryRepository ──► tabla usuario
```

- **Ajuste al implementar:** el plan ponía el método en `CuentaQueryPort`, pero subía el CBO de su gateway a 11/10 (CRITICAL). Se creó `NombreUsuarioQueryPort` con su gateway `SQLAlchemyNombreUsuarioQueryRepository` y `CuentaQueryPort` no se tocó.
- Sin cambios en casos de uso (`_resolucion_nombres.py`), API ni frontend. Comportamiento: una consulta por lote, ids sin cuenta no aparecen, lista vacía devuelve `{}` sin consultar.

## Componentes a Implementar

### 1. Proveedor — Identidad
- [ ] `src/identidad/entities/ports/cuenta_query_port.py`: método abstracto `obtener_nombres(ids: list[UUID]) -> dict[UUID, str]` con docstring.
- [ ] `src/identidad/interface_adapters/gateways/cuenta_query_repository.py`: implementación (corto circuito con `{}` si `ids` está vacío; un `SELECT id, nombre ... WHERE id IN`).

### 2. Consumidor — Actividad Evaluativa
- [ ] `estudiante_consulta_port_in_process.py`: `obtener_nombres` delega en `SQLAlchemyCuentaQueryRepository(session)`; se quitan los imports de `select` y `UsuarioModel`; docstrings actualizados.

### 3. Regla de imports
- [ ] `pyproject.toml`: borrar la línea `ignore_imports` marcada `# #601`.

## Tests (Fases 4 y 5)
- **Primero, antes de tocar `src/` (caracterización, `tests/integration/inc9/test_us_9_4_2_estudiante_consulta_integration.py`):** lista vacía, ids existentes, id inexistente, una sola sentencia SQL (evento `before_cursor_execute`), y `existe` / `obtener_comision_id` intactos. En verde antes y después. Primer commit.
- **Integración del gateway** (`tests/integration/inc1/...` o el archivo de cuentas existente): casos de `obtener_nombres`.
- **Unitarios:** `FakeCuentaQueryRepository` implementa el método nuevo; se corre `tests/unit` completo.
- `uv run lint-imports` y mypy en verde.

## Documentación (Fase 8)
- Spec `US-9.4.2` → `Implementada`; `ADR-026`: caso 2 migrado.

## Riesgos
- **CBO del gateway de cuentas** (se mide en el pre-push); el método no suma dependencias.
- **Otros fakes de `CuentaQueryPort`:** si alguno queda sin el método, falla al instanciarlo; se detecta en Fase 4.
