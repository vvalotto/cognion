# Plan de Implementación: US-1.1.9 - Administrador da de alta un Docente desde la UI

**Patrón:** React 19 + TypeScript (frontend) — sin cambios de backend
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-29

## Métricas de Tiempo (tracking real, `tracker_cli.py`)

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Validación de contexto | 60s |
| Fase 1 — BDD | 14s |
| Fase 2 — Plan | 240s |
| Fase 3 — Implementación (4 tareas) | 229s |
| Fase 4 — Tests unitarios | 102s |
| Fase 5 — Tests de integración | 38s |
| Fase 6 — Validación BDD | 14s |
| Fase 7 — Quality gates | 168s |

> No se compara contra estimaciones humanas (`PRIN-001`) — el tracking registra tiempo real
> de ejecución del agente, no varianza contra esfuerzo humano estimado.

## Lecciones Aprendidas

- ⚠️ El `.feature` asumía que la ruta ya estaba protegida por rol ("comportamiento ya cubierto
  por US-1.1.6"), pero `router.tsx`/`AppLayout.tsx` no tenían ningún guard client-side — el
  401/403 de `US-1.1.6` es puramente reactivo (se dispara al recibir esos códigos de una
  respuesta HTTP, no al navegar a una pantalla). Gap detectado en Fase 2, antes de escribir
  código; consultado con Víctor, que eligió un componente `RequireRole` reutilizable en vez de
  un chequeo inline, pensando en las próximas rutas protegidas por rol.
- 💡 Detectar el gap en Fase 2 (planificación) evitó tener que reescribir `router.tsx` después
  de implementar la pantalla — mismo patrón que el gap de `materia` en `US-1.1.8`.
- ✅ Reutilizar la estructura de `Registro.tsx`/`RegistroExito.tsx` (validación de cliente,
  manejo de 409 inline, `location.state` con fallback) redujo el tiempo de implementación de
  `AltaDocente.tsx`/`AltaDocenteExito.tsx` a un ajuste de campos y textos, sin decisiones de
  diseño nuevas.

## Decisión de scope (gap detectado en Fase 2, antes de implementar)

Los escenarios "acceso sin sesión" / "acceso con rol insuficiente" del `.feature`
(`tests/features/inc1/US-1.1.9-alta-docente-ui.feature`) asumen ruta protegida, pero
`router.tsx`/`AppLayout.tsx` no tienen ningún guard client-side hoy — el único mecanismo de
401/403 de `US-1.1.6` es reactivo (se dispara al recibir esos códigos de una respuesta HTTP,
no al navegar a una pantalla; confirmado contra `AppLayout.test.tsx`). Decisión de Víctor: se
agrega un componente `RequireRole` reutilizable (no un chequeo inline en `AltaDocente.tsx`),
pensando en las próximas rutas protegidas por rol de incrementos futuros (banco de preguntas,
analytics). Sin decisión arquitectónica nueva — mismo patrón de sesión (`lib/session.ts`) y
navegación imperativa ya usado en `api-client.ts`.

## Componentes a Implementar

### 1. Guard de ruta — `RequireRole`

- [x] `frontend/src/components/RequireRole.tsx`
  - Props: `rol: Rol` (rol requerido), `children: ReactNode`
  - Sin sesión (`getSession() === null`) → `<Navigate to="/login" replace />`
  - Con sesión pero `session.rol !== rol` → renderiza mensaje inline "Acceso denegado" (sin
    componente de página dedicado — no hay precedente de pantalla de error de rol en el
    wireframe, es un mensaje de una línea dentro del layout de app)
  - Con sesión y rol correcto → renderiza `children`

### 2. Frontend — Pantallas de alta de Docente

- [x] `frontend/src/pages/AltaDocente.tsx`
  - Formulario: nombre, email, contraseña, confirmar contraseña (misma validación de cliente
    que `Registro.tsx` — coincidencia y mínimo 8 caracteres; la regla de negocio la aplica el
    backend)
  - Perfil fijo en "Docente" — tag informativo no editable (§2.6, sin selector)
  - Copy de ayuda: contraseña temporal, el Docente la usa para generar invitaciones
  - `POST /usuarios` vía `apiFetch` con `{ nombre, email, password, perfil: "docente" }`
  - 201 → navega a `/docentes/nuevo/exito` pasando `nombre`/`email` del Docente creado (via
    `navigate(..., { state })`, mismo patrón que `Registro.tsx` → `RegistroExito.tsx`)
  - 409 (`ApiError`, email ya registrado) → error inline en el propio formulario (mismo patrón
    que `Registro.tsx`/`LoginError`, sin navegar)
  - Acción secundaria "Cancelar" → vuelve a `/` (listado de cuentas fuera de alcance; home real
    de la app en esta iteración)
- [x] `frontend/src/pages/AltaDocenteExito.tsx`
  - Confirmación con nombre y email del Docente creado (recibidos por `location.state`, con
    fallback genérico si se accede sin state — mismo patrón que `RegistroExito.tsx`)
  - Aclaración explícita: "Todavía no está asignado a ninguna comisión" (§2.7)
  - Acción primaria "Dar de alta otro Docente" → vuelve a `/docentes/nuevo` (limpia el
    formulario, flujo pensado para altas en lote)

### 3. Integración

- [x] `frontend/src/router.tsx`
  - Agregar rutas bajo `AppLayout` (no `AuthLayout` — header de aplicación con breadcrumb, no
    tarjeta centrada): `/docentes/nuevo` → `<RequireRole rol="administrador"><AltaDocente /></RequireRole>`,
    `/docentes/nuevo/exito` → mismo guard envolviendo `<AltaDocenteExito />`

**Estado:** 4/4 tareas completadas

---

## Addendum post-Fase 9 — Corrección de UAT (estilo institucional)

Agregado después de cerrar el tracking de la US, a partir de un smoke test manual de Víctor en
navegador real (ver `docs/reports/inc1/US-1.1.9-report.md` para el detalle completo de las dos
causas: bug de cascada CSS sin `@layer` + paleta/tipografía no institucionales). A pedido de
Víctor, esta corrección queda dentro de US-1.1.9 aunque afecta a todas las pantallas de
Identidad (no solo a las de esta US).

- [x] `frontend/src/index.css` — reescrito: elimina el bloque heredado sin `@layer`, recalibra
  los tokens de color de shadcn a la paleta institucional del prototipo, cambia tipografía a
  Roboto
- [x] `frontend/src/components/Logo.tsx` (nuevo) — marca SVG de Cognión
- [x] `frontend/src/components/TopStrip.tsx` (nuevo) — barra institucional superior
- [x] `frontend/src/layouts/AuthLayout.tsx` — agrega `TopStrip` + bloque de marca
- [x] `frontend/src/layouts/AppLayout.tsx` — agrega `TopStrip` + header con marca + avatar de rol
- [x] `frontend/package.json` — `@fontsource/roboto` (nuevo), saca `@fontsource-variable/geist`
  (sin uso)
- [x] Tests: `AppLayout.test.tsx` (+2), `AuthLayout.test.tsx` (nuevo, 2 tests)

**Verificado en navegador real** (no solo Vitest): login → `/docentes/nuevo` → alta de Docente
→ `/docentes/nuevo/exito`, con la paleta institucional y sin el bug de ancho/centrado.
