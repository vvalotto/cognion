# Contexto de Ejecución — US-6.3.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.2.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna") + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-6.3.2
- **Título:** Listar las sesiones en vivo de una Comisión
- **Tipo:** Nueva funcionalidad (consulta nueva, sin comando ni evento de dominio)
- **Puntos:** 3
- **Prioridad:** Alta — bloquea `US-6.3.5` (Docente) y `US-6.3.8` (Estudiante)

## Decisiones de Ejecución
- **BDD:** Sí — la spec trae 9 escenarios Gherkin completos
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (histórico del proyecto: ≥ 9.0 en Incremento 6)
  - CC ≤ 10 (histórico del proyecto: ≤ 8)
  - MI ≥ 20 (histórico del proyecto: ≥ 40)
  - cobertura ≥ 95%
  - CBO ≤ 10 / WMC ≤ 25 (`pyproject.toml [tool.designreviewer]`, pre-push, bloqueante)

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.2-context.md`
- BDD feature: `tests/features/inc6/US-6.3.2-listar-sesiones-en-vivo-comision.feature`
- Plan: `docs/plans/inc6/US-6.3.2-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.2-report.md`
- Quality report: `quality/reports/inc6/US-6.3.2-quality.json`

## Notas propias de esta US
- **CBO a vigilar:** `SesionesEnVivoQueryController` ya tiene 3 use cases (`US-6.2.8`) — la spec pide controller propio si el 4° hace saltar el CBO.
- **Sin proyección sincronizada:** el adapter lee la tabla `events` directamente (primer evento = comisión, último = estado), mismo criterio que `EvaluacionActivaQueryPort` (`US-3.2.4`) — válido a esta escala (una sesión activa por Comisión a la vez).
