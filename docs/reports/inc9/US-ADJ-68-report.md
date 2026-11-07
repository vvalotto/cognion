# Reporte — US-ADJ-68: El log de acceso no muestra el token de las invitaciones

**Estado:** implementada en `feature/inc-9-iter-1-correcciones` (2026-11-07), un commit por US; el PR sale al cierre de la Iteración 1.
**Issue:** [#594](https://github.com/vvalotto/cognion/issues/594) · **Spec:** `docs/specs/ajustes/US-ADJ-68.md` · **Origen:** revisión del log de la VM de GCP tras la prueba real con estudiantes (2026-11-06)

## Qué se hizo
- `src/shared/frameworks/logging_config.py`: nueva expresión regular `_TOKEN_EN_RUTA_INVITACION` (`/invitaciones/` seguido de 20 o más caracteres de `[A-Za-z0-9_-]`) que `enmascarar_tokens` aplica junto a las dos existentes (`token=` y `/recuperar-password/<token>`, de `US-ADJ-64`). `GET /api/identidad/invitaciones/<token>` queda registrado como `GET /api/identidad/invitaciones/***`; el método, el estado y el resto de la línea no cambian.
- Sin cambios en la API, el dominio, los casos de uso ni `frontend/`.

## Decisiones
- Mismo criterio de token que `/recuperar-password/` (20 o más caracteres): los tokens reales tienen 43.
- Probado con el proceso real (`ServidorReal`, un `uvicorn` como subproceso) además de las pruebas unitarias: `caplog` dejó pasar el error original de `US-ADJ-64`.
- Una consecuencia anotada para `US-ADJ-67` (#590): si esa US agrega una ruta `/invitaciones/<uuid>`, el UUID de 36 caracteres también quedaría enmascarado. Es inocuo; esa US decide si distingue.

## Hallazgo al probar
`ServidorReal.salida` es un método, no una propiedad. Los steps BDD la usaban sin paréntesis y fallaban con `TypeError`; corregido. Además CodeGuard señaló dos líneas de comentario de más de 100 caracteres (`pylint` había bajado a 9,44); acortadas, `pylint` vuelve a 10,00.

## Calidad
13 unitarios (sin base), 5 de integración y 6 escenarios BDD, todos en verde; los 37 unitarios de logging (`US-ADJ-64` + `US-ADJ-68`) y los 29 de integración/BDD de logging pasan contra una base descartable. Con el filtro anterior fallan 9 de los 13 unitarios y 3 de los 5 de integración (los que pasan son los que no deben cambiar). `pylint` 10,00/10, `mypy` 0 errores (315 archivos), `ruff`/`black`/`isort` limpios, `bandit` sin problemas, CC promedio A (3,5), MI 85,85 (A). La suite completa se corre una sola vez al cerrar la Iteración 1. Evidencia: `quality/reports/inc9/US-ADJ-68-quality.json`.

## Tiempo
Ver `.claude/tracking/US-ADJ-68-tracking.json`.

## Pendiente
- Los logs ya escritos (VM de GCP, prueba del 2026-11-06) conservan tokens: esta US no los reescribe. Esa base es de prueba para desechar.
- Eliminar la base descartable `cognion_dg_descartable` al cerrar la iteración.
