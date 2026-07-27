# Contexto de Ejecución — US-1.1.7

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc1/US-1.1.7.md`
- **Fuente Arquitectura:** `CLAUDE.md` (stack: React 19 + TypeScript + Vite + Tailwind CSS +
  shadcn/ui); infraestructura de routing/cliente API/sesión ya establecida por `US-1.1.6`.

## Historia de Usuario
- **ID:** US-1.1.7
- **Título:** Docente/Administrador/Estudiante inicia sesión desde la UI
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — primera de las tres US bloqueadas por `US-1.1.6`; valida la
  infraestructura con el flujo más simple del wireframe (spec, `docs/plans/inc1/inc1-candidatas.md`)

## Adaptación de las fases del skill a stack frontend (TypeScript/React)
Mismo criterio que `US-1.1.6` (`docs/plans/inc1/US-1.1.6-context.md`) — el skill asume Python
(pylint, radon, pytest, pytest-bdd) en fases 4-7; no aplica a este stack.

| Fase del skill | Equivalente aplicado aquí (frontend) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (documental) — implementado como tests Vitest, no step_defs |
| Fase 4/5 — Tests | Vitest + React Testing Library — componentes `Login.tsx`/`LoginError.tsx` y flujo de envío del formulario |
| Fase 6 — Validación BDD | Verificar que los tests Vitest cubren cada escenario del `.feature` |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest — cobertura de referencia ≥80% sobre `Login.tsx`/`LoginError.tsx` |

## Decisión de componentes UI (a confirmar en Fase 2)
El proyecto solo tiene `Button` instalado de shadcn/ui (`components.json`, preset `base-nova`).
Esta US necesita `Input` y `Label` para los campos de email/contraseña. Hay red disponible
(`npm view shadcn` responde) — se instalan con `npx shadcn add input label`, igual que se hizo
con `Button` (`cef8abb`), en vez de escribirlos a mano.

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios Gherkin ya definidos en la spec (login exitoso, credenciales
  inválidas, email inexistente).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4-7 adaptadas a stack frontend, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion) — perfil backend; sin perfil frontend dedicado,
  misma adaptación documentada que en `US-1.1.6`.
- **Patrón arquitectónico:** React 19 + TypeScript + Vite, sin capas Clean Architecture (no
  aplica al frontend).
- **Umbrales de calidad (adaptados):**
  - ESLint/oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - Vitest: todos los tests pasan, cobertura de referencia ≥80% en `Login.tsx`/`LoginError.tsx`

## Rutas de Artefactos
- Contexto: `docs/plans/inc1/US-1.1.7-context.md`
- BDD feature: `tests/features/inc1/US-1.1.7-login-ui.feature`
- Plan: `docs/plans/inc1/US-1.1.7-plan.md`
- Reporte: `docs/reports/inc1/US-1.1.7-report.md`
- Quality report: `quality/reports/inc1/US-1.1.7-quality.json`
