# Contexto de Ejecución — US-1.1.2

## Fuentes
- **Fuente HU:** `docs/specs/inc1/US-1.1.2.md` (Issue GitHub #7)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-1.1.2
- **Título:** Estudiante se registra con un link de invitación válido
- **Tipo:** Nueva funcionalidad
- **Puntos:** 5
- **Prioridad:** Alta — cierra el flujo de punta a punta de RF-01 (invitación → registro → asignación a comisión)

## Decisión de alcance — dependencia de JWT (US-1.1.4/US-1.1.5)

Igual que en `US-1.1.1`: el endpoint `POST /identidad/registro` es público, sin guard de JWT
— coincide con la spec ("endpoint FastAPI público, sin JWT — se autentica después") y con el
criterio de negocio: el Estudiante todavía no tiene sesión al momento de registrarse. El guard
de JWT para otros recursos se agrega en `US-1.1.5`, sin tocar este use case.

## Decisión de alcance — frontend

Al revisar `frontend/src` se encontró que es todavía el scaffold default de Vite: sin
React Router, sin cliente HTTP, sin ninguna página propia. Implementar `Registro.tsx` /
`RegistroExito.tsx` "completos" requeriría decidir routing y cliente API ahora, una decisión
de infraestructura no planificada dentro de esta HU.

**Decisión (confirmada por Víctor):** esta US se cierra con backend completo. El frontend de
registro (`Registro.tsx`, `RegistroExito.tsx`, sobre los wireframes ya aprobados en
`docs/design/ux/wireframes-identidad.md` §2.3, §2.5) se implementa en una US-IEDD separada,
una vez decidida la infraestructura base de frontend (router, cliente API). Se registra como
ítem abierto en `CLAUDE.md`.

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación Gherkin ya definidos en la spec
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
- Contexto: docs/plans/inc1/US-1.1.2-context.md
- BDD feature: tests/features/inc1/US-1.1.2-registro-estudiante.feature
- Plan: docs/plans/inc1/US-1.1.2-plan.md
- Reporte: docs/reports/inc1/US-1.1.2-report.md
- Quality report: quality/reports/inc1/US-1.1.2-quality.json
