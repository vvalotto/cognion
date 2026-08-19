# Contexto de Ejecución — US-2.2.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.1.md`
- **Fuente Arquitectura:** `CLAUDE.md` (raíz del repo) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.2.1
- **Título:** Bloqueo automático de cuenta por 3 intentos fallidos consecutivos de login
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — base de la que depende el resto de la Iteración 2 (Incremento 2)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya incluye escenarios Gherkin completos en Criterios de aceptación
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc2/US-2.2.1-context.md
- BDD feature: tests/features/US-2.2.1-bloqueo-cuenta-login.feature
- Plan: docs/plans/inc2/US-2.2.1-plan.md
- Reporte: docs/reports/inc2/US-2.2.1-report.md
- Quality report: quality/reports/inc2/US-2.2.1-quality.json

## Notas de dominio (de la spec)
- BC: Identidad. Aggregate afectado: `Usuario`.
- Agrega a `Usuario`: `bloqueada: bool`, `intentos_fallidos_login: int`,
  `intentos_fallidos_password: int` (defaults `False`/`0`/`0`).
- Nuevo evento `CuentaBloqueada`, nuevo error `CuentaBloqueadaError`.
- Extiende `IniciarSesionUseCase` (US-1.1.4): verifica `bloqueada` antes de la contraseña;
  cuenta fallos/aciertos; emite `CuentaBloqueada` al llegar a 3.
- Migración Alembic nueva con backfill (`bloqueada=false`, contadores en 0).
- Sin frontend propio — cubierto por US-2.2.9.
