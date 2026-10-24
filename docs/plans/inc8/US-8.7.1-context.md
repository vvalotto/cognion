# Contexto de Ejecución — US-8.7.1

## Fuentes
- **Fuente HU:** `docs/specs/inc8/US-8.7.1.md`, Issue [#564](https://github.com/vvalotto/cognion/issues/564)
- **Arquitectura:** `docs/architecture/`, `CLAUDE.md` (Clean Architecture por BC), `src/identidad/frameworks/cli/bootstrap_administrador.py` (precedente de comando operativo)
- **Datos de entrada reales (fuera de git):** `tests/uat/datos-reales/*- Cuestionario.md` (17 archivos × 20 preguntas, formato regular verificado)

## Historia de Usuario
- **ID:** US-8.7.1 — Carga de datos iniciales (materias y preguntas) desde archivos JSON o Markdown
- **Tipo:** comando operativo en `src/banco_preguntas/frameworks/cli/` (código de producción sobre el BC Banco de Preguntas)
- **Puntos:** 5
- **Patrón activo:** `clean-architecture-bc`

## Decisiones de Ejecución
- **Casos de uso reutilizados sin cambios:** `CrearMateriaUseCase`, `CargarPreguntaOpcionMultipleUseCase`, `CargarPreguntaVerdaderoFalsoUseCase`, `FiltrarBancoUseCase`. Con `docente_id=None` omiten la autorización por Comisión (`US-ADJ-57`), que es lo que necesita un comando operativo sin usuario.
- **Idempotencia:** se leen los textos de las preguntas activas del banco con `PreguntaRepositoryPort.filtrar` (sin paginar) y se omiten las repetidas; sin puerto nuevo.
- **Capas:** el parseo y la validación de archivos (JSON/Markdown) son lógica de adaptación → `interface_adapters/`; el comando y el armado de dependencias → `frameworks/cli/`. El dominio no cambia.
- **Todo o nada por archivo:** se valida el archivo completo (formato y construcción de las entidades, que aplica INV-BP-02/03) antes de persistir nada. Los repositorios existentes hacen `commit` por llamada, así que la persistencia no es una única transacción; si la base falla a mitad de un archivo, volver a ejecutar es seguro porque el comando es idempotente (omite lo ya cargado).
- **BDD:** sí (la spec define 11 escenarios). Fases 1 a 9 completas.

## Rutas
- Plan: docs/plans/inc8/US-8.7.1-plan.md · Reporte: docs/reports/inc8/US-8.7.1-report.md · Quality: quality/reports/inc8/US-8.7.1-quality.json
- Feature: tests/features/inc8/US-8.7.1-carga-datos-iniciales.feature
- Branch: `feature/US-8.7.1-carga-datos-iniciales` (rebaseada sobre `develop` en `5a0cce8`).
