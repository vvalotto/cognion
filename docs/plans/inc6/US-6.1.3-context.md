# Contexto de Ejecución — US-6.1.3

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.1.3.md`, GitHub Issue [#384](https://github.com/vvalotto/cognion/issues/384)
- **Fuente Arquitectura:** `CLAUDE.md` (§Arquitectura interna — reglas no negociables) + `docs/design/domain/BC-actividad-evaluativa-modelo.md` §12–§17

## Historia de Usuario
- **ID:** US-6.1.3
- **Título:** Estudiante se une a una sesión en vivo
- **Tipo:** Nueva funcionalidad (feature backend)
- **Puntos:** 3 (la spec no lo declara; mismo valor que `US-6.1.1`/`US-6.1.2` de la iteración)
- **Prioridad:** Alta — bloquea `US-6.1.4` y la Iteración 2

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con 5 escenarios Gherkin ya redactados en la spec.
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (el proyecto viene sosteniendo ≥9.0)
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6/US-6.1.3-context.md
- BDD feature: tests/features/inc6/US-6.1.3-unirse-sesion-en-vivo.feature
- Plan: docs/plans/inc6/US-6.1.3-plan.md
- Reporte: docs/reports/inc6/US-6.1.3-report.md
- Quality report: quality/reports/inc6/US-6.1.3-quality.json

## Notas específicas del proyecto (no genéricas del skill)
- Rutas de plan/contexto/reporte/quality en subcarpeta `incN/`, no en la raíz.
- `codeguard` en Fase 7: `--analysis-type full`, con `PATH="$PWD/.venv/bin:$PATH"`, y **en
  serie** (no en paralelo a la suite completa). `designreviewer` con `--config pyproject.toml`.
- **Correr la suite completa (`tests/`) antes de dar por buena la Fase 7**, no solo los tests
  de la US (lección de `US-6.1.2`: datos huérfanos entre directorios solo aparecen ahí).
  `tests/integration/inc6/conftest.py` ya limpia `events`/`pregunta_plantilla`/`banco`/`materia`.
- En zsh, expandir listas de archivos con `${=VAR}` o `$(cat archivo)`.
- CBO: `SesionesEnVivoController` tiene hoy 1 use case; evaluar en Fase 2 si un 2° cabe o
  conviene un controller propio.
- **Punto de diseño para Fase 2:** los escenarios "sesión EnCurso" y "sesión Finalizada" no se
  pueden producir por API todavía (`IniciarSesionEnVivo` es `US-6.1.4`, finalizar es Iteración
  2). Definir cómo se siembra ese estado en tests y qué eventos debe entender
  `ActividadEvaluativaEnVivo.reconstruir()` (diferido desde `US-6.1.2`).
- `tests/uat/datos-reales/` y los trackers no se commitean.
