# Reporte de Implementación: US-ADJ-56 - El desempeño del Estudiante incluye las sesiones en vivo

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-56 |
| **Título** | El desempeño del Estudiante incluye las sesiones en vivo |
| **Producto** | analytics (BC Analytics, lee BC Actividad Evaluativa por puerto in-process) |
| **Prioridad** | Primera US formal de `Incremento 6-ADJ` (después de `US-ADJ-58`) |
| **Puntos estimados** | 5 |
| **Fecha inicio** | 2026-09-27 |
| **Fecha fin** | 2026-09-27 |
| **Tiempo real** | ~197 min (tracking automático — incluye la espera de varias corridas completas de test en background) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

"Mi desempeño" (Estudiante) y "Desempeño por alumno" (Docente) ganan una sección propia
"Sesiones en vivo" — comisión, fecha, cantidad de preguntas, correctas/incorrectas, puntaje
final y posición ("3° de 14") de cada sesión en vivo `Finalizada` en la que participó el
estudiante, separada del acumulado de período abierto (que no cambia). Cierra el hueco de
alcance que RF-15/RF-16 dejaban abierto desde el Incremento 4 (el modo en vivo no existía
todavía) y que la validación manual de `US-6.3.10` volvió a exponer.

Segundo puerto de Analytics hacia Actividad Evaluativa (`SesionEnVivoDesempenoConsultaPort`,
junto a `EvaluacionDesempenoConsultaPort` de `US-4.1.1`): agrupa los streams
`ActividadEvaluativaEnVivo`/`ParticipacionEnVivo` del event store para `correctas`/
`incorrectas`/`puntaje_final`, y lee además la proyección `ranking_por_sesion` (`US-6.2.3`) para
`posicion`/`total_participantes`, sin reimplementar el desempate ya resuelto por
`SQLAlchemyProyeccionesEnVivoRepository.ranking()`. El nombre de la comisión (`horario`) se
resuelve en el Use Case con el `ComisionConsultaPort` ya existente (`US-4.2.2`) — evita que el
Estudiante necesite un permiso HTTP que no tiene. Sin endpoint nuevo: los dos endpoints
existentes de `mi-desempeno`/`estudiantes/{id}/desempeno` quedan cubiertos ampliando la única
respuesta que ya comparten.

De paso se completó un renombre pendiente de documentación (`SP-ADJ-02` → `Incremento 6-ADJ`,
decisión de Víctor tomada al inicio de la sesión) que había quedado incompleto en el PR de
renombre original — `tests/step_defs/`, `tests/features/`, `docs/plans/`, `docs/reports/` y
`quality/reports/` quedaron consistentes.

---

## Componentes Implementados

### Código Fuente (BC Analytics)

