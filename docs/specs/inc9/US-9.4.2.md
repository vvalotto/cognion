# US-9.4.2: Actividad Evaluativa deja de leer el modelo ORM de usuarios de Identidad

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 4
**Tipo**: `refactor` backend (sin cambio de comportamiento)
**Agregado principal afectado**: ninguno
**Bounded Context**: Actividad Evaluativa (consumidor), Identidad (proveedor)
**Origen**: `ADR-026` (#498), caso 2 de 3.
**Issue**: [#601](https://github.com/vvalotto/cognion/issues/601)
**Interactúa con**: `US-9.4.1` (#600), `US-9.4.3` (#602), `US-6.3.1` (nombres en el canal en vivo), contrato `import-linter` de `pyproject.toml`.

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de mantener Cognión**,
quiero **que Actividad Evaluativa obtenga los nombres de los estudiantes a través de Identidad y no leyendo su tabla de usuarios**,
para **que un cambio de esquema en Identidad se detecte con los tests de Identidad y no rompa a su vecino sin aviso**.

---

## Contexto

`actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py` importa `UsuarioModel` de
`identidad.frameworks.db.models` solo para `obtener_nombres(ids)`, que resuelve los nombres de un lote de ids en una única
consulta (`US-6.3.1`; lo usa `_resolucion_nombres.py` en el canal en vivo). Los otros dos métodos (`existe`,
`obtener_comision_id`) ya usan `SQLAlchemyUsuarioRepository`.

Ni `UsuarioRepositoryPort` ni `ComisionQueryPort` ofrecen un lote de nombres. `CuentaQueryPort` es el puerto de consultas de
solo lectura sobre cuentas (separado de `UsuarioRepositoryPort` por command/query): es donde corresponde.

## Especificacion del comportamiento

- Identidad agrega a `CuentaQueryPort` el método `obtener_nombres(ids) -> dict[UUID, str]`: devuelve `{id: nombre}` para los
  ids que existen, en **una sola consulta**; los ids sin cuenta no aparecen; lista vacía → `{}` sin consultar la base. Lo
  implementa `SQLAlchemyCuentaQueryRepository`.
- `EstudianteConsultaPortInProcess.obtener_nombres` delega en ese método.
- El adaptador deja de importar `identidad.frameworks.db.models`.
- Se borra de `pyproject.toml` la línea de `ignore_imports` marcada `# #601`; `uv run lint-imports` sigue en verde.
- **El comportamiento observable no cambia.**

## Escenarios (BDD)

1. **Lista vacía.** `obtener_nombres([])` devuelve `{}`.
2. **Ids existentes.** Devuelve el nombre de cada uno.
3. **Id inexistente.** No aparece en el resultado; los demás sí.
4. **Una sola consulta.** Resolver varios ids ejecuta una única sentencia SQL.
5. **`existe` y `obtener_comision_id` intactos.**
6. **Regla de imports.** Sin la línea `# #601`, `lint-imports` no reporta violaciones.

## Fuera de alcance

Cambiar `existe` / `obtener_comision_id`; migrar los otros adaptadores (`US-9.4.1`, `US-9.4.3`); el resto de las consultas de cuentas.

## Notas para `/implement-us`

- **Primer commit: test de caracterización** del adaptador actual (integración, base descartable inline en `DATABASE_URL`),
  que pasa antes y después (escenarios 1 a 5). El escenario 4 se verifica contando sentencias con un evento de SQLAlchemy.
- Test de integración de `obtener_nombres` en el gateway y fake actualizado (`FakeCuentaQueryRepository`, `tests/unit/inc1/_fakes.py`).
- Cuidar el CBO del gateway de cuentas (pre-push).
