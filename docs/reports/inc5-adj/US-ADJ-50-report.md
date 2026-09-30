# Reporte de Implementación: US-ADJ-50 - Docente ve el ranking de "Preguntas más falladas"

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-50 |
| **Título** | Docente ve el ranking de "Preguntas más falladas" |
| **Producto** | cognion (analytics, frontend) |
| **Prioridad** | Tercera US de la Iteración 4 frontend del Incremento 5-ADJ — par backend→frontend de RF-22 |
| **Puntos estimados** | 3 (sin asignación formal, mismo criterio que el resto de Analytics) |
| **Fecha inicio** | 2026-09-14 |
| **Fecha fin** | 2026-09-14 |
| **Tiempo real** | ~19 min de tracking (Fases 0, 3, 4, 7, 8; Fase 2 sin registrar — se inició la planificación sin llamar `start-phase 2` antes del checkpoint de aprobación) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Cierra el par backend→frontend de RF-22 (`US-ADJ-46`, backend, ya cerrado): pantalla con el
ranking de preguntas más falladas de una materia (o de una comisión puntual), ordenado por
tasa de error descendente y numerado por posición en la lista ya ordenada por el backend.
Mismo esqueleto de selectores Materia→Comisión y misma escala de severidad (≥50% rojo, 20-49%
ámbar, <20% verde) que `DesempenoPorTema.tsx` (`US-4.2.6`), a nivel de pregunta individual en
vez de tema. A diferencia de `EvolucionTemporal.tsx` (`US-ADJ-49`), esta pantalla tiene entrada
directa en `AppNav.tsx` — se accede como informe de primer nivel, no por drill-down. Frontend
puro, sin cambios de backend.

Segunda US de la iteración bajo el criterio operativo de Víctor (2026-09-14): la verificación
manual en navegador real se concentra en un solo pase al cierre completo de la Iteración 4, no
se repite por cada US — esta US se cierra solo con Vitest/tsc/oxlint.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro, consume el endpoint ya expuesto por `US-ADJ-46`
(`GET /analytics/materias/{id}/ranking-preguntas-falladas?comision_id=`).

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/analytics-api.ts` (modificado) — nueva interface
  `RankingPreguntaFalladaResponse`, interface interna `RankingPreguntaFalladaApiResponse`,
  mapper `mapearRankingPreguntaFallada`, función `obtenerRankingPreguntasFalladas(materiaId,
  comisionId?, signal?)`
- ✅ `frontend/src/pages/analytics/RankingPreguntasFalladas.tsx` (nuevo) — selectores
  Materia→Comisión (mismo patrón de `DesempenoPorTema.tsx`), listado `.ranking-row` numerado
  por posición (índice de presentación en la lista, no un campo que viaje en la respuesta),
  enunciado truncado a una línea, color por severidad reutilizando la misma función
  `severidad()`/`COLOR_TEXTO` duplicada localmente (sin componente compartido entre `US-4.2.6`
  y esta, mismo criterio documentado en la spec)
- ✅ `frontend/src/router.tsx` (modificado) — ruta nueva
  `/analytics/ranking-preguntas-falladas`, `RequireRole rol="docente"`
- ✅ `frontend/src/components/AppNav.tsx` (modificado) — entrada "Preguntas más falladas" en
  el menú del Docente

**Total archivos:** 4 (0 backend, 4 frontend — 1 nuevo, 3 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/pages/analytics/RankingPreguntasFalladas.test.tsx` (nuevo) — 6 tests: estado
  inicial sin listado, consulta de toda la materia sin `comision_id` con listado numerado,
  acotar a una comisión puntual reconsulta con `comision_id`, color por severidad (rojo/ámbar/
  verde), estado vacío sin preguntas presentadas, cambiar de Materia reinicia Comisión a "Toda
  la materia"
- ✅ `frontend/src/components/AppNav.test.tsx` (modificado) — "Docente ve sus 6 ítems" →
  "Docente ve sus 7 ítems", agrega la aserción de la entrada nueva

#### Tests de Integración

No aplica — sin cambios de backend ni de RBAC de router más allá de la ruta nueva, ya cubierta
por el propio test de la pantalla.

#### Escenarios BDD

No aplica — frontend puro, mismo criterio que `US-ADJ-48`/`49`.

