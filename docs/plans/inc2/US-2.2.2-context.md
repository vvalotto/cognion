# Contexto de Ejecución — US-2.2.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.2.md`
- **Fuente Arquitectura:** `CLAUDE.md` (raíz del repo) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.2.2
- **Título:** Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — RF-03, segunda US de la Iteración 2 del Incremento 2

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
- Contexto: docs/plans/inc2/US-2.2.2-context.md
- BDD feature: tests/features/inc2/US-2.2.2-listado-cuentas.feature
- Plan: docs/plans/inc2/US-2.2.2-plan.md
- Reporte: docs/reports/inc2/US-2.2.2-report.md
- Quality report: quality/reports/inc2/US-2.2.2-quality.json

## Notas de dominio (de la spec)
- BC: Identidad. Query de solo lectura, sin invariantes de dominio propias.
- `UsuarioRepositoryPort.listar(rol?, estado?, busqueda?) -> list[Usuario]` — filtros
  combinables AND; `busqueda` case-insensitive parcial contra `nombre` o `email`; `estado`
  acepta `activa` (`bloqueada=false`) o `bloqueada` (`bloqueada=true`).
- `ListarCuentasUseCase`, `CuentasController` nuevo (no reutiliza `AuthController` ni ningún
  controller existente), endpoint `GET /usuarios` (rol `administrador`).
- Sin frontend propio — cubierto por US-2.2.6.
