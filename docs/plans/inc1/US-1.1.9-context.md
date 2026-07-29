# Contexto de Ejecución — US-1.1.9

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc1/US-1.1.9.md`
- **Fuente Arquitectura:** `CLAUDE.md` (stack: React 19 + TypeScript + Vite + Tailwind CSS +
  shadcn/ui); infraestructura de routing/cliente API/sesión ya establecida por `US-1.1.6`.

## Historia de Usuario
- **ID:** US-1.1.9
- **Título:** Administrador da de alta un Docente desde la UI
- **Tipo:** Nueva funcionalidad
- **Puntos:** 3
- **Prioridad:** Alta — última US-IEDD pendiente de la Iteración 2, bloqueada por `US-1.1.6`
  (infraestructura) y `US-1.1.7` (login, para que el Administrador llegue a la pantalla
  protegida). Cierra la Iteración 2 y habilita la apertura de BL-002
  (`docs/plans/inc1/inc1-candidatas.md`).

## Adaptación de las fases del skill a stack frontend (TypeScript/React)
Mismo criterio que `US-1.1.6`/`US-1.1.7`/`US-1.1.8` (`docs/plans/inc1/US-1.1.8-context.md`) —
el skill asume Python (pylint, radon, pytest, pytest-bdd) en fases 4-7; no aplica a este stack.

| Fase del skill | Equivalente aplicado aquí (frontend) |
|---|---|
| Fase 1 — BDD | `.feature` Gherkin (documental) — implementado como tests Vitest, no step_defs |
| Fase 4/5 — Tests | Vitest + React Testing Library — componentes `AltaDocente.tsx`/`AltaDocenteExito.tsx` y flujo de envío del formulario, más la protección de ruta por rol |
| Fase 6 — Validación BDD | Verificar que los tests Vitest cubren cada escenario del `.feature` |
| Fase 7 — Quality Gates | `npm run lint` (0 errores), `tsc --noEmit` (0 errores), Vitest — cobertura de referencia ≥80% sobre `AltaDocente.tsx`/`AltaDocenteExito.tsx` |

## Decisión de componentes UI (a confirmar en Fase 2)
Ya están instalados `Button`, `Input`, `Label` (shadcn/ui, desde `US-1.1.7`). El formulario de
alta de Docente (nombre, email, contraseña) reutiliza estos componentes — perfil fijo en
"Docente", sin selector de perfil (decisión explícita de Víctor, wireframe §4). No se anticipan
componentes nuevos, a confirmar en Fase 2 contra el wireframe (`§2.6`, `§2.7`).

## Decisiones de Ejecución
- **BDD:** Sí — 4 escenarios Gherkin ya definidos en la spec (alta exitosa, email duplicado,
  acceso sin sesión, acceso con rol insuficiente).
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 (4-7 adaptadas a stack frontend, ver tabla)

## Perfil Activo
- **Perfil:** clean-architecture-bc (Cognion) — perfil backend; sin perfil frontend dedicado,
  misma adaptación documentada que en `US-1.1.6`/`US-1.1.7`/`US-1.1.8`.
- **Patrón arquitectónico:** React 19 + TypeScript + Vite, sin capas Clean Architecture (no
  aplica al frontend). Sin impacto en backend — consume `POST /usuarios` ya existente
  (`US-1.1.0`, protegido por `US-1.1.5`).
- **Umbrales de calidad (adaptados):**
  - ESLint/oxlint: 0 errores
  - `tsc --noEmit`: 0 errores
  - Vitest: todos los tests pasan, cobertura de referencia ≥80% en
    `AltaDocente.tsx`/`AltaDocenteExito.tsx`

## Rutas de Artefactos
- Contexto: `docs/plans/inc1/US-1.1.9-context.md`
- BDD feature: `tests/features/inc1/US-1.1.9-alta-docente-ui.feature`
- Plan: `docs/plans/inc1/US-1.1.9-plan.md`
- Reporte: `docs/reports/inc1/US-1.1.9-report.md`
- Quality report: `quality/reports/inc1/US-1.1.9-quality.json`
