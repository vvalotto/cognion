# Changelog

Todos los cambios notables de Cognion se documentan en este archivo.

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.0.0/)
Versionado: [Semantic Versioning](https://semver.org/lang/es/)

---

## [Unreleased]

### Added
- [US-1.1.0] Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes
  — BC Identidad, precondición del resto de la Iteración 1
  - `Usuario` (aggregate) + entities subordinadas `Docente`/`Administrador`/`Estudiante`,
    `Comisión` (aggregate), eventos `UsuarioCreado`/`ComisionCreada`/`DocenteAsignado`
  - `CrearUsuarioUseCase`, `CrearComisionUseCase`, `AsignarDocenteAComisionUseCase`
  - Endpoints `POST /usuarios`, `POST /comisiones`, `POST /comisiones/{id}/docentes` (sin
    guard de rol todavía — se agrega en `US-1.1.5`)
  - `scripts/seed_admin.py` — bootstrap del primer Administrador (`ADR-016`)
  - Migración Alembic: tablas `usuario`, `docente`, `administrador`, `estudiante`, `comision`,
    `comision_docentes`
  - 37 tests (20 unitarios + 9 integración + 5 BDD via `step_defs`), coverage 100% en
    entities/use_cases/interface_adapters
  - `ADR-016` (bootstrap admin), `ADR-017` (DB session compartida `shared/frameworks/db.py`),
    `ADR-018` (`NullPool` en el engine SQLAlchemy)

### Fixed
- `passlib` incompatible con `bcrypt>=4.1` — reemplazado por `bcrypt` directo
- Orden de inserción `Usuario`/perfil sin `relationship()` ORM causaba violación de FK —
  corregido con flush intermedio en `SQLAlchemyUsuarioRepository`
- `pytest-asyncio` sin `loop_scope` explícito rompía el engine compartido entre tests con
  distintos event loops — fijado a `session` scope

## [0.2.0] - 2026-07-16

### Added
- PostgreSQL local (vía Homebrew) y Alembic inicializado (`alembic.ini`, `migrations/`)
- `src/settings.py` — configuración desde `.env` con pydantic-settings
- Primer test real del proyecto (`tests/unit/inc0/test_health.py`)
- `.claude/commands/docs-audit.md` — skill de auditoría de trazabilidad documental
- HITO-2 y HITO-3 (`docs/aprendizajes/`)
- BL-001 — cierre del Incremento 0 (`.cm/baselines/BL-001-fundacion-tecnica.md`)

### Changed
- CI ya no tolera "0 tests" — retirado tras agregar el primer test real
- `docs/rf/PLAN_v1.md`: Docker local diferido a un incremento posterior; PostgreSQL local
  corre vía Homebrew mientras tanto
- `CLAUDE.md`: corregido el "próximo paso" — el Incremento 0 no usa `incN-candidatas.md`

## [0.1.0] - 2026-07-15

### Added
- Fundación documental: RF_v1, RNF_v1, ARQ_v1, PLAN_v1
- Plan de Gestión de Configuración (`docs/plans/PLAN-CM.md`), checklist de instalación y
  workflow de desarrollo
- ADRs 001-011 ratificados y matriz de trazabilidad inicial
- Primer HITO de aprendizaje (`docs/aprendizajes/HITO-1-*.md`)
- BL-000 — cierre de la fundación documental (`.cm/baselines/BL-000-fundacion-documental.md`)

### Changed
- Plan de incrementos (`PLAN_v1.md`) reestructurado: Incremento 0 pasa a ser fundación técnica
  pura, BC Identidad se mueve a un nuevo Incremento 1, resto renumerado (2-7)
- `docs/cm/` renombrado a `docs/plans/`
