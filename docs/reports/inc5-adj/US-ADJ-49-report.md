# Reporte de Implementación: US-ADJ-49 - Docente ve la evolución temporal de un estudiante y de su comisión

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-49 |
| **Título** | Docente ve la evolución temporal de un estudiante y de su comisión |
| **Producto** | cognion (analytics, frontend) |
| **Prioridad** | Segunda US de la Iteración 4 frontend del Incremento 5-ADJ — par backend→frontend de RF-21 |
| **Puntos estimados** | 5 (sin asignación formal, mismo criterio que el resto de Analytics) |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | ~13 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Cierra el par backend→frontend de RF-21 (`US-ADJ-45`, backend, ya cerrado): gráfico de línea
SVG hecho a mano (sin librería) con dos series simultáneas — % de aciertos del estudiante
(sólida, azul) y promedio de su comisión (punteada, verde) — sobre un eje X unificado por la
unión de actividades de ambas series, respetando el orden que ya devuelve el backend. Accesible
únicamente desde un link nuevo en el detalle de estudiante de `US-ADJ-48`, sin entrada directa
en `AppNav.tsx` (tal como especifica la spec). Frontend puro, sin cambios de backend.

Primera US de la iteración con el nuevo criterio operativo de Víctor: la verificación manual
en navegador real se concentra en un solo pase al cierre completo de la Iteración 4, no se
repite por cada US — esta US se cierra solo con Vitest/tsc/oxlint.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro, consume los endpoints ya expuestos por `US-ADJ-45`
(`GET /analytics/materias/{id}/estudiantes/{id}/evolucion-temporal` y
`GET /analytics/materias/{id}/comisiones/{id}/evolucion-temporal`).

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/analytics-api.ts` — nuevas interfaces `EvolucionTemporalPuntoResponse`
  y `EvolucionTemporalComisionPuntoResponse`, funciones `obtenerEvolucionTemporalEstudiante` y
  `obtenerEvolucionTemporalComision`
- ✅ `frontend/src/pages/analytics/EvolucionTemporal.tsx` (nuevo) — gráfico SVG: `armarEjeX`
  (unión de actividades, ancla en la serie de comisión, agrega al final las actividades
  propias del estudiante que no estén ahí), `SerieGrafico` (polyline solo con >1 punto, sin
  interpolar huecos), leyenda, estado vacío, breadcrumb de 4 niveles
- ✅ `frontend/src/pages/analytics/DesempenoPorComisionDetalleEstudiante.tsx` (modificado) —
  agrega el link "Ver evolución temporal" hacia la ruta nueva, sin tocar
  `DesempenoResumenDetalle.tsx` (compartido con `US-4.1.3`/`US-4.2.5`)
- ✅ `frontend/src/router.tsx` — 1 ruta nueva anidada bajo `desempeno-por-comision`,
  `RequireRole rol="docente"`, sin entrada en `AppNav.tsx`

**Total archivos:** 4 (0 backend, 4 frontend — 1 nuevo, 3 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/lib/analytics-api.test.ts` (+4 casos) —
  `obtenerEvolucionTemporalEstudiante`/`obtenerEvolucionTemporalComision`, con y sin datos
- ✅ `frontend/src/pages/analytics/EvolucionTemporal.test.tsx` (nuevo) — 5 tests: serie completa
  con ambas etiquetas, una sola evaluación sin `<polyline>`, actividad no rendida por el
  estudiante (no aparece en su serie), estado vacío sin gráfico, error de red