- ✅ `src/analytics/entities/ports/sesion_en_vivo_desempeno_consulta_port.py` — nuevo, `SesionEnVivoDesempenoConsultaPort` + DTO `SesionEnVivoDesempenoResumen`
- ✅ `src/analytics/frameworks/adapters/sesion_en_vivo_desempeno_consulta_port_in_process.py` — nuevo, agrupa `events` + `ranking_por_sesion`
- ✅ `src/analytics/use_cases/obtener_desempeno_estudiante.py` — `SesionEnVivoDetalle` nuevo, `DesempenoEstudiante.sesiones_en_vivo`, `ObtenerDesempenoEstudianteUseCase` recibe 2 puertos más
- ✅ `src/analytics/frameworks/dependencies.py` — `get_analytics_controller` cablea los 2 puertos nuevos
- ✅ `src/analytics/frameworks/api/schemas.py` — `SesionEnVivoDetalleResponse`, `DesempenoEstudianteResponse.sesiones_en_vivo`
- ✅ `src/analytics/frameworks/api/analytics_router.py` — `_a_response()` mapea el campo nuevo (sin endpoint nuevo)

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/analytics-api.ts` — `SesionEnVivoDesempenoResponse` + mapeo snake_case↔camelCase
- ✅ `frontend/src/pages/analytics/DesempenoResumenDetalle.tsx` — `armarFilasEnVivo`, sección "Sesiones en vivo" (props opcionales `filasEnVivo`/`mensajeVacioEnVivo`)
- ✅ `frontend/src/pages/analytics/MiDesempeno.tsx` / `DesempenoPorAlumno.tsx` — pasan los props nuevos
- ✅ `DesempenoPorComisionDetalleEstudiante.tsx` (RF-20) — **sin cambios**, decisión de alcance (RF-20 no incluye el vivo)

**Total archivos de producción modificados/creados:** 10 (6 nuevos, 4 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `tests/unit/inc4/test_sesion_en_vivo_desempeno_consulta_port.py` — 3 tests (nuevo)
- ✅ `tests/unit/inc4/test_sesion_en_vivo_desempeno_consulta_port_in_process.py` — 11 tests (nuevo, funciones puras del adapter)
- ✅ `tests/unit/inc4/test_obtener_desempeno_estudiante.py` — 6 tests nuevos (`TestSesionesEnVivo`) + 6 existentes migrados al Use Case de 3 dependencias
- ✅ `tests/unit/inc4/test_analytics_controller.py` — Fakes de los 2 puertos nuevos (sin tests nuevos, solo corrección de firma)
- ✅ Frontend: `analytics-api.test.ts` (2 tests ampliados), `DesempenoResumenDetalle.test.tsx` (7 tests nuevos + 2 de `armarFilasEnVivo`), `MiDesempeno.test.tsx`/`DesempenoPorAlumno.test.tsx`/`DesempenoPorComisionDetalleEstudiante.test.tsx` (fixture ampliado)

**Total tests unitarios backend:** 814/814 pasando (100% coverage en `src/analytics` fuera de `frameworks/`)
**Total tests frontend (Vitest):** 796/796 pasando

#### Tests de Integración
- ✅ `tests/integration/inc4/test_sesion_en_vivo_desempeno_consulta_port.py` — 8 tests nuevos contra Postgres real
- ✅ `tests/integration/inc4/test_analytics_router.py` — `TestAnalyticsRouterSesionesEnVivo`, 2 tests nuevos end-to-end (router → controller → use case → los 2 adapters → Postgres)
- ✅ `tests/integration/inc4/conftest.py` — ampliado para limpiar también `ranking_por_sesion`

**Total tests de integración del proyecto:** 555/555 pasando

#### Escenarios BDD
- ✅ `tests/features/inc6-adj/US-ADJ-56-desempeno-sesiones-en-vivo.feature` — 9 escenarios
- ✅ `tests/step_defs/inc4/test_us_adj_56_steps.py` — steps nuevo, resueltos contra el endpoint HTTP real

**Total escenarios BDD del proyecto:** 375/376 pasando (el único fallo,
`test_rechazo_fuera_del_período_vigente` de `inc3`, es el flake preexistente ya documentado en
`CLAUDE.md` — falla igual en `develop` limpio, ajeno a esta US)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (6 archivos, corrida directa) | 9.74/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 8 | ≤ 10 | ✅ |
| **Índice Mantenibilidad (mín/archivo)** | 57.88 | > 20 | ✅ |
| **Coverage** (`src/analytics`, excluye `frameworks/` por `pyproject.toml`) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/analytics/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (6 archivos modificados/agregados) | 15 errores, 2 warnings | 0 CRITICAL | ✅ |

Fuente completa: `quality/reports/inc6-adj/US-ADJ-56-quality.json`.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 6 |
| PEP8 | 0 | 1 | 5 |
| Complexity | 0 | 0 | 6 |
| DeadCode | 6 | 0 | 0 |
| Maintainability | 0 | 0 | 6 |
| Pylint | 0 | 1 | 5 |
| Spelling | 6 | 0 | 0 |
| Types | 2 | 0 | 3 |
| UnusedImports | 1 | 0 | 5 |

Los 15 "errors" son fallas de herramientas ausentes o con timeout, no hallazgos de código:
`vulture`/`codespell` no están instalados (`DeadCode`/`Spelling`, 6+6), y mypy/pylint embebidos
en CodeGuard exceden su timeout interno de 10s/5s en corrida en frío (`Types`/`UnusedImports`) —
mismo bug ya documentado en `CLAUDE.md` (`vvalotto/software_limpio#70`/`#71`). El warning de
`Pylint` (7.54/10 para `schemas.py`) es un falso valor del pylint embebido analizando el archivo
aislado — la corrida directa sobre los 6 archivos da 9.74/10. El warning de `PEP8` (línea
larga en `analytics_router.py:1`) es el docstring del módulo, preexistente desde 2026-09-05, no
tocado por esta US.

