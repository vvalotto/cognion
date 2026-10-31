# Contexto de Ejecución — US-8.6.4

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.6.4.md`, Issue [#548](https://github.com/vvalotto/cognion/issues/548)
- **Fuente de lo que funcionó:** `quality/reports/uat/inc8-gcp/bitacora-despliegue.md` (cierre del paso a paso) y `docs/plans/DESPLIEGUE-GCP.md`
- **Arquitectura:** `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md`, `US-8.6.2` (`deploy/gcp/`)

## Historia de Usuario
- **ID:** US-8.6.4 — Scripts de aprovisionamiento, publicación y despliegue con rollback
- **Tipo:** tooling operativo / infraestructura (`deploy/gcp/`, `.github/workflows/`); sin código de producción
- **Puntos:** 5

## Decisiones de Ejecución
- **skip_bdd:** true — tooling; mismo precedente que `US-8.5.x` y `US-8.6.2`.
- **Fases a ejecutar:** 0, 2, 3, 4 (tests con ejecutables simulados + verificación real), 7, 8, 9. Sin 5/6.
- **Verificación sin tocar la nube:** los scripts se prueban con `gcloud`, `docker`, `curl` y `ssh` **simulados** (ejecutables falsos en el PATH de un test) que registran qué se les pidió. Así se comprueban orden, idempotencia, confirmaciones y rollback sin crear recursos.
- **Verificación real:** sobre la VM de la prueba (despliegue y rollback) y con una etiqueta temporal en CI (publicación). Cada acción real que cree o toque algo se confirma con Víctor antes.
- **Alcance real vs. simulado:** el escenario 1 ("proyecto limpio") se ensaya de verdad en `US-8.6.6` (instalación limpia); acá se verifica la idempotencia contra el proyecto existente.

## Hechos que condicionan el diseño
- El repositorio `vvalotto/cognion` es **público**: una imagen en GHCR puede ser pública (la VM la baja sin credenciales).
- La VM solo tiene el permiso `devstorage.read_only`; Artifact Registry no está habilitado.
- La imagen pesa 100,7 MB comprimida / 569 MB cargada; el artefacto de CI vence a las 24 h.
- `cd.yml` hoy construye la imagen en `main` y en etiquetas, pero no la publica.
- Las etiquetas del repositorio son hitos de baseline (`v0.8.1` es la última).

## Rutas
- Plan: docs/plans/inc8/US-8.6.4-plan.md · Reporte: docs/reports/inc8/US-8.6.4-report.md · Quality: quality/reports/inc8/US-8.6.4-quality.json
- Branch: `feature/US-8.6.4-scripts-aprovisionamiento-despliegue` (apilada sobre `US-8.6.3`); PR único al cierre de la Iteración 6.