**Total tests nuevos/actualizados:** 6 nuevos + 1 actualizado · **Estado:** 487/487 frontend
pasando (corrida completa con `--coverage`, segunda corrida en verde; la primera corrida con
`--coverage` mostró 5 fallos intermitentes en tests ajenos a esta US —`ResetearPassword`,
`NuevaPreguntaOpcionMultiple`, `NuevaPreguntaVerdaderoFalso`, `AutoregistroDocente`,
`CambiarPassword`— por timeout de 5000ms bajo carga de instrumentación, confirmados en verde
de forma aislada; mismo flake preexistente ya documentado en `US-ADJ-24`/`35`/`36`/`37`/`49`)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (`npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 487/487 | Sin regresiones | ✅ |
| **Coverage global (branches)** | 81.86% | ≥ 80% (`US-ADJ-16`) | ✅ |
| **Coverage `analytics-api.ts`** | 100% stmts/branches/functions | — | ✅ |
| **Coverage `RankingPreguntasFalladas.tsx`** | 93.88% stmts, 81.48% branches, 82.35% funcs | — | ✅ |
| **Coverage `AppNav.tsx`** | 100% en las tres métricas | — | ✅ |
| **Coverage `router.tsx`** | 100% (línea de import) | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-50-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Materia completa por defecto: listado numerado ordenado por tasa de error descendente,
  agregado de toda la materia
- [x] Acotar a una comisión: el listado se recalcula solo con esa comisión (`comision_id` en
  la query)
- [x] Color por severidad: ≥50% rojo, 20-49% ámbar, <20% verde
- [x] Materia sin preguntas presentadas: mensaje de estado vacío, sin listado
- [x] Acceso sin rol Docente: `RequireRole` bloquea la ruta (mismo mecanismo ya probado en
  `US-4.2.5`/`6`/`US-ADJ-48`/`49`, sin test de integración propio adicional)

**Estado:** 5/5 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro, mismo esqueleto exacto de `DesempenoPorTema.tsx` (`US-4.2.6`) trasladado a
pregunta individual en vez de tema: dos `useEffect` encadenados (Materia → Comisión, luego
Materia+Comisión → consulta), reseteo de estado al cambiar de Materia, mismos umbrales de
severidad de UI (no de dominio).

### Decisión de diseño: numeración de presentación

La posición del ranking (`1.`, `2.`, ...) se calcula como `índice + 1` sobre la lista ya
ordenada por el backend — no es un campo que viaje en la respuesta ni se recalcula del lado
del cliente por ningún criterio propio. Documentado como invariante explícita en la spec
(`US-ADJ-50.md` §Invariantes) y respetado sin ambigüedad en la implementación.

---

## Cambios no Previstos

Ninguno respecto del plan aprobado.

---

## Testing Manual Realizado

Ninguno en esta US — decisión operativa de Víctor (2026-09-14): la verificación manual en
navegador real se concentra en un solo pase al cierre completo de la Iteración 4 (con
`US-ADJ-51`), resembrando la base de datos para esa corrida, en vez de repetirse por cada US.
Ver `feedback_uat_navegador_solo_cierre_iteracion` en la memoria del proyecto.

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

`US-ADJ-51` (frontend de RF-23) queda como última US para completar la Iteración 4 del
Incremento 5-ADJ. Al cerrarla, corresponde el pase único de verificación manual en navegador
real con resiembra de base de datos, y luego la Iteración 5 (revisión documental de cierre).

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 30s |
| Plan | No registrado (se omitió `start-phase 2` antes del checkpoint de aprobación) |
| Implementación | 80s |
| Tests Unitarios | 527s (incluye 2 corridas completas de la suite para diagnosticar fallas ajenas a esta US) |
| Quality Gates | 439s (incluye 2 corridas de `--coverage`, la primera con flakes preexistentes) |
| Documentación | 45s |
| **TOTAL** | **~19 min de tracking efectivo (fases con registro)** |

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar el esqueleto exacto de `DesempenoPorTema.tsx` (selectores, `useEffect`
   encadenados, severidad) evitó cualquier fricción de diseño — la US se implementó sin
   ajustes al plan original.
2. Correr los archivos que fallaron bajo `--coverage` de forma aislada, antes de asumir una
   regresión propia, confirmó rápido que los 5 fallos eran contención de CPU y no un problema
   introducido por esta US.

### Recomendaciones para Próximas Historias

1. Mismo patrón que `US-ADJ-37`/`48`/`49`: evitar correr `npx vitest run --coverage` más de
   una vez en paralelo — bajo carga, tests con `testTimeout` de 5000ms flaquean de forma
   intermitente sin relación con el código tocado.
2. Recordar llamar `start-phase 2` antes de generar el plan, aunque la aprobación del usuario
   sea inmediata — esta US quedó sin ese dato en el tracking.
