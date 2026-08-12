# Contexto de Ejecución — US-1.1.5

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc1/US-1.1.5.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md`, ADR-007 (JWT+RBAC), `CLAUDE.md`

## Historia de Usuario
- **ID:** US-1.1.5
- **Título:** El sistema restringe el acceso a funcionalidades según el rol del usuario autenticado
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — cierra RF-02 (con US-1.1.4 ya implementada) y es guard transversal
  reutilizado por todos los BC futuros

## Alcance acordado con el usuario
- **Solo backend.** Sin pantalla propia (ver `## Fuente de verdad UX` de la spec — no aplica).
  El frontend condicional por rol queda fuera de alcance hasta que exista una pantalla
  protegida real (banco de preguntas, analytics — incrementos posteriores).
- Artefactos de backend a modificar (de la spec):
  - `src/identidad/interface_adapters/security/get_current_user.py` — dependency que decodifica
    y valida el JWT, resuelve el `Usuario`/rol actual
  - `src/identidad/interface_adapters/security/require_rol.py` — dependency que verifica `rol`
    contra una lista de roles permitidos
  - `src/identidad/frameworks/api/usuarios_router.py`, `comisiones_router.py` — aplicar
    `require_rol(["administrador"])` a los endpoints de `US-1.1.0`
  - `src/identidad/frameworks/api/invitaciones_router.py` — aplicar `require_rol(["docente"])`
    (`US-1.1.1`)
- No requiere nuevo evento de dominio ni aggregate propio — es un guard (query), no un comando.
  `Rol` (VO) y `JWTIssuerPort` ya existen de `US-1.1.4` y se reutilizan sin redefinir.

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la spec
  (6 escenarios: acceso concedido, rechazo por rol insuficiente ×3, sin JWT, JWT expirado).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion)
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10 (por función, radon)
  - MI ≥ 20 (radon)
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: `docs/plans/inc1/US-1.1.5-context.md`
- BDD feature: `tests/features/inc1/US-1.1.5-autorizacion-rbac.feature`
- Plan: `docs/plans/inc1/US-1.1.5-plan.md`
- Reporte: `docs/reports/inc1/US-1.1.5-report.md`
- Quality report: `quality/reports/inc1/US-1.1.5-quality.json`
