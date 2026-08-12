# Plan de Implementación: US-1.1.6 - Infraestructura de frontend

**Patrón:** React 19 + TypeScript + Vite (sin capas Clean Architecture — no aplica a `frontend/`)
**Producto:** frontend
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-24

## Componentes a Implementar

### 1. Testing infra (decisión tomada con Víctor en Fase 0)
- [x] `frontend/package.json`
  - Agregar deps: `react-router`
  - Agregar devDeps: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`,
    `@testing-library/user-event`, `jsdom`
  - Scripts: `"test": "vitest run"`, `"test:watch": "vitest"`
- [x] `frontend/vite.config.ts`
  - Usar `defineConfig` de `vitest/config` (en vez de `vite`) y agregar bloque `test`
    (`environment: "jsdom"`, `setupFiles: ["./src/test/setup.ts"]`, `coverage` con umbral de
    referencia 80%)
- [x] `frontend/src/test/setup.ts`
  - `import '@testing-library/jest-dom'`

### 2. Sesión y cliente API (`frontend/src/lib/`)
- [x] `frontend/src/lib/session.ts`
  - `getSession()` / `setSession({token, rol})` / `clearSession()` sobre `localStorage`
  - Sin decisión arquitectónica nueva: `localStorage` es la opción simple y suficiente para
    un JWT sin refresh/blacklist (`ADR-013`) — documentar el trade-off (XSS) en el reporte
- [x] `frontend/src/lib/api-client.ts`
  - `ApiError` (status, message)
  - `apiFetch<T>(path, init)` — arma la URL desde `import.meta.env.VITE_API_BASE_URL`, adjunta
    `Authorization: Bearer <token>` si hay sesión, parsea JSON
  - 401 → `clearSession()` + `router.navigate("/login")` + lanza `ApiError`
  - 403 → lanza `ApiError` con el mensaje genérico que ya devuelve el backend (`US-1.1.5`),
    sin agregar detalle del recurso

### 3. Routing y layouts (`frontend/src/`)
- [x] `frontend/src/router.tsx`
  - `createBrowserRouter` (React Router v7, modo data) — exporta `router` para que
    `api-client.ts` pueda navegar imperativamente en el 401
  - Rutas placeholder: `/login`, `/registro` (contenido real en US-1.1.7/1.1.8)
- [x] `frontend/src/layouts/AuthLayout.tsx`
  - Tarjeta centrada, ancho máx. 420px (`wireframes-identidad.md` §3)
- [x] `frontend/src/layouts/AppLayout.tsx`
  - Header de aplicación: marca + usuario autenticado (lee de `session.ts`)
- [x] `frontend/src/App.tsx`
  - Reemplaza el contenido demo de Vite por `<RouterProvider router={router} />`
- [x] `frontend/.env.example`
  - `VITE_API_BASE_URL=http://localhost:8000`

### 4. Integración — CI
- [x] `.github/workflows/ci.yml`
  - Agregar pasos `tsc --noEmit` y `npm run test` al job `lint-frontend` — mantiene el nombre
    del job (`develop` tiene branch protection que exige `Lint frontend` como required status
    check exacto; renombrarlo rompería el check sin tocar también la protección del branch)

**Estado:** 11/11 tareas completadas (agrupadas en 7 tareas de tracking)

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| Validación de Contexto | 99s |
| Escenarios BDD | 159s |
| Plan de Implementación | 105s |
| Implementación | 1281s |
| Tests Unitarios | 166s |
| Tests de Integración | 67s |
| Validación BDD | 15s |
| Quality Gates | 185s |
| **Total** | **~37 min** |

> Nota (PRIN-001, `.claude/skills/implement-us/skill.md`): estos tiempos son ejecución real del
> agente, no comparables contra estimaciones de esfuerzo humano.

## Lecciones Aprendidas

- ⚠️ El proyecto no tenía ninguna estrategia de testing de frontend definida antes de esta US
  — Fase 0 detectó el gap (sin Vitest/Jest/Playwright, CI solo con ESLint) y se resolvió con
  Víctor antes de seguir, en vez de asumir un criterio. Quedó como convención de este PR (no
  hay perfil `config.json` para frontend todavía) — considerar formalizarlo si el patrón se
  repite en próximos incrementos con frontend.
- 💡 Exportar la instancia del router (`createBrowserRouter`) en vez de solo el componente
  `<RouterProvider>` permite que `api-client.ts` navegue imperativamente ante un 401 sin
  necesitar un hook de React fuera del árbol de componentes — patrón reutilizable para
  cualquier lógica de infraestructura que necesite reaccionar a la sesión.
- ⚠️ Un error de `cd` durante la Fase 3 creó un `src/test/` duplicado en la raíz del repo (en
  vez de `frontend/src/test/`) — detectado recién en Fase 8 al revisar `git status`. Verificar
  la ruta de trabajo antes de comandos con rutas relativas (`mkdir -p`, heredocs) evita este
  tipo de duplicado silencioso.
