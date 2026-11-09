# Contexto de Ejecución — US-ADJ-68

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-68.md`, Issue [#594](https://github.com/vvalotto/cognion/issues/594)
- **Origen:** revisión del log de la VM de GCP tras la prueba real con estudiantes (2026-11-07)
- **Código existente:** `src/shared/frameworks/logging_config.py` (`US-ADJ-64`: `_TOKEN_EN_QUERY`, `_TOKEN_EN_RUTA`, `enmascarar_tokens`, `FiltroTokens`); la ruta con token es `GET /identidad/invitaciones/{token}` (`registro_router.py`, consumida por `Registro.tsx`)

## Historia de Usuario
- **ID:** US-ADJ-68 — El log de acceso no muestra el token de las invitaciones
- **Tipo:** mejora de seguridad, logging transversal (`shared/frameworks`); sin cambios en dominio, casos de uso ni frontend
- **Puntos:** 2 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 1 (rama `feature/inc-9-iter-1-correcciones`, un commit por US y un solo PR al cierre de la iteración)

## Decisiones de Ejecución
- **Una tercera expresión regular** junto a las dos existentes, aplicada dentro de `enmascarar_tokens`; mismo criterio que `/recuperar-password/<token>` (segmento de 20 o más caracteres de `[A-Za-z0-9_-]`). Los tokens reales tienen 43.
- **Probar con el proceso real** (`ServidorReal`, `uvicorn` como subproceso): `caplog` no alcanza (`US-ADJ-64`). Esos tests exigen una base descartable inline porque `tests/integration/conftest.py` vacía las tablas.
- **Los tests unitarios** de `enmascarar_tokens` y de `FiltroTokens` (argumentos `%s` de `uvicorn`) no tocan la base.
- **Sin cambios** en la API, en `frontend/` ni en `Registro.tsx`.
- **Fases:** todas, con BDD.

## Rutas
- Plan: docs/plans/inc9/US-ADJ-68-plan.md · Reporte: docs/reports/inc9/US-ADJ-68-report.md · Quality: quality/reports/inc9/US-ADJ-68-quality.json
- Feature: tests/features/inc9/US-ADJ-68-token-invitacion-log.feature