---

## Criterios de Aceptación

- [x] El Estudiante ve sus sesiones en vivo — fila por sesión con fecha, puntaje, posición, correctas e incorrectas
- [x] La posición es la del ranking final (mismo desempate que `ObtenerRankingDeSesion`)
- [x] Sesiones que no terminaron (`EnEspera`/`EnCurso`) no aparecen
- [x] Sesiones canceladas (`US-ADJ-58`) no aparecen
- [x] Se unió pero no respondió — 0 puntos, 0 correctas, con su posición
- [x] Período abierto no se mezcla — el acumulado no cambia, sesiones en vivo en su propia sección
- [x] Sin sesiones en vivo — sección vacía (texto literal a cargo del frontend, ya testeado en Vitest)
- [x] El Docente ve lo mismo para el estudiante elegido en "Desempeño por alumno"
- [x] Otra materia no se mezcla

**Estado:** 9/9 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Clean Architecture BC-first (`entities → use_cases → interface_adapters → frameworks`). Sin
BC nuevo ni endpoint nuevo — amplía un puerto/adapter/use case ya existente de Analytics.

### Flujo de Datos

```
GET /analytics/materias/{id}/mi-desempeno (rol estudiante)
  → AnalyticsController.obtener_mi_desempeno
    → ObtenerDesempenoEstudianteUseCase.execute(estudiante_id, materia_id)
        → EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas (sin cambios, US-4.1.1)
        → SesionEnVivoDesempenoConsultaPort.listar_sesiones_finalizadas (nuevo)
            → agrupa streams ActividadEvaluativaEnVivo/ParticipacionEnVivo (events)
            → lee ranking_por_sesion para posicion/total_participantes
        → ComisionConsultaPort.listar_comisiones_por_materia (US-4.2.2, resuelve horario)
    → DesempenoEstudiante(evaluaciones, resumen, sesiones_en_vivo)
```

---

## Desafíos y Soluciones

### Desafío 1: `puntaje_final` no sale de donde parece

**Descripción:** Al escribir los primeros steps BDD, sembrar solo la fila de `ranking_por_sesion`
(sin el evento `RespuestaEnVivoRegistrada` real) hacía que `puntaje_final` volviera en `0` — 2
escenarios fallaron con ese síntoma.

**Solución:** `puntaje_final` sale de `ParticipacionEnVivo.puntaje_acumulado` (reconstruido del
event stream), no de `ranking_por_sesion.puntaje_acumulado` (que solo se usa para el desempate
de `posicion`/`total_participantes`) — corregido agregando la respuesta real en el setup de
esos 2 escenarios.

**Aprendizaje:** Cuando un adapter compone dos fuentes de datos para un mismo aggregate lógico
(event stream + proyección de lectura), los tests de más alto nivel (BDD/integración) tienen
que sembrar ambas de forma consistente, no asumir que una implica la otra.

### Desafío 2: Correr dos suites de integración en paralelo genera ~111 fallos que no son regresiones

**Descripción:** Por apuro, se lanzaron dos corridas de `pytest tests/integration/` en background
al mismo tiempo. Ambas reportaron decenas de fallos en archivos completamente ajenos a esta US
(`ranking_preguntas_falladas`, `tasa_error_por_tema`, todo `inc6`).

