# Plan de Implementación: US-ADJ-15 - Fix de `coverage_report_path` en `[tool.architectanalyst]`

**Patrón:** N/A — config de tooling, transversal (no toca `src/`)
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-15-tracking.json`).
Fases 1, 4, 5, 6 y 7 omitidas (sin código de producción). Tiempo real acumulado sin
comparación contra estimación humana (`PRIN-001`).

## Lecciones Aprendidas

- 💡 Verificar con datos reales (correr `pytest --cov` y `architectanalyst` de punta a punta)
  en vez de confiar en la investigación previa de la spec dio la confirmación exacta: 98.9% de
  cobertura real reportado, no solo "el archivo se encuentra".
- 💡 Mismo patrón que `US-ADJ-13`: para una US de config de una línea sin código de producción,
  reducir el flujo a Fases 0, 2, 3, 8, 9 evita ceremonia sin valor.

## Componentes a Implementar

### 1. Config — `pyproject.toml`
- [x] `[tool.architectanalyst]`: agregado `coverage_report_path = "../coverage.json"` (relativo
  a `src/`, que es el `PATH` posicional que recibe el CLI — sube un nivel a la raíz del repo,
  donde `pytest --cov=src --cov-report=json` escribe `coverage.json`)

### 2. Documentación — `CLAUDE.md`
- [x] Nota operativa en "Quality gates → Notas operativas críticas": generar `coverage.json`
  (`pytest --cov=src --cov-report=json` desde la raíz del repo) *antes* de correr
  `architectanalyst` al cerrar una baseline — si no existe, `CoverageAnalyzer` reporta warning
  de archivo no encontrado en vez del porcentaje real.

## Verificación (reemplaza Fases 1/4/5/6/7 — sin código de producción ni tests)

- [x] Generar `coverage.json` en la raíz con `pytest --cov=src --cov-report=json` (739/739
  tests pasando)
- [x] Correr `architectanalyst src/ --config pyproject.toml` y confirmar que `CoverageAnalyzer`
  reporta severidad `info` con el porcentaje real de cobertura (98.9%), sin el warning "no se
  encontró el archivo de cobertura"

**Estado:** 3/3 tareas completadas