- ✅ `frontend/src/pages/analytics/DesempenoPorComisionDetalleEstudiante.test.tsx` (+1 caso) —
  el link "Ver evolución temporal" navega a la ruta nueva

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` (+2 casos) — RBAC de la ruta de evolución temporal (acceso
  denegado a Estudiante, renderiza con Docente)

#### Escenarios BDD

No aplica — frontend puro, mismo criterio que `US-ADJ-48`.

**Total tests nuevos/actualizados:** 8 nuevos + 2 actualizados · **Estado:** 475/481 frontend
pasando (6 fallos en 2 archivos ajenos a esta US —`AutoregistroDocente.test.tsx` y
`CambiarPassword.test.tsx`, timeout de contención de CPU al correr la suite completa, mismo
flake preexistente ya documentado en `US-ADJ-24`/`35`/`36`/`37`)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** | 0 errores | 0 errores | ✅ |
| **Vitest** (archivos tocados) | 22/22 en aislamiento | Sin regresiones | ✅ |
| **Coverage `analytics-api.ts`** | 100% stmts/branches/functions | — | ✅ |
| **Coverage `EvolucionTemporal.tsx`** | 91.38% stmts, 86.36% branches, 100% funcs | — | ✅ |
| **Coverage `DesempenoPorComisionDetalleEstudiante.tsx`** | 91.67% stmts, 78.57% branches, 100% funcs | — | ✅ |
| **Coverage `router.tsx`** | 100% en las tres métricas | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-49-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Serie completa con varias actividades: gráfico de línea con 2 series, eje X etiquetado
  por título de actividad
- [x] Una sola evaluación: un solo punto, sin línea, para esa serie
- [x] Actividad no rendida por el estudiante: no aparece en el eje X de su serie
- [x] RBAC: un Estudiante o Administrador no ve la pantalla (`RequireRole`)

**Estado:** 4/4 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro, SVG hecho a mano sobre coordenadas calculadas en JS (sin librería de gráficos,
mismo criterio de la spec para un solo gráfico de línea simple). Reutiliza el patrón de
"pantalla wrapper + componente compartido" ya establecido en `US-ADJ-48`: el link de entrada
vive en la página wrapper (`DesempenoPorComisionDetalleEstudiante.tsx`), no en el componente
compartido (`DesempenoResumenDetalle.tsx`).

### Decisión de diseño: unión del eje X

Ambas series pueden tener actividades que la otra no tiene (el estudiante puede haber rendido
actividades fuera de esta comisión puntual; la comisión puede tener actividades que este
estudiante no rindió). La unión se ancla en el orden de la serie de comisión — la más completa
para el contexto de esta pantalla — y agrega al final las actividades propias del estudiante
que falten. Documentado como decisión explícita (no oculta) en el código y en el plan.

---

## Cambios no Previstos

Ninguno respecto del plan aprobado.

---

## Testing Manual Realizado

Ninguno en esta US — decisión operativa de Víctor (2026-09-14): la verificación manual en
navegador real se concentra en un solo pase al cierre completo de la Iteración 4 (con
`US-ADJ-50`/`51`), resembrando la base de datos para esa corrida, en vez de repetirse por cada
US. Ver `feedback_uat_navegador_solo_cierre_iteracion` en la memoria del proyecto.

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

`US-ADJ-50`/`51` (frontend de RF-22/23) quedan para completar la Iteración 4 del Incremento
5-ADJ. Al cerrar la última de las tres, corresponde el pase único de verificación manual en
navegador real con resiembra de base de datos.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 15s |
| Plan | 1215s (incluye la pausa de aprobación con el usuario) |
| Implementación | 238s |
| Tests Unitarios | 121s |
| Tests de Integración | 50s |
| Quality Gates | 314s |
| Documentación | 27s |
| **TOTAL** | **~33 min (incluye tiempo de espera de aprobación)** |

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar el mismo patrón de "pantalla wrapper + componente compartido" de `US-ADJ-48`
   (link de entrada en la wrapper, no en el componente compartido) evitó cualquier fricción de
   diseño — la US se implementó sin ajustes al plan original.
2. Documentar la decisión de merge del eje X como comentario explícito en el código (no una
   heurística oculta) deja trazable el criterio para cuando aparezca un caso real donde el
   estudiante tenga actividades fuera de la comisión evaluada.

### Recomendaciones para Próximas Historias

1. Mismo patrón que `US-ADJ-37`/`48`: evitar correr `npx vitest run` de la suite completa más
   de una vez en paralelo — los 6 fallos de esta corrida fueron, de nuevo, el flake de
   contención de CPU ya documentado, no una regresión real.
