# Reporte de Implementación: US-ADJ-48 - Docente ve "Desempeño por comisión" con drill-down

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-48 |
| **Título** | Docente ve "Desempeño por comisión" con drill-down |
| **Producto** | cognion (analytics, frontend) |
| **Prioridad** | Primera US de la Iteración 4 frontend del Incremento 5-ADJ — par backend→frontend de RF-20 |
| **Puntos estimados** | 5 (sin asignación formal, mismo criterio que el resto de Analytics) |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | ~23 min de tracking (Fases 0, 3, 4, 7, 8, 9 — ver nota en "Tiempo Invertido") |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Cierra el par backend→frontend de RF-20 (`US-ADJ-44`, backend, ya cerrado): pantalla
"Desempeño por comisión" con selectores Materia→Comisión (cascada), tabla ordenable por
columna (Nombre, % Aciertos, Actividades pendientes — `null` renderizado como "Sin datos" en
cursiva, nunca "0%") y dos niveles de drill-down. El nivel 1 reusa `DesempenoResumenDetalle.tsx`
(componente ya compartido por "Mi desempeño"/"Desempeño por alumno"), al que se le agregó un
`onFilaClick` opcional sin afectar su uso existente. El nivel 2 (revisión completa de una
evaluación puntual) reusa el contenido visual de la pantalla de revisión del Estudiante,
extraído a un componente nuevo (`RevisionEvaluacionContenido.tsx`) parametrizado por la
etiqueta de "respuesta propia" ("Tu respuesta" vs. "Respuesta del estudiante"), sin duplicar
JSX ni tocar el comportamiento de `RevisionEvaluacion.tsx` (Estudiante). Frontend puro, sin
cambios de backend.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro, consume el endpoint ya expuesto por `US-ADJ-44`
(`GET /analytics/materias/{id}/comisiones/{id}/desempeno`) y el guard de rol ya ampliado de
`GET /evaluaciones/{id}/revision`.

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/analytics-api.ts` — nueva interfaz `DesempenoComisionFilaResponse` y
  función `obtenerDesempenoPorComision(materiaId, comisionId, signal?)`, mismo patrón
  snake_case↔camelCase que el resto del archivo
- ✅ `frontend/src/pages/analytics/DesempenoResumenDetalle.tsx` (modificado) — agrega
  `onFilaClick?: (evaluacionId: string) => void` opcional; sin él, el comportamiento de
  `MiDesempeno.tsx` (`US-4.1.3`) y `DesempenoPorAlumno.tsx` (`US-4.2.5`) no cambia
- ✅ `frontend/src/pages/analytics/DesempenoPorComision.tsx` (nuevo) — nivel 0: selectores
  Materia→Comisión, tabla ordenable, `actividadesPendientes > 0` resaltado en ámbar
- ✅ `frontend/src/pages/analytics/DesempenoPorComisionDetalleEstudiante.tsx` (nuevo) — drill-down
  1°, misma lógica de datos que `DesempenoPorAlumno.tsx`, renderiza `DesempenoResumenDetalle`
  con `onFilaClick`
- ✅ `frontend/src/pages/actividad-evaluativa/RevisionEvaluacionContenido.tsx` (nuevo) —
  estadísticas + detalle pregunta por pregunta, extraído de `RevisionEvaluacion.tsx` sin
  cambiar su comportamiento, parametrizado por `etiquetaRespuestaPropia`
- ✅ `frontend/src/pages/actividad-evaluativa/RevisionEvaluacion.tsx` (modificado) — pasa a
  usar `RevisionEvaluacionContenido` con `etiquetaRespuestaPropia="Tu respuesta"`
- ✅ `frontend/src/pages/analytics/RevisionEvaluacionDocente.tsx` (nuevo) — drill-down 2°, reusa
  `obtenerRevision` y `RevisionEvaluacionContenido` con `etiquetaRespuestaPropia="Respuesta del
  estudiante"`
- ✅ `frontend/src/router.tsx` — 3 rutas nuevas bajo `/analytics/desempeno-por-comision`,
  todas `RequireRole rol="docente"`
- ✅ `frontend/src/components/AppNav.tsx` — entrada "Desempeño por comisión" en el bloque
  Docente, antes de "Desempeño por alumno"

