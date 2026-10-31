# Contexto de Ejecución — US-8.6.3

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.6.3.md`, Issue [#547](https://github.com/vvalotto/cognion/issues/547)
- **Fuente Arquitectura:** `CLAUDE.md`, `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md` (revisión 2026-10-23), `US-8.6.2` (`deploy/gcp/`)

## Historia de Usuario
- **ID:** US-8.6.3 — Plan de instalación y prueba manual del despliegue en GCP
- **Tipo:** plan + prueba manual (spike de despliegue); entrega un documento y una bitácora, sin código de producción
- **Puntos:** 5

## Decisiones de Ejecución
- **skip_bdd:** true — no hay código de producción; los escenarios de la spec se verifican con la propia bitácora.
- **Fases a ejecutar:** 0, 2, 3 (redactar el plan y el ajuste del workflow), 7 (verificación del cambio de CI), 8 (**revisión del plan por Víctor**), 9. La **ejecución manual** es posterior a la aprobación del plan y se registra en la bitácora.
- **La ejecución manual crea recursos reales y costo en la cuenta personal de Víctor:** ninguna acción se ejecuta sin su confirmación explícita previa.
- **Branch:** `feature/US-8.6.3-plan-instalacion-prueba` (apilada sobre `US-8.6.2`); PR único al cierre de la Iteración 6.

## Rutas
- Plan de la US: docs/plans/inc8/US-8.6.3-plan.md · Entregable: docs/plans/DESPLIEGUE-GCP.md
- Bitácora: quality/reports/uat/inc8-gcp/bitacora-despliegue.md · Reporte: docs/reports/inc8/US-8.6.3-report.md

## Notas
- Cuenta de facturación **paga y sin créditos** (`ADR-025`, revisión 2026-10-23): un recurso de más cuesta dinero.
- Todos los comandos del plan nacen como **sin probar**; cada uno pasa a **probado** cuando se ejecuta y queda en la bitácora.
