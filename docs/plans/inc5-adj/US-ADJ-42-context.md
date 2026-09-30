# Contexto de Ejecución — US-ADJ-42

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-42.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (reglas de capas Clean Architecture
  BC-first, capas `entities/use_cases/interface_adapters/frameworks`)

## Historia de Usuario
- **ID:** US-ADJ-42
- **Título:** Autoregistro de Estudiante (endpoint público)
- **Tipo:** Nueva funcionalidad (backend nuevo, endpoint público)
- **Puntos:** 3
- **Prioridad:** Segunda US de la Iteración 3 del Incremento 5-ADJ (autoregistro con selección
  de perfil). Depende de `US-ADJ-41` (mismo patrón de endpoint, hermano por perfil, ya cerrada
  — `UsuarioAutoregistrado` y `AutoregistroController`/`autoregistro_router.py` ya existen).
  `US-ADJ-43` (pantalla) sigue a esta.

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad de dominio con invariantes propias (INV-ID-14 comisión
  existente, INV-ID-15 perfil no admite Administrador, INV-ID-16 activa de inmediato), mismo
  criterio que `US-ADJ-41`.
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (todas)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters →
  frameworks), BC Identidad
- **Umbrales de calidad** (de `pyproject.toml`, no de los defaults de `config.json`):
  - pylint ≥ 8.0 (`[tool.codeguard]` `min_pylint_score`)
  - CC ≤ 10 (`max_cyclomatic_complexity`)
  - MI: sin umbral explícito en `pyproject.toml` — referencia histórica del proyecto ≥ 40-60
    según US previas de Identidad
  - CBO ≤ 10 (`[tool.designreviewer]` `max_cbo`, gate de pre-push — bloqueante)
  - cobertura: sin `fail_under` global (`fail_under = 0`), pero el criterio de cierre de US en
    este proyecto apunta a 100% en el código nuevo del BC (ver US-2.1.x a US-ADJ-41)

## Rutas de Artefactos
- Contexto: docs/plans/inc5-adj/US-ADJ-42-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-42-autoregistro-estudiante.feature
- Plan: docs/plans/inc5-adj/US-ADJ-42-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-42-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-42-quality.json

## Notas específicas de esta US
- Reutiliza el evento `UsuarioAutoregistrado` de `US-ADJ-41` (mismo shape, sin dato adicional
  — `comision_id` no forma parte de su payload).
- Reutiliza puertos ya existentes: `UsuarioRepositoryPort`, `PasswordHasherPort`,
  `ComisionRepositoryPort` — sin puertos nuevos.
- **No** reutiliza `AutoregistrarDocenteUseCase` — dos comandos separados, criterio ya
  documentado en `BC-identidad-modelo.md` §13.2 (cada perfil tiene su propia precondición de
  datos).
- Endpoint nuevo en el mismo router de `US-ADJ-41`
  (`src/identidad/frameworks/api/autoregistro_router.py`):
  `POST /identidad/autoregistro/estudiante`, público, responde `201 Created`.
- Composition root: ampliar `src/identidad/frameworks/dependencies.py` para cablear el nuevo
  use case (mismo patrón que `AutoregistrarDocenteUseCase`).
- Issue: [#348](https://github.com/vvalotto/cognion/issues/348)
