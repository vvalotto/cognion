# Reporte de Implementación: US-ADJ-27 - Menú de navegación persistente en AppLayout

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-27 |
| **Título** | Menú de navegación persistente en AppLayout |
| **Producto** | cognion |
| **Prioridad** | Alta — primera US de la Iteración 1b, gate para `US-ADJ-28`/`29`/`30` |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | ~10 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Primera US de la Iteración 1b del Incremento 4-ADJ (portal de entrada): resuelve el gap
señalado en `HITO-9` — ninguna pantalla post-login tenía navegación cruzada entre áreas, el
usuario dependía de escribir URLs de memoria. Componente `AppNav.tsx` nuevo, integrado en
`AppLayout.tsx` debajo del header, con ítems condicionados por rol (Docente 5, Estudiante 3,
Administrador 4) y resaltado de la sección actual. Frontend puro sobre rutas ya protegidas por
`RequireRole` (`US-1.1.9`), sin backend nuevo — mismo criterio que `US-ADJ-24`.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/components/AppNav.tsx` (nuevo) — menú condicionado por rol, ítem activo
  vía `useLocation()`
- ✅ `frontend/src/layouts/AppLayout.tsx` — integra `<AppNav />` debajo del header, solo con
  sesión activa

**Total archivos:** 2 (0 backend, 2 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/components/AppNav.test.tsx` (nuevo) — 7 tests (ítems por rol, ítem activo,
  hrefs)

#### Tests de Integración
- ✅ `frontend/src/layouts/AppLayout.test.tsx` — +3 tests (menú visible con sesión, oculto sin
  sesión, ítems del rol correcto)
- ✅ `frontend/src/router.test.tsx` — +3 tests (navegación real por clic con el router
  completo: Docente a Banco de Preguntas, Administrador a Comisiones, Estudiante sin ítems de
  otros roles)

**Total tests nuevos:** 13 · **Estado:** 304/304 frontend pasando, sin regresiones

#### Escenarios BDD

No aplica — frontend puro sobre rutas ya protegidas, sin comportamiento de dominio nuevo.
Mismo criterio que `US-ADJ-24`, `US-2.1.10`, `US-3.4.2`.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (5 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (comando real de `npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 304/304 | Sin regresiones | ✅ |
| **Coverage `AppNav.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage `AppLayout.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage global frontend (branches)** | 79.81% | ≥ 80% | ⚠️ ver "Deuda Técnica" |

Fuente: `quality/reports/inc4-adj/US-ADJ-27-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Docente ve sus 5 ítems de menú
- [x] Estudiante ve sus 3 ítems de menú
- [x] Administrador ve sus 4 ítems de menú
- [x] El ítem de la sección actual queda resaltado
- [x] Click en un ítem navega a su ruta
- [x] Sin sesión activa no se muestra el menú

**Estado:** 6/6 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro, sin componentes de dominio. `AppNav.tsx` es un componente de presentación
puro: una tabla constante de ítems por rol, sin estado propio, delegando en `useLocation()` de
`react-router` para saber qué ítem resaltar.

### Flujo de Datos

```
AppLayout (con sesión activa)
  → <AppNav rol={session.rol} /> — lee ITEMS_POR_ROL[rol]
  → useLocation().pathname → esItemActivo(pathname, item.to) por cada ítem
  → click en <Link to={item.to}> → navegación client-side (React Router)
```

---

## Cambios no Previstos

Ninguno — el plan se ejecutó sin desvíos respecto de la spec aprobada.

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — se verificó con la suite
automatizada completa (`tsc -b`, oxlint, Vitest, incluyendo navegación real por clic sobre el
router completo en `router.test.tsx`). El recorrido en navegador real queda cubierto por la
Validación E2E consolidada de `US-ADJ-31` (Iteración 2 del incremento).

---

## Deuda Técnica

- **No introducida por esta US, pero sigue presente:** el umbral global de cobertura de
  branches del frontend (`vite.config.ts`, 80%) sigue roto — 79.81% tras esta US (mejoró
  desde 78.74% de `US-ADJ-24`, pero no lo cierra). Mismo chip abierto (`task_ec36dcbe`,
  "Agregar tests a Comisiones.tsx").

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-28` — Home del Docente (reemplaza `InicioPlaceholder` para rol `docente`)
- [ ] `US-ADJ-29` — Home del Estudiante
- [ ] `US-ADJ-30` — Home del Administrador

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 41s |
| Plan | 129s |
| Implementación | 52s |
| Tests Unitarios | 100s |
| Tests de Integración | 100s |
| Quality Gates | 127s |
| Documentación | 66s |
| **TOTAL** | **~615s (~10 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar el precedente de `US-ADJ-24` para la decisión BDD (frontend puro → sin `.feature`)
   evitó reabrir esa discusión — quedó documentado en `context.md` con referencia explícita.
2. Los tests de "navegación real por clic" en `router.test.tsx` (usando el router completo, no
   `MemoryRouter` aislado) dieron más confianza que solo tests de componente — verifican que
   las rutas destino realmente existen y renderizan.

### Recomendaciones para Próximas Historias

1. Cuando una US define una tabla estática (ítems de menú, rutas por rol), conviene fijar esa
   tabla en un único lugar (`ITEMS_POR_ROL`) para que `US-ADJ-28`/`29`/`30` puedan reusarla si
   necesitan la misma lista de accesos en las cards de cada home.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
