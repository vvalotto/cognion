# US-9.4.3: Identidad deja de leer el event store de Actividad Evaluativa

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 4
**Tipo**: `refactor` backend (sin cambio de comportamiento)
**Agregado principal afectado**: ninguno
**Bounded Context**: Identidad (consumidor), Actividad Evaluativa (proveedor)
**Origen**: `ADR-026` (#498), caso 3 de 3.
**Issue**: [#602](https://github.com/vvalotto/cognion/issues/602)
**Interactúa con**: `US-9.4.1` (#600), `US-9.4.2` (#601), `eliminar_cuenta` (`RF-03`), contrato `import-linter` de `pyproject.toml`.

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de mantener Cognión**,
quiero **que Identidad pregunte a Actividad Evaluativa si un estudiante tiene evaluaciones, en vez de leer su tabla de eventos**,
para **que un cambio en cómo Actividad Evaluativa guarda sus eventos se detecte con sus propios tests y no rompa a Identidad sin aviso**.

---

## Contexto

`identidad/frameworks/adapters/evaluacion_consulta_port_in_process.py` importa `EventoModel` de
`actividad_evaluativa.frameworks.db.models`, y para `tiene_evaluaciones(estudiante_id)` (lo usa `eliminar_cuenta`: no se puede
eliminar a un estudiante con evaluaciones) consulta el event store: trae el `payload` de **todos** los eventos
`Evaluacion/EvaluacionIniciada` y filtra en memoria por `payload["estudiante_id"]`.

Actividad Evaluativa no expone hoy una consulta equivalente. El patrón del BC para consultas de solo lectura sobre el event
store es un puerto en `entities/ports/` (`EvaluacionEstudianteQueryPort`, `EvaluacionActivaQueryPort`, …) con un gateway en
`frameworks/adapters/` que lee `EventoModel`.

## Especificacion del comportamiento

- Actividad Evaluativa agrega el puerto `EstudianteEvaluacionesQueryPort` con `tiene_evaluaciones_iniciadas(estudiante_id) -> bool`:
  `True` si el estudiante inició alguna vez una evaluación (cualquier estado). Lo implementa
  `SQLAlchemyEstudianteEvaluacionesQueryRepository` en `frameworks/adapters/`, con la misma lógica de hoy (filtro en memoria del
  `payload`, sin operadores JSONB, por consistencia con el resto del proyecto).
- `EvaluacionConsultaPortInProcess.tiene_evaluaciones` delega en ese gateway.
- El adaptador deja de importar `actividad_evaluativa.frameworks.db.models`.
- Se borra de `pyproject.toml` la línea de `ignore_imports` marcada `# #602`; `uv run lint-imports` sigue en verde.
- **El comportamiento observable no cambia.**

## Escenarios (BDD)

1. **Estudiante sin evaluaciones.** `tiene_evaluaciones` devuelve `False`.
2. **Estudiante con una evaluación iniciada.** Devuelve `True`, sea cual sea su estado posterior.
3. **Otro estudiante.** Las evaluaciones de otro no cuentan.
4. **Otros eventos.** Eventos de otro tipo o de otro agregado con el mismo `estudiante_id` no cuentan.
5. **`eliminar_cuenta` intacto.** Un estudiante con evaluaciones sigue sin poder eliminarse.
6. **Regla de imports.** Sin la línea `# #602`, `lint-imports` no reporta violaciones.

## Fuera de alcance

Optimizar la consulta (traer todos los payloads es O(n) en eventos; la mejora con índices o JSONB es otra decisión); cambiar la
semántica de `eliminar_cuenta`; migrar los adaptadores de Analytics (excepción de `ADR-026`).

## Notas para `/implement-us`

- **Primer commit: test de caracterización** del adaptador actual (integración, base descartable inline en `DATABASE_URL`), que
  pasa antes y después (escenarios 1 a 4). Los eventos se cargan con `SQLAlchemyEventStore`.
- Test de integración del gateway nuevo en Actividad Evaluativa y fake nuevo solo si algún test unitario lo necesita.
- El adaptador de Identidad puede importar el gateway de otro BC: `frameworks/adapters/` es la única capa autorizada (`ADR-006`).
