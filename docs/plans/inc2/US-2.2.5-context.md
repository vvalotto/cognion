# Contexto de Ejecución — US-2.2.5

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.5.md`
- **Fuente Arquitectura:** `CLAUDE.md` (reglas de capas Clean Architecture BC-first) +
  `docs/rf/ARQ_v1.md` (ADRs 001–006, 012–014, 019) — mismas fuentes usadas en `US-2.2.1` a
  `US-2.2.4`, ya establecidas en el proyecto.

## Historia de Usuario
- **ID:** US-2.2.5
- **Título:** Usuario autenticado cambia su propia contraseña
- **Tipo:** Nueva funcionalidad
- **Puntos:** 2
- **Prioridad:** Alta — última US backend de la Iteración 2 (RF-19), bloquea el inicio del
  frontend (`US-2.2.8`)

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación en Gherkin ya redactados en la
  spec (5 escenarios)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10 por función
  - MI ≥ 20
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: `docs/plans/inc2/US-2.2.5-context.md`
- BDD feature: `tests/features/inc2/US-2.2.5-cambiar-password.feature`
- Plan: `docs/plans/inc2/US-2.2.5-plan.md`
- Reporte: `docs/reports/inc2/US-2.2.5-report.md`
- Quality report: `quality/reports/inc2/US-2.2.5-quality.json`

## Notas de continuidad
- Reutiliza `Usuario.validar_password_nueva()` (INV-ID-11) de `US-2.2.4`.
- Comparte el mecanismo de bloqueo (`bloqueada`) de `US-2.2.1`, con contador propio e
  independiente `intentos_fallidos_password` (ya existe en `Usuario` desde `US-2.2.1`, sin
  usar todavía).
- `UsuarioRepositoryPort.actualizar()` (de `US-2.2.1`) es el método de persistencia a reutilizar.
- Precedente recurrente de CBO CRITICAL en pre-push (`US-2.1.2`/`.5`/`.6`/`2.2.2`): vigilar el
  controller elegido para el endpoint nuevo (`PUT /usuarios/me/password`) — decidir en Fase 2
  si conviene sumarlo a `CuentasController` (ya en 3 métodos tras `US-2.2.4`, sin CRITICAL) o
  a un controller propio de autenticación/self-service.
