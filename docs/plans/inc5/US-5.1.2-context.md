# Contexto de Ejecución — US-5.1.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc5/US-5.1.2.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md`, `docs/architecture/`, `CLAUDE.md` §"Arquitectura interna" — decididos, no se re-consulta con el usuario (regla operativa del proyecto)

## Historia de Usuario
- **ID:** US-5.1.2
- **Título:** Notificación de apertura de una Actividad Evaluativa de período abierto
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5 (sin estimación explícita en `inc5-candidatas.md` — placeholder, no afecta métricas de correlación ya documentadas)
- **Prioridad:** Secuencial dentro de la Iteración 1 (`US-5.1.1` → `US-5.1.2` → `US-5.1.3`, sin paralelismo)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación en Gherkin ya redactados en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ (calibrado por incremento, ver `pyproject.toml`)
  - MI ≥ (calibrado por incremento, ver `pyproject.toml`)
  - cobertura ≥ 90% (umbral base del perfil; el proyecto viene sosteniendo 99-100% en US-IEDD backend recientes)

## Rutas de Artefactos
- Contexto: `docs/plans/inc5/US-5.1.2-context.md`
- BDD feature: `tests/features/inc5/US-5.1.2-notificacion-apertura.feature`
- Plan: `docs/plans/inc5/US-5.1.2-plan.md`
- Reporte: `docs/reports/inc5/US-5.1.2-report.md`
- Quality report: `quality/reports/inc5/US-5.1.2-quality.json`

## Notas de contexto adicionales
- Depende de `US-5.1.1` (infraestructura del BC Notificaciones), ya cerrada y mergeada a `develop`.
- Primer cableado real de integración directa entre BCs disparada desde un Use Case de escritura (`ADR-006`). Vigilar CBO de `CrearActividadPeriodoAbiertoUseCase` al inyectar `NotificacionPort` — mismo patrón de CRITICAL visto repetidamente en el proyecto (ver spec, sección "Impacto arquitectónico").
- Issue asociado: [#308](https://github.com/vvalotto/cognion/issues/308)
