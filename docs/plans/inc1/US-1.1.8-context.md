# Contexto de Ejecución — US-1.1.8

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc1/US-1.1.8.md`
- **Fuente Arquitectura:** `CLAUDE.md` (stack: React 19 + TypeScript + Vite + Tailwind CSS +
  shadcn/ui); infraestructura de routing/cliente API/sesión ya establecida por `US-1.1.6`.

## Historia de Usuario
- **ID:** US-1.1.8
- **Título:** Estudiante se registra desde la UI con un link de invitación
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — segunda US bloqueada por `US-1.1.6`, después de `US-1.1.7` (login,
  cerrada). Flujo con más estados (registro: 3 pantallas) — spec, `docs/plans/inc1/inc1-candidatas.md`.

## Adaptación de las fases del skill a stack frontend (TypeScript/React)
Mismo criterio que `US-1.1.6`/`US-1.1.7` (`docs/plans/inc1/US-1.1.7-context.md`) — el skill
asume Python (pylint, radon, pytest, pytest-bdd) en fases 4-7; no aplica a este stack.

| Fase del skill | Equivalente aplicado aquí (frontend) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (documental) — implementado como tests Vitest, no step_defs |
| Fase 4/5 — Tests | Vitest + React Testing Library — componentes `Registro.tsx`/`RegistroError.tsx`/`RegistroExito.tsx` y flujo de envío del formulario |
| Fase 6 — Validación BDD | Verificar que los tests Vitest cubren cada escenario del `.feature` |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest — cobertura de referencia ≥80% sobre `Registro.tsx`/`RegistroError.tsx`/`RegistroExito.tsx` |

## Decisión de componentes UI (a confirmar en Fase 2)
Ya están instalados `Button`, `Input`, `Label` (shadcn/ui, desde `US-1.1.7`). El formulario de
registro (nombre, email, contraseña) reutiliza estos componentes — no se anticipan componentes
nuevos, a confirmar en Fase 2 contra el wireframe (`§2.3`, `§2.4`, `§2.5`).

## Decisiones de Ejecución
- **BDD:** Sí — 5 escenarios Gherkin ya definidos en la spec (registro exitoso, token vencido,
  token ya usado, token inexistente, email ya registrado).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4-7 adaptadas a stack frontend, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion) — perfil backend; sin perfil frontend dedicado,
  misma adaptación documentada que en `US-1.1.6`/`US-1.1.7`.
- **Patrón arquitectónico:** React 19 + TypeScript + Vite, sin capas Clean Architecture (no
  aplica al frontend).
- **Umbrales de calidad (adaptados):**
  - ESLint/oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - Vitest: todos los tests pasan, cobertura de referencia ≥80% en `Registro.tsx`/`RegistroError.tsx`/`RegistroExito.tsx`

## Rutas de Artefactos
- Contexto: `docs/plans/inc1/US-1.1.8-context.md`
- BDD feature: `tests/features/inc1/US-1.1.8-registro-ui.feature`
- Plan: `docs/plans/inc1/US-1.1.8-plan.md`
- Reporte: `docs/reports/inc1/US-1.1.8-report.md`
- Quality report: `quality/reports/inc1/US-1.1.8-quality.json`
