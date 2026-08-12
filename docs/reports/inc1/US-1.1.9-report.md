# Reporte de Implementación: US-1.1.9

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.9 - Administrador da de alta un Docente desde la UI
- **Puntos estimados:** 3
- **Tiempo real:** ~22 min (fases 0-9, tracking de ejecución del agente, no comparable contra
  esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-07-29

Cuarta y última US de la Iteración 2 (frontend de Identidad). Consume la infraestructura de
`US-1.1.6` y cierra la Iteración 2 — habilita la apertura de BL-002
(`docs/plans/PLAN-CM.md` §7). Incluye un componente nuevo, `RequireRole` (guard de ruta por
rol), fuera del alcance original de la spec — gap detectado en Fase 2: el `.feature` asumía
ruta protegida, pero `router.tsx`/`AppLayout.tsx` (`US-1.1.6`) no tenían ningún guard
client-side, solo el manejo reactivo de 401/403 de `apiFetch`; ver adenda en
`docs/specs/inc1/US-1.1.9.md`.

**UAT manual de Víctor tras el cierre de Fase 9** (vibe coding, smoke test en navegador real):
detectó que el estilo de la app no respetaba el prototipo aprobado (`docs/design/ux/prototipos/
identidad-registro-login.html`, US-1.0.2) — ni en esta US ni en ninguna de las anteriores de la
Iteración 2. Investigado y corregido en la misma US (ver sección dedicada más abajo), a pedido
explícito de Víctor de que quede dentro de US-1.1.9 y no como fix aparte.

---

## Componentes Implementados

### Guard de ruta — `RequireRole` (ampliación acordada, fuera del alcance original)
- ✅ `frontend/src/components/RequireRole.tsx` (nuevo) — componente reutilizable: sin sesión
  → `<Navigate to="/login" replace />`; sesión con rol distinto del requerido → mensaje
  inline "Acceso denegado"; rol correcto → renderiza `children`

### Pantallas de Alta de Docente (`frontend/src/pages/`)
- ✅ `AltaDocente.tsx` (nuevo) — formulario controlado (nombre/email/contraseña/confirmar
  contraseña), perfil fijo en "Docente" sin selector (§2.6 `wireframes-identidad.md`), valida
  contraseña en cliente (≥8 caracteres, coincidencia); consume `POST /usuarios` con
  `perfil: "docente"`; 201 → `/docentes/nuevo/exito` (pasa `nombre`/`email` por
  `location.state`); 409 → error inline en el formulario
- ✅ `AltaDocenteExito.tsx` (nuevo) — confirmación con nombre y email del Docente creado (con
  fallback genérico si se accede sin `location.state`), aclaración explícita de que todavía
  no está asignado a ninguna comisión (§2.7); acción "Dar de alta otro Docente" vuelve al
  formulario

### Integración
- ✅ `frontend/src/router.tsx` (editado) — rutas nuevas `/docentes/nuevo` y
  `/docentes/nuevo/exito` bajo `AppLayout`, ambas envueltas en
  `RequireRole rol="administrador"`

### Corrección de UAT — estilo institucional no respetado (ampliación acordada con Víctor)
Detectado en un smoke test manual en navegador real, después de cerrar Fase 9. Dos causas
distintas, ambas en `frontend/`:
1. **Bug de cascada CSS:** `frontend/src/index.css` tenía un bloque de CSS heredado (boilerplate
   de un starter genérico — `#root { width:1126px; text-align:center; ... }`, estilos globales
   de `h1`/`h2` a 56px/24px) declarado **fuera de cualquier `@layer`**. En Tailwind v4 cualquier
   regla sin `@layer` gana automáticamente contra las utilities de Tailwind (que sí están en
   capas) — le pisaba `text-lg`/`font-semibold` a todos los `<h1>` de Login/Registro/AltaDocente
   y angostaba/centraba toda la app a 1126px. Vigente desde `US-1.1.6`, invisible en Vitest
   (jsdom no aplica cascada de layers de la misma forma perceptible visualmente) y nunca antes
   verificado en un navegador real.
2. **Paleta/tipografía no coincidían con el prototipo aprobado** (`docs/design/ux/prototipos/
   identidad-registro-login.html`, US-1.0.2): la app usaba el tema neutro/gris por defecto de
   shadcn (negro `oklch(0.205 0 0)`) con fuente Geist, en vez del azul institucional `#1D75B5` +
   verde `#53AA74` + Roboto: sin barra institucional ("FACULTAD DE INGENIERÍA · UNER") ni marca
   de Cognión en ninguna pantalla.

- ✅ `frontend/src/index.css` (reescrito) — elimina el bloque heredado sin `@layer`; tokens de
  color de shadcn recalibrados a la paleta institucional del prototipo; tipografía Roboto
  (`@fontsource/roboto`, reemplaza a `@fontsource-variable/geist`, ya sin uso)
- ✅ `frontend/src/components/Logo.tsx` (nuevo) — marca SVG de Cognión (§1
  `wireframes-identidad.md`)
- ✅ `frontend/src/components/TopStrip.tsx` (nuevo) — barra institucional superior
- ✅ `frontend/src/layouts/AuthLayout.tsx` (editado) — agrega `TopStrip` + bloque de marca
  (logo, "Cognión", "Evaluación universitaria") sobre el `Outlet`
- ✅ `frontend/src/layouts/AppLayout.tsx` (editado) — agrega `TopStrip` + header con
  `brand-mini` (logo + "Cognión") y avatar con iniciales del rol
- ✅ `frontend/package.json` / `package-lock.json` — agrega `@fontsource/roboto`, saca
  `@fontsource-variable/geist`

---

## Métricas de Calidad

Umbrales adaptados a stack frontend (TypeScript/React) — ver `docs/plans/inc1/US-1.1.9-context.md`.

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| ESLint/oxlint | 0 errores, 1 warning (preexistente en `button.tsx`, no introducido por esta US) | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 46/46 pasan (suite completa) | 100% pasan | ✅ |
| Cobertura `RequireRole.tsx` (statements) | 100% | ≥80% (referencia) | ✅ |
| Cobertura `AltaDocente.tsx` (statements) | 85.2% | ≥80% (referencia) | ✅ |
| Cobertura `AltaDocenteExito.tsx` (statements) | 100% | ≥80% (referencia) | ✅ |
| Cobertura global del proyecto (statements/branches) | 93.61% / 88.05% | ≥80% (umbral `vitest.config`) | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc1/US-1.1.9-quality.json`)

---

## Tests Implementados

### Tests frontend (16 tests nuevos + 2 editados)
- `RequireRole.test.tsx` (3 tests) — sin sesión redirige a login, rol distinto muestra acceso
  denegado, rol correcto renderiza el contenido
- `AltaDocente.test.tsx` (4 tests) — perfil fijo sin selector, alta exitosa, email duplicado
  (409, error inline), contraseñas no coincidentes (validación de cliente)
- `AltaDocenteExito.test.tsx` (3 tests) — nombre/email desde `location.state`, fallback
  genérico sin state, botón "Dar de alta otro Docente" navega de vuelta al formulario
- `router.test.tsx` (editado, +2 tests) — `/docentes/nuevo` redirige a login sin sesión,
  renderiza dentro del layout de app con sesión de administrador
- `AppLayout.test.tsx` (editado, +2 tests) — marca institucional + barra superior, avatar con
  iniciales del rol (corrección de UAT)
- `AuthLayout.test.tsx` (nuevo, 2 tests) — marca institucional + barra superior, renderiza el
  contenido anidado vía `Outlet` (corrección de UAT — layout sin test previo)

### Escenarios BDD (4 escenarios) — `tests/features/inc1/US-1.1.9-alta-docente-ui.feature`
- Alta exitosa de un Docente
- Alta rechazada por email duplicado
- Acceso sin sesión
- Acceso con rol insuficiente

Sin runner Gherkin dedicado para TypeScript — los 4 escenarios están cubiertos 1:1 por
`AltaDocente.test.tsx` y `RequireRole.test.tsx`/`router.test.tsx` (ver Fase 6).

**Todos los tests pasando:** ✅ 46/46 frontend (30 previos + 16 nuevos)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/components/RequireRole.tsx` (nuevo)
- `frontend/src/pages/AltaDocente.tsx` (nuevo)
- `frontend/src/pages/AltaDocenteExito.tsx` (nuevo)
- `frontend/src/router.tsx` (editado)
- `frontend/src/index.css` (reescrito — corrección de UAT, paleta/tipografía institucional)
- `frontend/src/components/Logo.tsx` (nuevo — corrección de UAT)
- `frontend/src/components/TopStrip.tsx` (nuevo — corrección de UAT)
- `frontend/src/layouts/AuthLayout.tsx` (editado — corrección de UAT)
- `frontend/src/layouts/AppLayout.tsx` (editado — corrección de UAT)
- `frontend/package.json` / `package-lock.json` (editado — `@fontsource/roboto`, corrección de UAT)

### Tests
- `frontend/src/components/RequireRole.test.tsx` (nuevo)
- `frontend/src/pages/AltaDocente.test.tsx` (nuevo)
- `frontend/src/pages/AltaDocenteExito.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (editado)
- `frontend/src/layouts/AppLayout.test.tsx` (editado — corrección de UAT)
- `frontend/src/layouts/AuthLayout.test.tsx` (nuevo — corrección de UAT)
- `tests/features/inc1/US-1.1.9-alta-docente-ui.feature` (nuevo)

### Documentación
- `docs/specs/inc1/US-1.1.9.md` (editado — adenda de `RequireRole`)
- `docs/plans/inc1/US-1.1.9-context.md` (nuevo)
- `docs/plans/inc1/US-1.1.9-plan.md` (nuevo)
- `docs/reports/inc1/US-1.1.9-report.md` (este archivo)
- `quality/reports/inc1/US-1.1.9-quality.json` (nuevo)
- `CHANGELOG.md` (entrada `[US-1.1.9]`)
- `docs/traceability/matrix.md` (nota de cierre de Iteración 2 / apertura de BL-002)
- `docs/plans/inc1/inc1-candidatas.md` (US-1.1.9 tachada como cerrada)

---

## Criterios de Aceptación

- [x] Alta exitosa con datos válidos crea el Usuario con perfil Docente, muestra la pantalla
      de confirmación y aclara que el Docente todavía no está asignado a ninguna comisión
- [x] Alta rechazada por email duplicado muestra el error en el propio formulario
- [x] Acceso sin sesión redirige a login
- [x] Acceso con rol distinto de administrador muestra acceso denegado

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Abrir BL-002 — Iteración 2 (Frontend de Identidad) completa: backend y frontend de
      Identidad ambos implementados (criterio de cierre de baseline,
      `docs/plans/PLAN-CM.md` §7)
- [ ] Actualizar `CLAUDE.md` con el cierre de esta US y el estado de BL-002

---

## Lecciones Aprendidas

- ⚠️ El `.feature` asumía que la ruta ya estaba protegida por rol ("comportamiento ya cubierto
  por US-1.1.6"), pero `router.tsx`/`AppLayout.tsx` no tenían ningún guard client-side — el
  401/403 de `US-1.1.6` es reactivo, no un guard de navegación. Gap detectado en Fase 2, antes
  de escribir código.
- ✅ Consultar con Víctor durante la planificación (Fase 2) evitó tener que reescribir
  `router.tsx` después de implementar la pantalla — mismo patrón que el gap de `materia` en
  `US-1.1.8`: detectar gaps spec-vs-código en la fase de plan, no en la de implementación.
- 💡 Reutilizar la estructura de `Registro.tsx`/`RegistroExito.tsx` (validación de cliente,
  manejo de 409 inline, `location.state` con fallback) redujo la implementación de
  `AltaDocente.tsx`/`AltaDocenteExito.tsx` a un ajuste de campos y textos, sin decisiones de
  diseño nuevas.
- ⚠️ **El estilo institucional del prototipo aprobado (US-1.0.2) nunca se verificó en un
  navegador real** desde `US-1.1.6` — ni Vitest/jsdom ni la revisión de código detectan un bug
  de cascada CSS (regla sin `@layer` pisando utilities de Tailwind) ni una paleta de colores
  equivocada. Detectado recién en un UAT manual de Víctor (smoke test en navegador) al cierre
  de esta US. Confirma la regla del proyecto (`CLAUDE.md`, "para UI o frontend changes, iniciar
  el servidor de desarrollo y probar en un navegador antes de reportar como completo") — el
  smoke test automatizado con `fetch` mockeado no sustituye una revisión visual real.
- 💡 A pedido de Víctor, esta corrección quedó dentro de US-1.1.9 en vez de como fix aparte —
  aunque toca todas las pantallas de Identidad (no solo las de esta US), por tratarse de un
  hallazgo de UAT descubierto durante el cierre de esta misma historia.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-29
