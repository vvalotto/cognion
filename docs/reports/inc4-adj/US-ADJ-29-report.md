# Reporte de Implementación: US-ADJ-29 - Home del Estudiante

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-29 |
| **Título** | Home del Estudiante |
| **Producto** | cognion |
| **Prioridad** | Alta — resuelve el punto de aterrizaje post-login del Estudiante |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | ~22 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Tercera US de la Iteración 1b: reemplaza `InicioPlaceholder` por una Home real para el rol
Estudiante, con 2 cards de acceso directo (Mis Actividades, Mi Desempeño). Sin gaps nuevos —
reutiliza la decisión de saludo genérico ya tomada en `US-ADJ-28` ("Hola, Estudiante" en vez
de "Hola, {nombre}"). Único rol que sigue en `InicioPlaceholder` después de esta US:
Administrador (`US-ADJ-30`).

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/pages/HomeEstudiante.tsx` (nuevo) — saludo genérico + 2 cards de acceso
- ✅ `frontend/src/pages/Inicio.tsx` — agrega la rama `rol === "estudiante"`

**Total archivos:** 2 (0 backend, 2 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/pages/HomeEstudiante.test.tsx` (nuevo) — 5 tests (saludo, 2 cards,
  navegación por clic y teclado)
- ✅ `frontend/src/pages/Inicio.test.tsx` — actualizado: Estudiante ahora ve `HomeEstudiante`
  en vez del placeholder

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` — actualizado: `/` con sesión estudiante renderiza la Home
  (no más placeholder), agregado el caso de Administrador (sigue en placeholder), +1 test de
  navegación real por clic; corregidos 2 tests preexistentes que ahora ambiguaban entre el
  ítem del `AppNav` y la card de la Home (`getByText` → `getByRole`/`getAllByText`)

**Total tests nuevos/actualizados:** 11 · **Estado:** 322/322 frontend pasando (flake
intermitente preexistente en `NuevaPreguntaOpcionMultiple.test.tsx` observado en una corrida
de la suite completa, no reproducido en la corrida final — mismo caso ya documentado en
`US-ADJ-24`/`26`/`28`, ajeno a esta US)

#### Escenarios BDD

No aplica — frontend puro, mismo criterio que `US-ADJ-24`/`27`/`28`.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (5 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (comando real de `npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 322/322 | Sin regresiones | ✅ |
| **Coverage `HomeEstudiante.tsx`** | 100% stmts/lines/functions, 83.33% branches | — | ✅ |
| **Coverage `Inicio.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage global frontend (branches)** | 79.76% | ≥ 80% | ⚠️ ver "Deuda Técnica" |

Fuente: `quality/reports/inc4-adj/US-ADJ-29-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Estudiante ve sus 2 cards de acceso
- [x] Click en una card navega a su ruta
- [x] Otro rol no ve la Home del Estudiante

**Estado:** 3/3 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Idéntico a `US-ADJ-28`: card-grid con `role="button"` + `onClick`/`onKeyDown`, despacho por
rol en `Inicio.tsx` sin estado propio.

### Flujo de Datos

```
Ruta índice (/)
  → <Inicio /> lee getSession()?.rol
      "docente"        → <HomeDocente />
      "estudiante"      → <HomeEstudiante /> (2 cards)  ← agregado en esta US
      "administrador" / null → <InicioPlaceholder /> (hasta US-ADJ-30)
  → click en card → navigate(card.to)
```

---

## Cambios no Previstos

Al agregar la rama `estudiante`, dos tests preexistentes de `router.test.tsx` (de `US-ADJ-27`)
quedaron ambiguos: buscaban `screen.getByText("Mis Actividades")` para verificar el `AppNav`,
pero ese texto ahora también aparece en la card de la Home — `findByText`/`getByText` fallan
con "multiple elements found". Corregido acotando esos tests a `getByRole("link", ...)` (para
el ítem del menú) o desestructurando `getAllByText(...)` cuando el test necesitaba
específicamente la card. No es un bug de la implementación — es la consecuencia esperada de
que dos textos iguales convivan en la misma pantalla (menú + card), detectada al correr la
suite completa en Fase 4.

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — verificado con la suite
automatizada completa. El recorrido en navegador real queda cubierto por `US-ADJ-31`.

---

## Deuda Técnica

- **No introducida por esta US, pero sigue presente:** umbral global de cobertura de branches
  del frontend (80%) sigue roto — 79.76% tras esta US. Mismo chip abierto (`task_ec36dcbe`).

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-30` — Home del Administrador (última de la Iteración 1b)

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 10s |
| Plan | 19s |
| Implementación | 40s |
| Tests Unitarios | 323s |
| Tests de Integración | 129s |
| Quality Gates | 120s |
| Documentación | 677s |
| **TOTAL** | **~1318s (~22 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar la decisión de saludo genérico de `US-ADJ-28` sin reabrir la discusión ahorró
   tiempo de Fase 0.

### Recomendaciones para Próximas Historias

1. **`US-ADJ-30` va a repetir el mismo problema de ambigüedad de texto** si algún ítem del
   menú de Administrador coincide con el título de una card de su Home (ej. "Comisiones") —
   anticipar el ajuste de los tests de `router.test.tsx` (`getByRole("link", ...)` para el
   `AppNav`) desde el principio, no como corrección posterior.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
