# US-9.4.1: Banco de Preguntas deja de leer el modelo ORM de comisiones de Identidad

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 4
**Tipo**: `refactor` backend (sin cambio de comportamiento)
**Agregado principal afectado**: ninguno
**Bounded Context**: Banco de Preguntas (consumidor), Identidad (proveedor)
**Origen**: `ADR-026` (#498), caso 1 de 3.
**Issue**: [#600](https://github.com/vvalotto/cognion/issues/600)
**Interactúa con**: `US-9.4.2` (#601), `US-9.4.3` (#602), `US-ADJ-57`, contrato `import-linter` de `pyproject.toml`.

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de mantener Cognión**,
quiero **que Banco de Preguntas consulte las comisiones a través de Identidad y no leyendo sus tablas**,
para **que un cambio de esquema en Identidad se detecte con los tests de Identidad y no rompa a su vecino sin aviso**.

---

## Contexto

`banco_preguntas/frameworks/adapters/comision_consulta_port_in_process.py` importa `ComisionModel` de
`identidad.frameworks.db.models` solo para `tiene_comisiones(materia_id)` (¿alguna comisión, activa o no, referencia la
materia?; lo usa `eliminar_materia`). El otro método, `esta_asignado_a_materia`, ya delega en
`SQLAlchemyComisionQueryRepository` de Identidad.

`ComisionQueryPort` de Identidad no tiene una consulta equivalente: `listar_comisiones_por_materia(incluir_inactivas=True)`
trae las comisiones completas con sus docentes (`selectinload`), demasiado para un chequeo de existencia.

## Especificacion del comportamiento

- Identidad agrega a `ComisionQueryPort` el método `existe_comision_en_materia(materia_id) -> bool`: `True` si hay al menos
  una comisión, activa o no, con esa materia. Lo implementa `SQLAlchemyComisionQueryRepository` con la misma consulta
  (`SELECT id ... LIMIT 1`).
- `ComisionConsultaPortInProcess.tiene_comisiones` delega en ese método.
- El adaptador deja de importar `identidad.frameworks.db.models` y de recibir/usar `session` para consultas propias.
- Se borra de `pyproject.toml` la línea de `ignore_imports` marcada `# #600`; `uv run lint-imports` sigue en verde.
- **El comportamiento observable no cambia.**

## Escenarios (BDD)

1. **Materia sin comisiones.** `tiene_comisiones` devuelve `False`.
2. **Materia con una comisión activa.** Devuelve `True`.
3. **Materia solo con comisiones deshabilitadas.** Devuelve `True`.
4. **Otra materia.** Las comisiones de una materia no afectan a otra.
5. **Autorización intacta.** `esta_asignado_a_materia` se comporta igual que antes.
6. **Regla de imports.** Sin la línea `# #600` en `ignore_imports`, `lint-imports` no reporta violaciones.

## Fuera de alcance

Cambiar `esta_asignado_a_materia`; migrar los otros adaptadores (`US-9.4.2`, `US-9.4.3`); los fakes de otros BC más allá de
sumar el método nuevo donde implementan `ComisionQueryPort`.

## Notas para `/implement-us`

- **Primer commit: test de caracterización** del adaptador actual (integración, base descartable inline en `DATABASE_URL`),
  que pasa antes y después de la migración (escenarios 1 a 5).
- Después, test de integración del método nuevo en `tests/integration/inc4/test_comision_query_repository.py` y actualizar
  los `Fake*` que implementan `ComisionQueryPort` (`tests/unit/inc1/_fakes.py`, `tests/unit/inc4/test_comisiones_query_controller.py`).
- Cuidar el CBO del gateway de Identidad (pre-push).
