# Reporte de Implementación: US-ADJ-28 - Home del Docente

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-28 |
| **Título** | Home del Docente |
| **Producto** | cognion |
| **Prioridad** | Alta — resuelve el punto de aterrizaje post-login del Docente |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | ~7 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Segunda US de la Iteración 1b: reemplaza `InicioPlaceholder` por una Home real para el rol
Docente, con 4 cards de acceso directo a sus áreas (Banco de Preguntas, Actividades,
Desempeño por alumno, Desempeño por tema). Gap de backend detectado en Fase 0 y decidido con
Víctor: el wireframe pide "Hola, {nombre}", pero ningún endpoint expone el nombre del propio
usuario autenticado — se usa un saludo genérico ("Hola, Docente") en vez de agregar
`GET /usuarios/me`, desvío documentado en la spec. Misma decisión aplicará a
`US-ADJ-29`/`30`.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/pages/HomeDocente.tsx` (nuevo) — saludo genérico + 4 cards de acceso
- ✅ `frontend/src/pages/Inicio.tsx` (nuevo) — despacha la ruta índice por `session.rol`
- ✅ `frontend/src/router.tsx` — la ruta índice usa `<Inicio />` en vez de
  `<InicioPlaceholder />` fijo

**Total archivos:** 3 (0 backend, 3 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/pages/HomeDocente.test.tsx` (nuevo) — 5 tests (saludo, 4 cards, navegación
  por clic, navegación por teclado)
- ✅ `frontend/src/pages/Inicio.test.tsx` (nuevo) — 3 tests (Docente ve Home, Estudiante y
  Administrador siguen en placeholder)

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` — +3 tests (`/` renderiza Home del Docente con sesión
  docente, sigue en placeholder con sesión estudiante, navegación real por clic desde la Home
  a Actividades)

**Total tests nuevos:** 11 · **Estado:** 315/315 frontend pasando, sin regresiones

#### Escenarios BDD

No aplica — frontend puro sobre rutas ya protegidas, mismo criterio que `US-ADJ-24`/`27`.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (5 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (comando real de `npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 315/315 | Sin regresiones | ✅ |
| **Coverage `HomeDocente.tsx`** | 100% stmts/lines/functions, 50% branches (rama `false` del guard de teclado, mismo patrón aceptado en `Actividades.tsx`) | — | ✅ |
| **Coverage `Inicio.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage global frontend (branches)** | 79.78% | ≥ 80% | ⚠️ ver "Deuda Técnica" |

Fuente: `quality/reports/inc4-adj/US-ADJ-28-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Docente ve sus 4 cards de acceso
- [x] Click en una card navega a su ruta
- [x] Otro rol no ve la Home del Docente

**Estado:** 3/3 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro. `HomeDocente.tsx` sigue el mismo patrón de card-grid ya usado en
`MateriasActividades.tsx`/`Actividades.tsx` (`role="button"` + `onClick`/`onKeyDown`).
`Inicio.tsx` es un componente de despacho puro (sin estado), delegando en `getSession()?.rol`.

### Flujo de Datos

```
Ruta índice (/)
  → <Inicio /> lee getSession()?.rol
      "docente"        → <HomeDocente /> (4 cards)
      otro rol / null  → <InicioPlaceholder /> (hasta US-ADJ-29/30)
  → click en card → navigate(card.to)
```

---

## Cambios no Previstos

Ninguno adicional al gap de backend ya documentado en Fase 0 (ver Resumen Ejecutivo).

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — se verificó con la suite
automatizada completa (`tsc -b`, oxlint, Vitest, incluyendo navegación real por clic sobre el
router completo). El recorrido en navegador real queda cubierto por la Validación E2E
consolidada de `US-ADJ-31`.

---

## Deuda Técnica

- **No introducida por esta US, pero sigue presente:** el umbral global de cobertura de
  branches del frontend (80%) sigue roto — 79.78% tras esta US. Mismo chip abierto
  (`task_ec36dcbe`).

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-29` — Home del Estudiante
- [ ] `US-ADJ-30` — Home del Administrador (mismo desvío de saludo genérico a confirmar)

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 11s |
| Plan | 25s |
| Implementación | 46s |
| Tests Unitarios | 82s |
| Tests de Integración | 89s |
| Quality Gates | 138s |
| Documentación | 21s |
| **TOTAL** | **~412s (~7 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Detectar el gap de "Hola, {nombre}" en Fase 0 (antes de escribir la spec) evitó una vuelta
   atrás desde Fase 3 — mismo hábito ya consolidado en `US-ADJ-25`/`26`.
2. Resolver la ruta índice con un componente de despacho (`Inicio.tsx`) en vez de lógica
   condicional inline en `router.tsx` deja `US-ADJ-29`/`30` como un cambio de una línea cada
   una (agregar el `if` de su rol).

### Recomendaciones para Próximas Historias

1. `US-ADJ-29`/`30` van a repetir la misma pregunta de saludo — ya está resuelta acá
   (genérico, sin `GET /usuarios/me`), no hace falta reabrir la discusión.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
