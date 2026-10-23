# Contexto de Ejecución — US-8.6.2

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.6.2.md`, Issue [#546](https://github.com/vvalotto/cognion/issues/546)
- **Fuente Arquitectura:** `CLAUDE.md`, `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md`, `ADR-018` (NullPool), `US-8.1.4`/`8.1.5`/`8.1.6`

## Historia de Usuario
- **ID:** US-8.6.2 — Composición de servicios y configuración de la VM
- **Tipo:** tooling operativo / infraestructura (`deploy/gcp/`), con un ajuste de `Dockerfile` y un workflow de CI
- **Puntos:** 5

## Decisiones de ADR-025 que aplican
Contenedores (decisión 3), `ENTORNO=local` + `EMAIL_MODO=consola` (decisión 2), URL de DuckDNS con HTTPS automático por el proxy (decisión 1).
Condición de la decisión 3: probar el arranque de la imagen contra una base descartable antes de aprovisionar la VM.

## Decisiones de Ejecución
- **skip_bdd:** true — tooling; mismo precedente que `US-8.5.x`. Se cubre con tests estáticos de la composición y con una verificación en CI.
- **Fases a ejecutar:** 0, 2, 3, 4 (tests estáticos + verificación en CI), 7, 8, 9. Sin 5/6.
- **Sin Docker local:** la verificación de runtime corre en GitHub Actions (workflow aparte con filtro de rutas, para no alargar los demás PRs).
- **Alcance de la verificación:** reinicio tras apagar la VM, memoria real en 1 GB y acceso externo solo se verifican en la VM (`US-8.6.3`/`8.6.6`/`8.6.7`); en CI se verifican los equivalentes a nivel contenedor.

## Perfil Activo
- clean-architecture-bc; umbrales: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95 %

## Rutas
- Plan: docs/plans/inc8/US-8.6.2-plan.md · Reporte: docs/reports/inc8/US-8.6.2-report.md
- Quality: quality/reports/inc8/US-8.6.2-quality.json

## Notas
- Branch: `feature/US-8.6.2-composicion-servicios`; PR único al cierre (CI lento).
- No correr integración/BDD contra la base de desarrollo; `tests/unit/` es seguro.
