# Contexto de Ejecución — US-ADJ-47

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-47.md`
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna" + `docs/design/domain/BC-analytics-modelo.md` §8

## Historia de Usuario
- **ID:** US-ADJ-47
- **Título:** Docente consulta la completitud de una actividad puntual
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5 (sin asignación formal, mismo criterio que el resto de Analytics)
- **Prioridad:** Cuarta y última US de la Iteración 4 del Incremento 5-ADJ backend — cierra
  completa la Iteración 4 backend (`US-ADJ-44` a `47`). Implementada junto con
  `US-ADJ-44`/`45`/`46` en una sola ejecución/branch/PR (decisión de Víctor 2026-09-14)

## Decisiones de Ejecución
- **BDD:** Sí
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:** pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/US-ADJ-47-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-47-completitud-por-actividad.feature
- Plan: docs/plans/US-ADJ-47-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-47-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-47-quality.json

## Notas específicas de esta US
- Amplía `EvaluacionDesempenoConsultaPort` con `obtener_actividad_resumen` (materia_id +
  comisiones_ids de la actividad) y `listar_estados_de_actividad` (estado de cada estudiante:
  en_curso/suspendida/finalizada, ausente = sin_iniciar).
- Reusa el cruce hacia `ActividadEvaluativaPeriodoAbierto` ya introducido en `US-ADJ-44`
  (`.reconstruir()`).
- Roster: comisión(es) restringida(s) de la actividad, o toda la materia si `comisiones_ids`
  vacío (unión de comisiones vía `ComisionConsultaPort`).
- **Lecciones aplicadas de US-ADJ-44/45/46:**
  1. Actualizar todos los Fakes del puerto en la misma tarea que lo amplía.
  2. Extraer agregación/orden a función de módulo desde el diseño si el método combina más de
     un paso.
  3. Correr `designreviewer` local antes de commitear si se agrega un Use Case a un controller
     que ya tiene 4+ (evitar el CRITICAL de CBO descubierto en `US-ADJ-46` — usar
     `AnalyticsInformesController`, que ya tiene 4, para el 5° en vez de crear uno nuevo, o
     evaluar de nuevo el CBO resultante).
  4. No correr otra suite de tests contra Postgres en paralelo.
