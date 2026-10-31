# Reporte — US-8.6.4: Scripts de aprovisionamiento, publicación y despliegue con rollback

**Estado:** implementada en `feature/US-8.6.4-scripts-aprovisionamiento-despliegue` (2026-10-24), apilada en la Iteración 6. PR diferido al cierre de la iteración.
**Issue:** #548 · **Spec:** `docs/specs/inc8/US-8.6.4.md` · **Decisión:** `ADR-025`

## Qué se hizo
- `deploy/gcp/aprovisionar.sh` / `destruir.sh`: crean y borran proyecto, presupuesto, IP estática, regla 80/443 y VM `e2-micro`. Piden confirmación (`--si` la omite) y son idempotentes.
- `deploy/gcp/cognion.sh desplegar <imagen>` y `rollback`; `deploy/gcp/desplegar.sh` los dispara desde la Mac. Orden: bajar imagen, respaldo previo (si existe `respaldar.sh`), migrar con la imagen nueva mientras la vieja sirve, reemplazar y esperar `/api/health`; si no responde, vuelve sola a la anterior.
- `cd.yml`: publica la imagen en GHCR (público) solo con etiquetas `vX.Y.Z`. `imagen-smoke.yml` prueba imagen y composición en ramas de trabajo.

## Decisiones
- Rollback solo de imagen: no hay `downgrade` confiable (`US-8.3.4`).
- Fallar cerrado: si no se puede consultar presupuestos, aborta en vez de duplicarlo.
- GHCR en lugar de Cloud Build: la VM baja sin credenciales.

## Defectos hallados al probar contra recursos reales
- `default-allow-rdp` lo crea Google al habilitar Compute y quedaba abierto a internet: ahora se cierra tras habilitar las APIs.
- La API de presupuestos exige un proyecto de cuota: se usa `--billing-project` y se falla cerrado.
- Error de YAML en `cd.yml`, atrapado antes de subirlo.

## Calidad
145/145 tests en `tests/unit/inc8` (54 de esta US, con `gcloud` y `docker` simulados). ruff, black, isort limpios; pylint 10,00/10; CodeGuard completo sin advertencias reales (tras partir los tests en archivos con simuladores compartidos); mypy y DesignReviewer sin bloqueos. Verificación real en la VM: despliegue sano (corte ~10 s), rollback automático (~63 s) y manual (~6 s), publicación en GHCR y descarga anónima. Evidencia: `quality/reports/inc8/US-8.6.4-quality.json`, `quality/reports/uat/inc8-gcp/verificacion-us-8.6.4.md`.

## Pendiente
- Borrar la versión de prueba del paquete en GHCR (`gh api -X DELETE /user/packages/container/cognion/versions/1439899604`) después del primer release real: GitHub no deja borrar la última versión con etiqueta.
- Sin probar hasta `US-8.6.6`: creación desde un proyecto limpio.
