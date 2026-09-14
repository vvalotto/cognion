# Contexto de Ejecución — US-ADJ-49

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-49.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas de capas) + `docs/design/ux/wireframes-analytics.md` §3.3 — sin capas de dominio aplicables (frontend puro)

## Historia de Usuario
- **ID:** US-ADJ-49
- **Título:** Docente ve la evolución temporal de un estudiante y de su comisión
- **Tipo:** Nueva funcionalidad (frontend puro, consume backend ya cerrado en `US-ADJ-45`)
- **Puntos:** 5 (sin asignación formal, mismo criterio que el resto de Analytics)
- **Prioridad:** Segunda US de la Iteración 4 frontend del Incremento 5-ADJ — par backend→frontend de RF-21

## Decisiones de Ejecución
- **BDD:** No — frontend puro, mismo criterio que `US-ADJ-48`
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se omiten 1 y 6)
- **Verificación manual en navegador:** diferida al cierre de la Iteración 4 completa (decisión
  de Víctor 2026-09-14, ver `feedback_uat_navegador_solo_cierre_iteracion` en memoria) — no se
  repite por cada US de esta iteración.

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (no aplica a esta US — frontend puro)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (N/A — sin código Python en esta US)
  - CC ≤ 10 (N/A)
  - MI ≥ 20 (N/A)
  - cobertura ≥ 95% (aplica a `frontend/`, vía Vitest — umbral de branches del proyecto: 80% global)

## Rutas de Artefactos
- Contexto: docs/plans/inc5-adj/US-ADJ-49-context.md
- BDD feature: N/A (skip_bdd)
- Plan: docs/plans/inc5-adj/US-ADJ-49-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-49-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-49-quality.json
