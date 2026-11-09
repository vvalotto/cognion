# Contexto de Ejecución — US-ADJ-63

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-63.md`, Issue [#562](https://github.com/vvalotto/cognion/issues/562)
- **Origen:** prueba manual de despliegue en GCP, paso 13 (`quality/reports/uat/inc8-gcp/bitacora-despliegue.md`): bcrypt tarda 325 ms por verificación en la VM `e2-micro` y bloquea todo el event loop
- **Código existente:** `src/identidad/entities/ports/password_hasher_port.py`, `src/identidad/frameworks/security/password_hasher.py` (`BcryptPasswordHasher`), 9 puntos de uso en 8 casos de uso de Identidad; `ADR-014` (bcrypt)

## Historia de Usuario
- **ID:** US-ADJ-63 — El hash de contraseñas no bloquea el event loop
- **Tipo:** fix de rendimiento, backend (puerto y adaptador de hashing de Identidad); sin cambios en frontend ni de comportamiento funcional
- **Puntos:** 3 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 1 (rama `feature/inc-9-iter-1-correcciones`, un commit por US y un solo PR al cierre de la iteración)

## Decisiones de Ejecución
- **Diseño de la spec:** puerto asíncrono con bcrypt en `asyncio.to_thread`, sin cambiar costo, algoritmo ni formato (`ADR-014`).
- **Hallazgo de Fase 0 que condiciona el diseño:** el puerto lo implementan solo `BcryptPasswordHasher` y `FakePasswordHasher` (`tests/unit/inc1/_fakes.py`), pero **144 llamadas en 58 archivos de tests** usan `hash`/`verificar` de forma síncrona para sembrar usuarios (`BcryptPasswordHasher().hash("x")`, `hasher.hash("x")`). Convertir esos métodos en `async` obligaría a reescribir todas esas llamadas. Las opciones y la recomendación se plantean en la Fase 2.
- **Prueba de tiempo del event loop:** el criterio de la spec (hueco máximo < 120 ms con 3 verificaciones concurrentes) depende del reloj; se diseña con margen para no ser intermitente en el CI.
- **Probar con el hasher real**, no solo con fakes: el bloqueo es una propiedad de bcrypt verdadero.
- **Sin base de datos:** los tests nuevos no tocan la base. La regresión de login y recuperación se corre contra una base descartable (`DATABASE_URL` inline).
- **Fases:** todas, con BDD.

## Rutas
- Plan: docs/plans/inc9/US-ADJ-63-plan.md · Reporte: docs/reports/inc9/US-ADJ-63-report.md · Quality: quality/reports/inc9/US-ADJ-63-quality.json
- Feature: tests/features/inc9/US-ADJ-63-hash-no-bloquea.feature