**Total archivos:** 9 (0 backend, 9 frontend — 5 nuevos, 4 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/lib/analytics-api.test.ts` (+2 casos) — `obtenerDesempenoPorComision`
- ✅ `frontend/src/pages/analytics/DesempenoResumenDetalle.test.tsx` (nuevo) — 6 tests: sin
  `onFilaClick` la fila no es clicable, con `onFilaClick` click/Enter/espacio invocan el
  callback, una tecla no relevante no lo invoca, estado vacío
- ✅ `frontend/src/pages/analytics/DesempenoPorComision.test.tsx` (nuevo) — 9 tests: estado
  inicial, tabla con estados mixtos, comisión sin evaluaciones finalizadas, click navega al
  drill-down 1°, orden por columna (asc/desc, `null` como valor más bajo), toggle de dirección
  al reclickear el mismo encabezado, tecla Enter en una fila, error de red
- ✅ `frontend/src/pages/analytics/DesempenoPorComisionDetalleEstudiante.test.tsx` (nuevo) — 3
  tests: resumen + detalle, estado vacío, click navega al drill-down 2°
- ✅ `frontend/src/pages/analytics/RevisionEvaluacionDocente.test.tsx` (nuevo) — 2 tests:
  revisión completa con la etiqueta "Respuesta del estudiante", evaluación inexistente

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` (+6 casos) — 3 rutas nuevas con `RequireRole` (acceso
  denegado a Estudiante, renderiza con Docente para nivel 0/1/2) + navegación real por clic
  desde `AppNav`
- ✅ `frontend/src/components/AppNav.test.tsx` (actualizado) — Docente pasa de 5 a 6 ítems

#### Escenarios BDD

No aplica — frontend puro, sin lógica de dominio backend, mismo criterio que
`US-ADJ-24`/`35`/`36`/`37`.

**Total tests nuevos/actualizados:** 20 nuevos + 8 actualizados · **Estado:** 469/469 frontend
pasando (el flake preexistente de contención de CPU de `NuevaPreguntaOpcionMultiple.test.tsx`,
documentado en `US-ADJ-24`/`37`, no se reprodujo en esta corrida completa)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 469/469 | Sin regresiones | ✅ |
| **Coverage `analytics-api.ts`** | 100% stmts/branches/functions | — | ✅ |
| **Coverage `DesempenoResumenDetalle.tsx`** | 100% stmts, 95% branches, 100% funcs | — | ✅ |
| **Coverage `DesempenoPorComision.tsx`** | 97.01% stmts, 87.5% branches, 92.59% funcs | — | ✅ |
| **Coverage `DesempenoPorComisionDetalleEstudiante.tsx`** | 91.67% stmts, 78.57% branches, 100% funcs | — | ✅ |
| **Coverage `RevisionEvaluacionDocente.tsx`** | 87.5% stmts, 72.73% branches, 100% funcs | — | ✅ |
| **Coverage `RevisionEvaluacionContenido.tsx`** | 100% stmts, 88.89% branches, 100% funcs | — | ✅ |
| **Coverage `router.tsx` / `AppNav.tsx`** | 100% en ambos | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-48-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python). Las ramas sin cubrir en `DesempenoPorComisionDetalleEstudiante.tsx`
y `RevisionEvaluacionDocente.tsx` son guardas de `AbortError`/parámetros de ruta ausentes, mismo
patrón ya aceptado como "inalcanzable en la práctica" en `DesempenoPorAlumno.tsx` y
`RevisionEvaluacion.tsx`.

---

## Criterios de Aceptación

- [x] Tabla con estados mixtos: una fila por estudiante, "Sin datos" en cursiva para quien no
  tiene evaluaciones finalizadas
- [x] Drill-down al detalle de un estudiante (resumen + lista de evaluaciones)
- [x] Drill-down a la revisión completa de una evaluación puntual, igual que la vería el
  propio Estudiante
- [x] RBAC: un Estudiante o Administrador no ve la pantalla (`RequireRole`)
- [x] Comisión sin ningún estudiante con evaluaciones finalizadas: tabla igual, todos "Sin datos"

**Estado:** 5/5 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro sobre Clean Architecture BC-first — sin capas `entities/use_cases/
interface_adapters/frameworks` de dominio, consume endpoints ya expuestos por `US-ADJ-44`.
Reutilización deliberada de dos componentes visuales ya existentes en vez de duplicar JSX:
`DesempenoResumenDetalle.tsx` (drill-down 1°, compartido con `US-4.1.3`/`US-4.2.5` desde antes
de esta US) y `RevisionEvaluacionContenido.tsx` (drill-down 2°, extraído de `RevisionEvaluacion.tsx`
en esta US para compartirlo entre la vista del Estudiante y la del Docente).

### Flujo de Navegación

```
/analytics/desempeno-por-comision
  → DesempenoPorComision (Materia → Comisión → tabla)
  → click en una fila
/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId
  → DesempenoPorComisionDetalleEstudiante (DesempenoResumenDetalle + onFilaClick)
  → click en una .eval-item
/analytics/desempeno-por-comision/.../evaluaciones/:evaluacionId/revision
  → RevisionEvaluacionDocente (RevisionEvaluacionContenido, etiqueta "Respuesta del estudiante")
```

