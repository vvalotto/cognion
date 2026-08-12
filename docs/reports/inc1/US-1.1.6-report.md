# Reporte de Implementación: US-1.1.6

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.6 - Infraestructura de frontend — routing, cliente API y
  manejo de sesión
- **Puntos estimados:** 3
- **Tiempo real:** ~37 min (fases 0-8, tracking de ejecución del agente, no comparable
  contra esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-07-24

Primera US de la Iteración 2 (frontend de Identidad) y la que bloqueaba a las otras tres
(`US-1.1.7`, `US-1.1.8`, `US-1.1.9`). `frontend/src` era el scaffold default de Vite, sin
routing ni cliente HTTP — esta US agrega React Router (modo data), un cliente API que adjunta
el JWT y maneja 401/403 de forma centralizada, y los dos layouts (auth/app) que consumirán las
pantallas siguientes. También resuelve un gap detectado en Fase 0: el proyecto no tenía
ninguna estrategia de testing de frontend — se agregó Vitest + React Testing Library, decisión
tomada con Víctor antes de continuar.

---

## Componentes Implementados

### Testing infra
- ✅ `vite.config.ts` (editado) — `defineConfig` de `vitest/config`, bloque `test` con
  `environment: jsdom`, `setupFiles`, `coverage` (umbral de referencia 80%)
- ✅ `src/test/setup.ts` (nuevo) — `@testing-library/jest-dom/vitest`
- ✅ `package.json` (editado) — `react-router`, `vitest`, `@testing-library/react`,
  `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`,
  `@vitest/coverage-v8`; scripts `test`/`test:watch`

### Sesión y cliente API (`src/lib/`)
- ✅ `session.ts` (nuevo) — `getSession`/`setSession`/`clearSession` sobre `localStorage`
- ✅ `api-client.ts` (nuevo) — `apiFetch<T>()`, `ApiError`; adjunta JWT, 401 limpia sesión y
  navega a `/login`, 403 propaga el mensaje genérico del backend

### Routing y layouts
- ✅ `router.tsx` (nuevo) — `createBrowserRouter`, exporta `router` (permite navegación
  imperativa desde `api-client.ts`), rutas placeholder `/login`/`/registro`
- ✅ `pages/_placeholders.tsx` (nuevo) — `LoginPlaceholder`/`RegistroPlaceholder`, movidos a
  archivo propio para evitar el warning de fast-refresh de oxlint
- ✅ `layouts/AuthLayout.tsx` (nuevo) — tarjeta centrada, ancho máx. 420px
- ✅ `layouts/AppLayout.tsx` (nuevo) — header con marca + rol del usuario autenticado
- ✅ `App.tsx` (editado) — reemplaza el demo de Vite por `<RouterProvider router={router} />`
- ✅ `.env.example` (nuevo) — `VITE_API_BASE_URL`

### CI
- ✅ `.github/workflows/ci.yml` (editado) — agrega `tsc --noEmit` y `npm run test` al job
  `lint-frontend` (mismo nombre — `develop` tiene branch protection que exige ese required
  status check exacto)

### Limpieza de código obsoleto (confirmada con Víctor)
- 🗑️ `src/App.css`, `src/assets/{react.svg,vite.svg,hero.png}`, `public/icons.svg` — sin
  referencias tras reemplazar `App.tsx`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| ESLint/oxlint | 0 errores, 0 warnings nuevas | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest — cobertura statements/lines/funcs | 100% | ≥ 80% | ✅ |
| Vitest — cobertura branches | 87.5% | ≥ 80% | ✅ |
| Backend — mypy `src/` completo | 0 errores (79 archivos) | — | ✅ (sin regresión) |

Fuente: `quality/reports/inc1/US-1.1.6-quality.json`. Umbrales de frontend adoptados en esta
US (Fase 0) — el proyecto no tenía perfil de quality gates para frontend en `config.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (10 tests) — `frontend/src/lib/`
- `session.test.ts` (4 tests) — set/get/clear, contenido corrupto en `localStorage`
- `api-client.test.ts` (6 tests) — adjunta JWT, sin JWT sin sesión, 401 limpia+navega, 403
  propaga mensaje genérico, respuesta 200 parseada, respuesta 204 sin body, error sin body
  JSON usa mensaje genérico

### Tests de Integración (6 tests)
- `router.test.tsx` (2 tests) — `/login` y `/registro` renderizan dentro del layout de auth
- `layouts/AppLayout.test.tsx` (3 tests) — muestra rol con sesión, oculta info sin sesión,
  renderiza contenido anidado vía `Outlet`

### Escenarios BDD (3 escenarios) — `tests/features/inc1/US-1.1.6-infraestructura-frontend.feature`
- JWT adjuntado en request a endpoint protegido
- 401 limpia sesión y redirige a login
- 403 muestra mensaje genérico sin filtrar el recurso

Sin runner Gherkin dedicado para TypeScript en este proyecto — los 3 escenarios están
cubiertos 1:1 por tests de `api-client.test.ts` (ver Fase 6).

**Todos los tests pasando:** ✅ 16/16 (suite frontend completa)

---

## Archivos Creados/Modificados

**Producción:** `frontend/src/lib/{session,api-client}.ts`, `frontend/src/router.tsx`,
`frontend/src/pages/_placeholders.tsx`, `frontend/src/layouts/{AuthLayout,AppLayout}.tsx`
(nuevos); `frontend/src/App.tsx`, `frontend/vite.config.ts`, `frontend/package.json`,
`.github/workflows/ci.yml` (editados); `frontend/.env.example` (nuevo) — ~230 líneas.

**Tests:** `frontend/src/lib/{session,api-client}.test.ts`, `frontend/src/router.test.tsx`,
`frontend/src/layouts/AppLayout.test.tsx`, `frontend/src/test/setup.ts` (nuevos);
`tests/features/inc1/US-1.1.6-infraestructura-frontend.feature` (nuevo) — ~220 líneas.

**Documentación:** `docs/plans/inc1/US-1.1.6-{context,plan}.md`,
`docs/reports/inc1/US-1.1.6-report.md` (este archivo),
`quality/reports/inc1/US-1.1.6-quality.json`, `docs/traceability/matrix.md`,
`docs/plans/inc1/inc1-candidatas.md`, `CHANGELOG.md` (editados).

**Eliminados:** `frontend/src/App.css`, `frontend/src/assets/{react.svg,vite.svg,hero.png}`,
`frontend/public/icons.svg`.

---

## Criterios de Aceptación

- [x] React Router configurado con rutas placeholder de login y registro
- [x] Cliente API con base URL configurable, manejo de JSON y de errores HTTP
- [x] El cliente adjunta el JWT guardado en cada request a un endpoint protegido
- [x] 401 → limpia la sesión y redirige a login; 403 → feedback genérico sin filtrar recurso
- [x] Layout de auth distinto del layout de aplicación
- [x] Sin pantallas de negocio propias (soporte técnico para US-1.1.7/1.1.8/1.1.9)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-1.1.7` (Issue #24) — login desde la UI, primera pantalla real que reemplaza el
  placeholder de `/login`
- [ ] `US-1.1.8` (Issue #25) — registro desde la UI (3 pantallas)
- [ ] `US-1.1.9` (Issue #26) — alta de docente desde la UI (ruta protegida, admin-only)
- [ ] Considerar formalizar un perfil de quality gates de frontend en
  `.claude/skills/implement-us/config.json` si el patrón Vitest se repite en próximos
  incrementos con frontend (hoy los umbrales de esta US son una convención ad hoc, no un
  perfil declarado)

---

## Lecciones Aprendidas

- ⚠️ Detectar un gap de tooling (sin testing de frontend) en Fase 0 y resolverlo con Víctor
  antes de seguir evitó construir sobre un supuesto no confirmado — el skill `/implement-us`
  asume Python/pytest en sus fases 4-7, y este proyecto necesitaba una adaptación explícita
  para TypeScript/React, documentada en `docs/plans/inc1/US-1.1.6-context.md`.
- 💡 Exportar la instancia del router (no solo el componente `RouterProvider`) permite
  navegación imperativa desde `api-client.ts` ante un 401, sin necesitar un hook de React
  fuera del árbol de componentes.
- ⚠️ Un error de `cd` en Fase 3 creó un `src/test/` duplicado en la raíz del repo — corregido
  al revisar `git status` en Fase 8. Verificar la ruta de trabajo antes de comandos con rutas
  relativas evita este tipo de duplicado silencioso.
- ✅ Mantener el nombre del job de CI (`Lint frontend`) al agregar pasos nuevos, en vez de
  renombrarlo, evitó romper el required status check de branch protection de `develop`.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-24
