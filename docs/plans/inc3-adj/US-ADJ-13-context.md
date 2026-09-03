# Contexto de Ejecución — US-ADJ-13

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-13.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture interna,
  perfil `clean-architecture-bc`) — no aplica al cambio en sí (documentación + config de
  herramienta de calidad, transversal, no toca `src/`)

## Historia de Usuario
- **ID:** US-ADJ-13
- **Título:** Documentar "Zone of Pain" de ArchitectAnalyst como falso positivo aceptado +
  limpiar claves inválidas de `[tool.architectanalyst]`
- **Tipo:** Documentación + corrección de config inválida (sin cambio de comportamiento —
  las claves corregidas nunca tuvieron efecto real)
- **Puntos:** 2
- **Prioridad:** Media (deuda de proceso repetida sin acción en 3 retros de baseline consecutivas)

## Decisiones de Ejecución
- **BDD:** No — no hay comportamiento de dominio ni de aplicación que ejercitar; es
  documentación + config de una herramienta de calidad externa (tabla de clasificación de
  Fase 0: más cercano a "Refactorización/eliminación de code smell documental" que a nueva
  funcionalidad).
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 8, 9 (se saltan 1, 4, 5, 6 y 7 — no hay código de producción
  que testear, lintear ni medir cobertura; la verificación de la Fase 3 es directa: correr
  `architectanalyst` y confirmar que el warning de clave desconocida desaparece)

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** N/A — el cambio es transversal (config de tooling +
  documentación), no toca ninguna capa de ningún BC
- **Umbrales de calidad:** N/A — sin código de producción ni tests nuevos. Verificación de
  aceptación: `architectanalyst src/ --config pyproject.toml` sin warnings de "clave
  desconocida ignorada".

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-13-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-13-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-13-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-13-quality.json`
