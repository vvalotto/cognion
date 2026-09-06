# Contexto de Ejecución — US-ADJ-18

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-18.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` — refactor interno de un gateway
  ya existente, sin cambio de contrato de `PreguntaRepositoryPort` ni de schema de BD

## Historia de Usuario
- **ID:** US-ADJ-18
- **Título:** Refactor `SQLAlchemyPreguntaRepository` (Feature Envy/Ley de Demeter/Long Method)
- **Tipo:** Refactor backend (sin cambio de comportamiento observable)
- **Puntos:** 5
- **Prioridad:** Alta — archivo con más issues concentrados del proyecto (15/159 antes de
  `US-ADJ-17`, que ya redujo `_a_entidad` parcialmente al introducir `MetadatosPregunta`)

## Estado de partida (post `US-ADJ-17`, ya mergeada)

`_a_entidad` ya usa `MetadatosPregunta.desde_valores_persistidos()` — más corto que antes,
pero `guardar`/`actualizar` siguen armando el modelo/aplicando cambios inline con
`if isinstance(...)/else`, y ambos siguen con `pregunta.dificultad.value`/
`pregunta.importancia.value` (profundidad 2).

## Decisiones de Ejecución
- **BDD:** No — refactorización sin cambio de comportamiento observable.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 5, 7, 8, 9 (se saltan 1, 4 y 6 — sin BDD, sin tests nuevos
  unitarios; Fase 5 corre los tests de integración existentes, que deben seguir pasando sin
  cambiar sus aserciones)
- **Alcance:** mapeadores privados por tipo concreto en `guardar`/`actualizar`/`_a_entidad`,
  más `dificultad_valor`/`importancia_valor` en `MetadatosPregunta` (ya existe el VO desde
  `US-ADJ-17`, no hace falta decidir dónde vive). `filtrar` con 7 parámetros queda **fuera de
  alcance** (lo dice la spec explícitamente).

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** Clean Architecture BC-first — mapeadores privados dentro del
  propio gateway (`frameworks`/`interface_adapters`, no se crea una capa nueva)
- **Umbrales de calidad:** los de siempre (mypy, pytest completo), más
  `designreviewer src/ --config pyproject.toml`: `pregunta_repository.py` baja de 15 a ≤2
  issues (el de `filtrar`/7 parámetros queda, fuera de alcance)

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-18-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-18-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-18-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-18-quality.json`