---

## Cambios no Previstos

Ninguno respecto del plan aprobado. Un ajuste menor durante la implementación: la primera
versión de las filas de la tabla usaba `role="button"` sobre `<tr>` para exponer la
afordancia de clic, lo que pisaba el rol semántico `row` (detectado por un test de
`getAllByRole("row")` que solo encontraba la fila de encabezado) — corregido quitando el
`role` explícito y dejando `onClick`/`onKeyDown`/`tabIndex` sin cambiar la semántica de la
tabla.

---

## Testing Manual Realizado

Recorrido completo en navegador real (Claude Browser) contra un backend real (`uvicorn`) y
PostgreSQL local. **Hallazgo relevante, no relacionado con el código de esta US**: la base de
datos local estaba completamente vacía (0 usuarios) al momento de la verificación — no la base
de "estabilización" con los 17 estudiantes reales que documenta
`tests/uat/datos-reales/bitacora-estudiante.md`. Se sembró un Administrador
(`scripts/seed_admin.py`), un Docente, una Materia, una Comisión, 2 Estudiantes (vía invitación,
flujo real) y una Actividad con 2 preguntas V/F para poder ejercitar el flujo completo, y se
limpiaron todos los datos al finalizar (verificado: 0 usuarios al cierre).

Escenarios verificados, todos sin hallazgos:
1. Comisión sin evaluaciones finalizadas: ambos estudiantes en "Sin datos", 1 pendiente en ámbar
2. Comisión con datos mixtos: "Ana Pérez" 50% / 0 pendientes, "Juan Gómez" "Sin datos" / 1
   pendiente en ámbar
3. Drill-down 1°: click en una fila navega al detalle del estudiante (resumen + `.eval-item`)
4. Drill-down 2°: click en la evaluación navega a la revisión completa, con "Respuesta del
   estudiante" (no "Tu respuesta") y breadcrumb de 4 niveles
5. RBAC: sesión de Estudiante contra la ruta de nivel 0 muestra "Acceso denegado"

**Nota para Víctor:** el hallazgo de la base vacía queda fuera del alcance de esta US — se
reportó aparte para que confirme qué pasó con los datos de la bitácora de estabilización
(¿un `pytest` corrido en otra sesión, un reset intencional, u otra base?).

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

`US-ADJ-49`/`50`/`51` (frontend de RF-21/22/23) quedan para completar la Iteración 4 del
Incremento 5-ADJ — independientes entre sí y de esta US según
`docs/plans/inc5-adj/inc5-adj-candidatas.md`.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 33s |
| Plan | sin registrar (gap de tracking — no se invocó `start-phase 2`) |
| Implementación | 199s |
| Tests Unitarios | 435s |
| Tests de Integración | sin registrar (gap de tracking — no se invocó `start-phase 5`) |
| Quality Gates | 568s |
| Documentación | 82s |
| **TOTAL registrado** | **~1317s (~22 min)** |

Dos fases (Plan, Tests de Integración) se ejecutaron pero sin `start-phase`/`end-phase`
explícitos — gap de disciplina de tracking de esta sesión, no de las fases en sí (ambas
generaron sus artefactos: `US-ADJ-48-plan.md` y las +6 pruebas de `router.test.tsx`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar `DesempenoResumenDetalle.tsx` y extraer `RevisionEvaluacionContenido.tsx` en vez
   de duplicar JSX evitó tener dos implementaciones visuales del mismo componente para
   Estudiante/Docente — el mismo criterio que ya usaban `US-4.1.3`/`US-4.2.5`.
2. Verificar en navegador real con datos sembrados vía API (no solo UI) permitió armar el
   escenario completo (Materia→Comisión→Estudiantes→Actividad→Evaluación finalizada) en pocos
   minutos, y detectó a tiempo el hallazgo de la base vacía antes de asumir que se estaba
   reusando la base de estabilización real.

### Recomendaciones para Próximas Historias

1. Evitar `role="button"` explícito sobre elementos con rol semántico propio (`<tr>`, `<li>`,
   etc.) cuando se agrega una afordancia de clic — pisa el rol nativo y rompe queries de
   testing-library que dependen de él (`getAllByRole("row")` en este caso). `onClick` +
   `onKeyDown` + `tabIndex` alcanzan sin tocar el rol.
2. Recordar `start-phase`/`end-phase` explícitos en cada fase del skill, incluso cuando el
   artefacto de esa fase (plan.md, tests de integración) ya se generó — el tracking depende de
   la disciplina del comando, no de que el trabajo se haya hecho.
