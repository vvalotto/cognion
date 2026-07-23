# Contexto de Ejecución — US-1.1.4

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc1/US-1.1.4.md`
- **Fuente Arquitectura:** Documento local — `docs/rf/ARQ_v1.md`, ADR-007 (JWT+RBAC), ADR-013 (expiración 60 min), `CLAUDE.md`

## Historia de Usuario
- **ID:** US-1.1.4
- **Título:** Docente, administrador y estudiante se autentican y reciben un JWT con su rol
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — habilita autorización por rol (US-1.1.5) y es punto de entrada común a los tres perfiles

## Alcance acordado con el usuario
- **Solo backend.** El frontend (`Login.tsx`, `LoginError.tsx`, `frontend/src/lib/auth.ts`)
  queda diferido a una US-IEDD separada, igual que se decidió para US-1.1.2 — `frontend/`
  todavía no tiene routing ni cliente API montados.
- Artefactos de backend a modificar (de la spec):
  - `src/identidad/entities/rol.py` — VO `Rol`
  - `src/identidad/entities/jwt.py` — VO `JWT`
  - `src/identidad/entities/ports/jwt_issuer_port.py` — puerto de emisión/verificación
  - `src/identidad/use_cases/iniciar_sesion.py` — orquesta verificación + emisión
  - `src/identidad/interface_adapters/controllers/auth_controller.py`
  - `src/identidad/frameworks/security/jwt_pyjwt.py` — adaptador PyJWT (ADR-007)
  - `src/identidad/frameworks/api/auth_router.py` — `POST /identidad/login`

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la spec (login exitoso por rol, rechazo por credenciales inválidas).
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
- Contexto: `docs/plans/inc1/US-1.1.4-context.md`
- BDD feature: `tests/features/inc1/US-1.1.4-autenticacion-jwt.feature`
- Plan: `docs/plans/inc1/US-1.1.4-plan.md`
- Reporte: `docs/reports/inc1/US-1.1.4-report.md`
- Quality report: `quality/reports/inc1/US-1.1.4-quality.json`
