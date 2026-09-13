# Contexto de Ejecución — US-ADJ-39

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-39.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` §"Arquitectura interna" (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-ADJ-39
- **Título:** Confirmar nueva contraseña con token de recuperación (endpoint público)
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — segunda de la Iteración 2 del Incremento 5-ADJ, depende de `US-ADJ-38` (ya cerrada)

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
- Contexto: docs/plans/inc5-adj/US-ADJ-39-context.md
- BDD feature: tests/features/inc5-adj/US-ADJ-39-confirmar-recuperacion-password.feature
- Plan: docs/plans/inc5-adj/US-ADJ-39-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-39-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-39-quality.json

## Notas específicas de esta US
- BC: `identidad`. Reutiliza el aggregate `TokenRecuperacionPassword` y el puerto
  `TokenRecuperacionPasswordRepositoryPort` creados en `US-ADJ-38` — sin puertos nuevos.
- Reutiliza `Usuario.validar_password_nueva()` (INV-ID-11 ampliada, `US-ADJ-36`) y el mismo
  mecanismo de mutación que `resetear_password()` (`US-2.2.4`) para actualizar
  `password_hash` sin tocar `bloqueada` ni los contadores de intentos fallidos.
- Excepciones nuevas: `TokenRecuperacionInvalido`, `TokenRecuperacionYaUsado`,
  `TokenRecuperacionVencido` (INV-ID-13).
- Endpoint nuevo: `POST /identidad/recuperar-password/confirmar` (público, sin auth).
- Sin pantalla propia — `US-ADJ-40` construye el frontend.
- Issue: [#340](https://github.com/vvalotto/cognion/issues/340)
