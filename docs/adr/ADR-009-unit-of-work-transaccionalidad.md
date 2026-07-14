# ADR-009 — Unit of Work por Use Case (vs. transacciones manuales ad-hoc)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El escenario de calidad de Confiabilidad en `RNF_v1.md` exige que las respuestas de un examen
se persistan atómicamente ante cualquier interrupción. Un Use Case puede necesitar modificar
más de una entidad en la misma operación (ej. registrar una respuesta y actualizar el estado de
la sesión).

## Opciones Consideradas

- **Transacciones manuales ad-hoc por repositorio** — cada repositorio abre y cierra su propia
  transacción. Descartada: el riesgo de un commit parcial es real si algún Use Case nuevo se
  olvida de envolver manualmente todas sus escrituras.
- **Autocommit de SQLAlchemy por operación individual** — descartada: no garantiza atomicidad
  entre múltiples escrituras relacionadas dentro del mismo Use Case.
- **Unit of Work encapsulada por Use Case**, con una única sesión SQLAlchemy async por
  ejecución. Elegida.

## Decisión

Cada Use Case se ejecuta dentro de una única Unit of Work (una sesión SQLAlchemy async), con
commit único al finalizar o rollback automático ante cualquier excepción de dominio.

## Justificación

Garantiza que cualquier escritura múltiple dentro de un Use Case sea atómica, sin depender de
que cada desarrollador recuerde envolver manualmente cada operación en una transacción
explícita — la atomicidad queda resuelta a nivel de infraestructura, no de disciplina
individual.

## Impacto en Configuración

- `src/<bc>/use_cases/` — cada Use Case recibe una Unit of Work inyectada como dependencia.
- `src/<bc>/frameworks/` — implementación concreta de la Unit of Work sobre `AsyncSession` de
  SQLAlchemy.
- Sin dependencias nuevas en `pyproject.toml` — ya cubierto por ADR-004 (PostgreSQL +
  SQLAlchemy async).

## Consecuencias

- ✅ Atomicidad garantizada sin disciplina manual por desarrollador
- ✅ Rollback automático ante excepción de dominio
- ⚠️ Un Use Case no puede hacer commits parciales intencionales — si se necesitara, requeriría
  una Unit of Work explícitamente distinta
