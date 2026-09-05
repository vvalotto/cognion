# Contexto de Ejecución — US-4.2.3

## Fuentes
- **Fuente HU:** `docs/specs/inc4/US-4.2.3.md` (convención del proyecto, ver `docs/plans/inc4/inc4-candidatas.md`)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` §Arquitectura interna + `.claude/skills/implement-us/customizations/clean-architecture-bc.json`

## Historia de Usuario
- **ID:** US-4.2.3
- **Título:** PreguntaMetadatoConsultaPort hacia Banco de Preguntas
- **Tipo:** Nueva funcionalidad (técnica — puerto de consulta nuevo, sin comando ni evento de dominio)
- **Puntos:** 2
- **Prioridad:** Alta — bloquea `US-4.2.4` (tasa de error por tema, RF-17)

## Decisiones de Ejecución
- **BDD:** Sí — mismo precedente que `US-4.1.1`/`US-4.2.2` (técnicas): aunque no hay actor humano, el contrato del puerto (`obtener_metadatos`) se describe en Gherkin (`tests/features/inc4/US-4.1.1-infra-consulta-analytics.feature` como referencia de formato). Los criterios de aceptación ya vienen en Gherkin en la spec — se trasladan casi directo al `.feature`.
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
- Contexto: docs/plans/inc4/US-4.2.3-context.md
- Plan: docs/plans/inc4/US-4.2.3-plan.md
- Reporte: docs/reports/inc4/US-4.2.3-report.md
- Quality report: quality/reports/inc4/US-4.2.3-quality.json
