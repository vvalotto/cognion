# Contexto de Ejecución — US-2.2.4

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.4.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md` + ADRs (`ADR-012` a `ADR-014`,
  `ADR-017`, `ADR-019`) + `CLAUDE.md` §"Arquitectura interna"

## Historia de Usuario
- **ID:** US-2.2.4
- **Título:** Administrador resetea la contraseña de una cuenta (desbloqueo incluido)
- **Tipo:** Nueva funcionalidad
- **Puntos:** 2
- **Prioridad:** Iteración 2 del Incremento 2 (RF-03)

## Decisiones de Ejecución
- **BDD:** Sí — comando de dominio nuevo con invariante nueva (`INV-ID-11`) y dos eventos
  nuevos (`PasswordReseteada`, `CuentaDesbloqueada`); comportamiento observable con múltiples
  escenarios de negocio.
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases →
  interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%
  - CBO ≤ 10 (gate de pre-push, DesignReviewer)

## Rutas de Artefactos
- Contexto: docs/plans/inc2/US-2.2.4-context.md
- BDD feature: tests/features/inc2/US-2.2.4-resetear-password.feature
- Plan: docs/plans/inc2/US-2.2.4-plan.md
- Reporte: docs/reports/inc2/US-2.2.4-report.md
- Quality report: quality/reports/inc2/US-2.2.4-quality.json
