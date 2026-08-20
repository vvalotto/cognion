# Plan de Implementación: US-2.2.6 - Administrador ve y filtra el listado de cuentas (UI)

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** identidad

## Decisiones de diseño

- **Cliente API nuevo** `cuentas-api.ts`, mismo patrón que `banco-preguntas-api.ts`: reutiliza
  `apiFetch` (JWT/401/403 ya resueltos), mapea snake_case↔camelCase.
- **Filtros con `<select>` nativo** para rol y estado (opciones fijas, no derivadas de datos
  como `unidad`/`tema` en `Banco.tsx`) + `<input>` de texto libre para búsqueda — mismo estilo
  visual que `Banco.tsx` (labels + `border-border`, sin componente shadcn nuevo).
- **Debounce no aplica**: los 3 filtros (rol, estado, búsqueda) se combinan en un único
  `useEffect` que dispara `listarCuentas(filtros)` en cada cambio, igual que `Banco.tsx` — el
  volumen esperado de cuentas (decenas, no cientos) no justifica debounce en esta iteración.
- **Ruta de detalle** `/cuentas/:usuarioId` se agrega en `router.tsx` apuntando a un
  placeholder (`CuentaDetallePlaceholder`, mismo patrón que `InicioPlaceholder` en
  `_placeholders.tsx`) hasta que `US-2.2.7` la reemplace — la fila de la tabla ya debe navegar
  ahí (criterio de aceptación "Navegar al detalle").
- **"+ Nueva cuenta"**: el wireframe (§2.1) aclara que enlaza el flujo ya existente de alta de
  Docente (`US-1.1.9`, ruta `/docentes/nuevo`) — no hay pantalla ni endpoint nuevo, solo un
  link.

## Componentes a Implementar

### 1. Cliente API (`frontend/src/lib/`)

- [x] `cuentas-api.ts` (nuevo)
  - Reutiliza `Rol` de `@/lib/session.ts` (`"administrador" | "docente" | "estudiante"`) —
    sin duplicar el tipo
  - `type Estado = "activa" | "bloqueada"`
  - `interface CuentaResponse { id: string; nombre: string; email: string; perfil: Rol; bloqueada: boolean }`
  - `interface FiltrosCuentas { rol?: Rol; estado?: Estado; busqueda?: string }`
  - `listarCuentas(filtros?: FiltrosCuentas): Promise<CuentaResponse[]>` — `GET /usuarios`
    con query string armada solo con los filtros presentes (mismo criterio que
    `filtrarBanco()`)

### 2. Página (`frontend/src/pages/`)

- [x] `Cuentas.tsx` (nuevo)
  - Estado: `cuentas: CuentaResponse[] | null`, `rol`, `estado`, `busqueda`
  - `useEffect` dispara `listarCuentas(filtros)` en cada cambio de filtro (patrón `Banco.tsx`)
  - Tabla: Nombre, Email, Rol (tag), Estado (tag activa/bloqueada), fila navega a
    `/cuentas/{id}` con `onClick`
  - "Limpiar filtros" resetea los 3 estados
  - Link "+ Nueva cuenta" → `/docentes/nuevo` (no botón de acción nueva, ver decisión arriba)
- [x] `_placeholders.tsx` (extendido)
  - `CuentaDetallePlaceholder` — mismo estilo que `InicioPlaceholder`, texto "Detalle de
    cuenta — pendiente de pantalla propia (US-2.2.7)"

### 3. Integración

- [x] `router.tsx` — ruta `/cuentas` (`<Cuentas />`, `RequireRole rol="administrador"`) y
  `/cuentas/:usuarioId` (`<CuentaDetallePlaceholder />`, mismo guard), agregadas junto al
  resto de las rutas de `AppLayout`

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-20

## Métricas de Tiempo

| Fase | Elapsed |
|------|---------|
| Fase 0 — Validación de Contexto | 230s |
| Fase 1 — Escenarios BDD | 339s |
| Fase 2 — Plan de Implementación | 75s |
| Fase 3 — Implementación (4 tareas) | 192s |
| Fase 4 — Tests Unitarios | 169s |
| Fase 5 — Tests de Integración (n/a, frontend puro) | 19s |
| Fase 6 — Validación BDD | 39s |
| Fase 7 — Quality Gates | 232s |
| **Total (Fases 0–7)** | **~22 min** |

## Lecciones Aprendidas

- ✅ Reutilizar el tipo `Rol` de `@/lib/session.ts` en vez de redefinirlo en `cuentas-api.ts`
  evitó una duplicación silenciosa — el mismo tipo ya circulaba por `RequireRole` y `Login.tsx`.
- 💡 Para US frontend puras que consumen un endpoint ya filtrable (`GET /usuarios?rol=&estado=&busqueda=`),
  un único `useEffect` que reacciona a los tres filtros (mismo patrón `Banco.tsx`) es
  suficiente sin debounce — el volumen de datos de este BC (decenas de cuentas) no lo justifica.
- ⚠️ Al testear un flujo con dos `selectOptions` seguidos (cada uno dispara su propio fetch por
  el `useEffect`), hay que mockear una respuesta de fetch por cada disparo intermedio, no solo
  la final — un mock faltante produce un `Unhandled Rejection` silencioso que Vitest reporta
  aparte de los resultados de test (los tests igual pasan, pero contamina la corrida).
