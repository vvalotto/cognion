# Plan de Implementación — US-8.1.5

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | Excepción `AdministradorYaExiste` | `src/identidad/entities/errors.py` |
| 2 | `BootstrapAdministradorUseCase` (no-op si hay Administrador operativo; delega en `CrearUsuarioUseCase`) | `src/identidad/use_cases/bootstrap_administrador.py` |
| 3 | CLI: `ejecutar(env, pedir_password, repo, hasher) -> int` (orquestación testable) + `main()` | `src/identidad/frameworks/cli/bootstrap_administrador.py` |
| 4 | `scripts/seed_admin.py` pasa a envoltorio del CLI | `scripts/seed_admin.py` |
| 5 | Tests unitarios (use case + 6 escenarios del CLI con fakes) | `tests/unit/inc8/test_us_8_1_5_*.py` |
| 6 | Sección 4 de `verificar_migraciones.sh`: bootstrap real contra la base descartable | `tests/uat/inc8/verificar_migraciones.sh` |
| 7 | Nota en `ADR-016` (módulo en `src/`, `getpass`, no-op con Administrador operativo) | `docs/adr/ADR-016-*.md` |

Sin frontend. Base de desarrollo intacta (se usa la base descartable del script).