**Solución:** Los `conftest.py` de este proyecto son `autouse` y hacen `DELETE FROM events` (y
similares) al inicio/fin de cada test — dos procesos pytest concurrentes contra la misma base de
test se pisan. Se diagnosticó por el patrón (fallos en archivos no tocados) y se corrigió
corriendo una sola vez, secuencial: 555/555 en verde.

**Aprendizaje:** Nunca lanzar dos corridas de test de integración/BDD en paralelo contra la
misma base de datos de test en este proyecto.

---

## Documentación Actualizada

- [x] Docstrings agregados/actualizados en los 6 archivos nuevos/modificados de `src/`
- [x] `docs/plans/US-ADJ-56-plan.md` completado con estado, métricas y lecciones aprendidas
- [x] `docs/design/domain/BC-analytics-modelo.md` — nueva query, nuevo puerto, nota de alcance RF-15 actualizada
- [x] `docs/traceability/matrix.md` — RF-15/RF-16 referencian esta US
- [x] `docs/architecture/20-context-map-integrations.md` — fila Actividad Evaluativa↔Analytics ampliada
- [x] `CHANGELOG.md` actualizado (`[Unreleased]`)
- [x] `quality/reports/inc6-adj/US-ADJ-56-quality.json`/`-codeguard.json`/`-coverage.json` generados
- [x] Renombre `SP-ADJ-02`→`Incremento 6-ADJ` completado en las carpetas que habían quedado
  inconsistentes (`tests/step_defs/`, `tests/features/`, `quality/reports/`)
- [ ] `docs/plans/inc6-adj/inc6-adj-candidatas.md`/`CLAUDE.md` — se actualizan al cierre de sesión (`/checkpoint`), no en esta fase

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Fase 0 — Validación de Contexto | 130 s |
| Fase 1 — Generación de Escenarios BDD | 89 s |
| Fase 2 — Plan de Implementación | 408 s |
| Fase 3 — Implementación (9 tareas) | 580 s |
| Fase 4 — Tests Unitarios | 8312 s (incluye la espera de dos corridas completas de Vitest en background) |
| Fase 5 — Tests de Integración | 1059 s |
| Fase 6 — Validación BDD | 702 s |
| Fase 7 — Quality Gates | 402 s |
| Fase 8 — Documentación | 3635 s (incluye el renombre pendiente de `SP-ADJ-02`) |
| **TOTAL (Fases 0-8)** | **≈ 15317 s (≈ 255 min de reloj, ≈ 197 min efectivos según el tracker)** |

> Nota (PRIN-001): estos tiempos son de ejecución del agente, no comparables a estimación
> humana. Buena parte del tiempo de Fase 4/8 es espera de corridas de test en background, no
> trabajo activo.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Resolver el nombre de la comisión en el Use Case (no en el frontend ni en el adapter) evitó
   un problema de permisos HTTP que solo se hubiera descubierto en Fase 5/6.
2. Reusar `ranking_por_sesion` para el desempate de posición, en vez de recalcularlo, mantiene
   una sola fuente de verdad para ese orden (`ObtenerRankingUseCase` y este adapter coinciden).

### Lo que Puede Mejorar

1. No lanzar corridas de test largas en paralelo contra la misma base de test — el diagnóstico
   de "fallos en archivos ajenos = interferencia, no regresión" costó dos corridas completas
   (~10 min) antes de confirmarlo con una corrida limpia.

### Recomendaciones para Próximas Historias

1. `US-ADJ-57` (Docente solo ve y modifica los recursos de sus materias) sigue en la cola de
   `Incremento 6-ADJ` — mismo criterio de secuenciación ya documentado en
   `docs/plans/inc6-adj/inc6-adj-candidatas.md`.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-57` — El Docente solo ve y modifica los recursos de sus materias
- [ ] `US-ADJ-08` — Ver la materia/comisión de la invitación antes de registrarse
- [ ] `US-ADJ-07` — Nombre legible de la comisión en el detalle de cuenta (track informal)
- [ ] Barrido documental de `docs/plans/PLAN-CM.md` §12 — pendiente al cierre de la iteración

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-27
