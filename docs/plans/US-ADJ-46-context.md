# Contexto de Ejecución — US-ADJ-46

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-46.md`
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna" + `docs/design/domain/BC-analytics-modelo.md` §8

## Historia de Usuario
- **ID:** US-ADJ-46
- **Título:** Docente consulta el ranking de preguntas más falladas
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5 (sin asignación formal, mismo criterio que el resto de Analytics)
- **Prioridad:** Tercera US de la Iteración 4 del Incremento 5-ADJ — implementada junto con
  `US-ADJ-45`/`47` en una sola ejecución/branch/PR (decisión de Víctor 2026-09-14)

## Decisiones de Ejecución
- **BDD:** Sí
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:** pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/US-ADJ-46-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-46-ranking-preguntas-falladas.feature
- Plan: docs/plans/US-ADJ-46-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-46-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-46-quality.json

## Notas específicas de esta US
- Reusa exactamente la fuente de `US-4.2.4` (`listar_respuestas_vigentes_de_materia`),
  cambiando la clave de agrupación de `(unidad_tematica, tema)` a `pregunta_id`.
- Amplía `MetadatoPreguntaResumen`/`PreguntaMetadatoConsultaPort` con el campo `enunciado`
  (mismo método `obtener_metadatos`, sin nuevo método).
- **Lecciones aplicadas de US-ADJ-44/45:**
  1. Si se amplía algún puerto con método nuevo, actualizar todos sus Fakes en la misma tarea.
  2. Si el Use Case combina agrupar + calcular + ordenar en un solo método, extraer a
     funciones de módulo desde el diseño (Fase 2), no esperar al CC CRITICAL de Fase 7.
  3. No correr otra suite de tests contra Postgres en paralelo con esta US.
