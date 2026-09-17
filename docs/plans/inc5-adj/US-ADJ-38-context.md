# Contexto de Ejecución — US-ADJ-38

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-38.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` §"Arquitectura interna" (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-ADJ-38
- **Título:** Solicitar recuperación de contraseña (endpoint público)
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — primera de la Iteración 2 del Incremento 5-ADJ, `US-ADJ-39` depende de esta

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación en Gherkin ya redactados en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc5-adj/US-ADJ-38-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-38-solicitar-recuperacion-password.feature
- Plan: docs/plans/inc5-adj/US-ADJ-38-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-38-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-38-quality.json

## Notas específicas de esta US
- BC: `identidad`, con dependencia nueva hacia `notificaciones` (primer puerto Identidad → Notificaciones, `ADR-006`).
- Aggregate nuevo: `TokenRecuperacionPassword`. Puertos nuevos: `TokenRecuperacionPasswordRepositoryPort`, `CanalRecuperacionPort`.
- Reutiliza patrón ya existente: `src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` (adapter in-process hacia otro BC) y `src/notificaciones/entities/ports/canal_envio_port.py`/`SmtpCanalEnvio`.
- Issue: [#339](https://github.com/vvalotto/cognion/issues/339)
