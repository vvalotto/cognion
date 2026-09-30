# BL-011 — Incremento 6 (Sesión en Vivo) + Incremento 6-ADJ (Ajuste técnico y documental)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento (`PLAN_v1.md`, numerado) + Incremento de ajuste (fuera de secuencia, mismo criterio que `BL-005`/`BL-007`/`BL-010`) |
| Fecha apertura | 2026-09-17 |
| Fecha cierre | 2026-09-30 |
| Git tag inicial | `v0.7.1` (`BL-010`) |
| Git tag cierre | `v0.8.0` (MINOR — cierre de Incremento 6 de `PLAN_v1.md`; `Incremento 6-ADJ` se pliega en la misma baseline, sin tag propio) |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | RF-08 (creación y unión a sesión en vivo), RF-09 (dinámica en tiempo real: presentar/responder/cerrar/avanzar/finalizar) y RF-10 (puntaje y ranking) implementados de punta a punta — backend (Iteraciones 1 y 2) y frontend (Iteración 3) — y verificados con datos reales (60 participantes simultáneos, RNF de rendimiento p95 43,81 ms ≤ 100 ms) y en dispositivo real (Mac/iPhone/iPad). `Incremento 6-ADJ`: backlog diferido de `SP-ADJ-01` resuelto (`US-ADJ-06/07/08`), sesiones en vivo integradas a Analytics (`US-ADJ-56`), aislamiento de datos por Docente (`US-ADJ-57`), robustez del modo en vivo (`US-ADJ-58`), y barrido documental §12 completo. |

---

## Descripción

Dos incrementos cerrados juntos en una sola baseline, mismo criterio de secuenciación usado
para agrupar un `-ADJ` con el incremento numerado que lo origina cuando ambos quedan listos
al mismo tiempo (a diferencia de `BL-005`/`BL-006`, que sí se mantuvieron como baselines
separadas pese a mergearse el mismo día).

### Incremento 6 — Sesión en Vivo (RF-08, RF-09, RF-10)

Incremento de mayor riesgo técnico del proyecto: primer uso real de WebSockets, primer
agregado sincrónico multi-participante (`ActividadEvaluativaEnVivo`, hermano de
`ActividadEvaluativaPeriodoAbierto` dentro del mismo BC Actividad Evaluativa, `ADR-015`), y
primer RNF de rendimiento duro verificado con datos reales.

- **Iteración 0 — Modelado** (`US-6.0.1`/`US-6.0.2`, Issues #379/#380): event storming
  (`BC-actividad-evaluativa-modelo.md` §§10-18) y wireframes/prototipo, seis rondas de ajuste
  con Víctor — el cambio más significativo movió la sesión en vivo de "por Materia con
  checklist de Comisiones" a "por una Comisión puntual". Spike del algoritmo de puntaje
  resuelto antes del modelado (`Puntaje = 1000 × FactorTiempo × FactorDificultad ×
  FactorImportancia`).
- **Iteración 1 — RF-08: creación de sesión + infraestructura WebSockets** (backend,
  `US-6.1.1` a `US-6.1.4`, Issues #382-#385): canal WebSocket por `sesion_id`, JWT por query
  param, `ComisionConsultaPort` hacia Identidad, crear/unir/iniciar sesión.
- **Iteración 2 — RF-09/RF-10: dinámica en tiempo real** (backend, `US-6.2.1` a `US-6.2.9`,
  Issues #392-#400): puntaje server-side, mostrar opciones, read models
  `ranking_por_sesion`/`distribucion_por_pregunta`, responder con feedback personal, cerrar
  pregunta (histograma + ranking), avanzar, finalizar, consultas de estado/participantes/
  ranking para reconexión, y verificación E2E del RNF de rendimiento (p95 43,81 ms del use
  case `CerrarPreguntaActual` con 60 participantes simultáneos, umbral 100 ms — cumple).
- **Iteración 3 — Frontend del modo en vivo** (backend + frontend juntos, `US-6.3.0` a
  `US-6.3.10`, Issues #412-#422): tres US de backend adicionales (nombres de Estudiantes en
  broadcasts, listar sesiones de una Comisión, estado completo para reconectar la
  proyección); infraestructura de frontend (cliente API, primer canal WebSocket del frontend
  con reconexión/backoff, `StageLayout`); 6 pantallas (Docente: crear sesión/sala de espera,
  proyectar pregunta/opciones/cerrar, proyectar histograma/ranking/podio/avanzar/finalizar;
  Estudiante: ver sesiones/unirse/esperar, responder desde el celular/ver resultado/final).
  UAT de cierre en dos tramos: Tramo 1 (8 circuitos Playwright E2E, 10/10 sin inestabilidad,
  mediciones de legibilidad de la proyección) y Tramo 2 (revisión manual de Víctor en
  Mac/iPhone/iPad sobre `develop` con datos reales, 7 hallazgos — 5 resueltos directo, 1
  aparte —reconexión WebSocket "zombi" en iOS—, 2 derivados a `US-ADJ-58`).

Tres US de ajuste de la propia suite de tests del frontend detectadas en Fase 7 de
`US-6.3.7`/`6.3.8` (`US-ADJ-53`/`54`/`55`, Issues #432/#433/#437) — cobertura estable,
esperas asincrónicas correctas, timeout de Testing Library acorde a la suite completa.

### Incremento 6-ADJ — Ajuste técnico y documental

Insertado antes del cierre de `BL-011` (decisión de Víctor 2026-09-26), agrupando lo que en
un principio iba después. Cinco frentes:

- **`US-ADJ-58`** (cancelar una sesión `EnEspera`, finalizar desde cualquier etapa relajando
  INV-AEV-03, no iniciar sin participantes también en backend), Issue #445 — primera de la
  iteración, porque termina de cerrar el modo en vivo que valida esta baseline.
- **`US-ADJ-56`** (las sesiones en vivo suman al desempeño del Estudiante y al "Desempeño por
  alumno" del Docente, acumulado separado del de período abierto, sin detalle pregunta por
  pregunta), Issue #441.
- **`US-ADJ-57`** (cada Docente ve y opera solo sobre las materias/Comisiones donde está
  asignado — primitiva nueva en Identidad, `docente_pertenece_a_comision`/
  `docente_tiene_comision_en_materia`, consumida por los 4 BC ampliando su propio
  `ComisionConsultaPort`), Issue #443, 4 partes (Identidad, Banco de Preguntas, Actividad
  Evaluativa, Analytics).
- **`US-ADJ-08`** (Estudiante ve la materia/comisión de la invitación antes de registrarse —
  endpoint público nuevo `GET /invitaciones/{token}`, sin exponer el docente), Issue #448.
- **`US-ADJ-07`** (nombre legible de la comisión en el detalle de cuenta, track informal —
  `CuentaDetalle.tsx` resuelve `comisionId` vía `GET /comisiones/{id}` + `useNombreMateria`,
  mismo patrón que `ComisionDetalle.tsx`).
- **Barrido documental §12** (`docs/plans/PLAN-CM.md`): catálogo de BC en
  `docs/architecture/03-bounded-contexts.md` desactualizado desde el Incremento 1, filas de
  RF-08/09/10 en la matriz con `US-6.3.x` marcadas "especificadas" en vez de "cerradas", un
  párrafo de wireframe desactualizado, dos archivos de `/implement-us` mal ubicados, y tres
  Issues de GitHub con trabajo ya mergeado sin cerrar (#421, #422, #443) — todo corregido.

`US-ADJ-06` se dio por resuelta de hecho (`US-ADJ-37`, `UserMenu.tsx`) sin código propio —
fuera del alcance de esta baseline.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D54 | `docs/design/domain/BC-actividad-evaluativa-modelo.md` §§10-18, `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` + `prototipos/actividad-evaluativa-en-vivo.html` (+ §0 y §8 de `US-6.3.0`/`US-ADJ-58`) | Documento | Modelado y UX del modo en vivo, Iteración 0 + ampliaciones de las Iteraciones 3 y `6-ADJ` |
| CI-D55 | `docs/specs/inc6/US-6.0.1.md` a `US-6.3.10.md`, `docs/specs/ajustes/US-ADJ-53.md` a `US-ADJ-58.md` | Documento | Specs US-IEDD de las 3 iteraciones + ajustes |
| CI-D56 | `docs/reports/inc6/` (23 reportes), `docs/reports/inc6-adj/` (3 reportes) | Documento | Reportes de cierre de `/implement-us` por US |
| CI-D57 | `docs/architecture/03-bounded-contexts.md`, `docs/traceability/matrix.md`, `CLAUDE.md` | Documento | Barrido documental §12 (`Incremento 6-ADJ`) |
| CI-C27 | `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`, `use_cases/{crear,unirse_a,iniciar}_sesion_en_vivo.py`, `frameworks/websockets/` | Código de backend | Agregado `ActividadEvaluativaEnVivo`, infraestructura WebSocket (Iteración 1) |
| CI-C28 | `src/actividad_evaluativa/use_cases/{presentar_pregunta,responder_pregunta_en_vivo,cerrar_pregunta_actual,avanzar_siguiente_pregunta,finalizar_sesion_en_vivo}.py`, read models `ranking_por_sesion`/`distribucion_por_pregunta` | Código de backend | Dinámica en tiempo real, puntaje, ranking (Iteración 2) |
| CI-C29 | `src/actividad_evaluativa/use_cases/{cancelar,finalizar}_sesion_en_vivo.py` (ampliados) | Código de backend | `US-ADJ-58` — cancelar/finalizar en cualquier etapa |
| CI-C30 | `src/identidad/interface_adapters/gateways/comision_query_repository.py` (`docente_pertenece_a_comision`/`docente_tiene_comision_en_materia`), `ComisionConsultaPort` ampliado en `banco_preguntas`/`actividad_evaluativa`/`analytics` | Código de backend | `US-ADJ-57` — aislamiento de datos por Docente, 4 BC |
| CI-C31 | `src/analytics/use_cases/obtener_desempeno_estudiante.py` (ampliado), `SesionEnVivoDesempenoConsultaPort` | Código de backend | `US-ADJ-56` — sesiones en vivo en Analytics |
| CI-C32 | `src/identidad/frameworks/api/invitaciones_router.py` (`GET /invitaciones/{token}`) | Código de backend | `US-ADJ-08` — vista previa pública de invitación |
| CI-F19 | `frontend/src/lib/sesiones-en-vivo-api.ts`, `frontend/src/pages/actividad-evaluativa-en-vivo/` (6 pantallas), `frontend/src/layouts/StageLayout.tsx` | Código de frontend | Frontend completo del modo en vivo (Iteración 3) |
| CI-F20 | `frontend/src/pages/cuentas/CuentaDetalle.tsx`, `frontend/src/pages/identidad/InvitacionPreview.tsx` | Código de frontend | `US-ADJ-07`/`US-ADJ-08` — nombre legible de comisión, vista previa de invitación |
| CI-T13 | `quality/reports/designreviewer/BL-011-designreviewer.json`, `quality/reports/architectanalyst/BL-011-arquitectura.json` | Herramienta | Salidas de cierre de esta baseline |

---

## Métricas al cerrar

**Backend:**
- `pytest --cov=src --cov-report=json`: **1799 passed** (unit + integration + BDD), 0 fallos
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (300 archivos)
- `pylint src/`: 9.59/10 (mismo `duplicate-code` preexistente entre `analytics/frameworks/api/schemas` y los use cases de desempeño, sin CRITICAL nuevo)
- Cobertura: 97% (`coverage.json`, 5042/5207 statements — `ArchitectAnalyst.CoverageAnalyzer` reporta 96.7%, dentro del umbral)

**Frontend:**
- `npx vitest run --coverage`: **801 passed** (105 archivos de test), 0 fallos
- `npx oxlint`: 0 errores (7 advertencias preexistentes, sin relación con esta baseline)
- `npx tsc -b`: 0 errores
- Cobertura: 93.5% statements / 85.71% branches / 90.31% functions / 96.31% lines — por
  encima del umbral de 80% del proyecto en las 4 métricas

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: 0 CRITICAL, 330 advertencias (`BL-010`: 215
  sobre 258 archivos; sube por el volumen del modo en vivo — 300 archivos ahora — sin cluster
  nuevo relevante, mismo tipo de hallazgos ya vistos: `LongMethodAnalyzer`/`LawOfDemeterAnalyzer`
  en use cases de sesión en vivo)
- `architectanalyst src/ --sprint-id BL-011`: 7 CRITICAL (`DistanceAnalyzer`, "Zone of Pain"),
  uno por cada paquete raíz de BC — mismo conteo que `BL-010`, mismo falso positivo aceptado
  permanentemente desde `US-ADJ-13`/`19` (`CLAUDE.md` §Quality gates): bug de
  `DependencyGraphBuilder` que deja `Ca=Ce=0` para todo el proyecto — `should_block: false`,
  sin acción. `LayerViolationsAnalyzer` sigue sin detectar ninguna violación bajo ninguna
  configuración probada (mismo bug, `software_limpio#77`).

**Sin migraciones de esquema fuera de** las tablas nuevas del modo en vivo (evento sourcing
sobre la misma tabla `events` — sin tabla propia adicional) y las columnas de aislamiento por
Docente de `US-ADJ-57` (sin backfill destructivo — nuevas primitivas de consulta, no
alteración de datos existentes).

---

## UAT de cierre

Sin UAT formal consolidada de baseline adicional — cada iteración con código de producción
ya corrió la propia, documentada progresivamente en `CLAUDE.md`:
- Iteración 1/2 (backend): revisión manual de Víctor (`tests/uat/inc6/guion_manual_iteracion2.sh`)
  sin hallazgos el 2026-09-21, más la verificación E2E del RNF (`US-6.2.9`,
  `quality/reports/uat/inc6/`).
- Iteración 3 (frontend): UAT en dos tramos — Playwright E2E (10/10 sin inestabilidad) y
  revisión manual de Víctor en Mac/iPhone/iPad con datos reales
  (`quality/reports/uat/inc6/revision-manual-app.md`, 2026-09-26), sin hallazgos 🔴
  Bloqueantes (7 hallazgos 🟡, todos resueltos antes de esta baseline).
- `Incremento 6-ADJ`: sin UAT formal propia — ajustes puntuales sobre funcionalidad ya
  validada (`US-ADJ-56`/`57`/`58`/`08`/`07`), cada uno verificado con su propia suite de
  tests (1799 backend / 801 frontend en verde al cierre, sin regresiones) y el barrido
  documental §12 sin superficie ejecutable que testear.

Mismo criterio que `BL-010` ("cada pieza de producto ya tuvo su propio pase de UAT antes de
llegar a esta baseline, en vez de no requerirlo por no ser observable").

**Ítem abierto, no bloqueante:** checkpoint de staging del RNF en Fly.io con WSS real
(`PROCEDIMIENTO-UAT.md` §4) — sigue pendiente, sin relación con el cierre de esta baseline.

---

## Actualización de la matriz de trazabilidad

`RF-08`, `RF-09` y `RF-10` pasan de **Implementado** a **Validado**, referenciando esta
baseline (`BL-011`) como evidencia — `docs/traceability/matrix.md` actualizado en el mismo
commit que este archivo.

---

## Retrospectiva

**Qué funcionó:**
- El spike de puntaje resuelto antes del event storming (Iteración 0) evitó que una decisión
  de producto (fórmula de puntaje) contaminara el modelado del dominio a mitad de camino —
  mismo patrón preventivo que otros ítems abiertos resueltos antes de empezar (ej. criterios
  de legibilidad de RNF_v1.md, resueltos en la misma Iteración 0).
- Separar Iteración 1/2 (backend) de Iteración 3 (frontend) permitió verificar el RNF de
  rendimiento (`US-6.2.9`, 60 participantes simultáneos) sin la variable de UI de por medio —
  el `p95` medido es del use case puro, no contaminado por latencia de render.
- La decisión de UAT en un solo pase consolidado (no US por US, ya adoptada desde `BL-010`)
  se sostuvo también en la Iteración 3 — los 7 hallazgos de la revisión manual fueron
  justamente del tipo que un pase consolidado en dispositivo real detecta mejor (reconexión
  "zombi" de iOS, contraste en pantalla real vs. prototipo).
- Insertar `Incremento 6-ADJ` **antes** de cerrar la baseline (en vez de después, como
  hubiera sido el default) evitó que `US-ADJ-56`/`57`/`58` quedaran como deuda que arrastrar
  al Incremento 7 — mismo aprendizaje ya capitalizado en `Incremento 3-ADJ`/`4-ADJ`/`5-ADJ`.

**Qué fue más difícil de lo esperado:**
- El barrido documental §12 encontró más deriva de la esperada en
  `docs/architecture/03-bounded-contexts.md` (congelado desde el Incremento 1) y tres Issues
  de GitHub con trabajo mergeado sin cerrar — el paso 7 del ciclo por US (cerrar el Issue al
  mergear el PR) no es a prueba de fallos cuando varias US se resuelven en la misma sesión
  sin pausar entre cada una.

**Qué ajustar en el próximo incremento:**
- Agregar una verificación automática (o un paso explícito de checklist) que liste los
  Issues abiertos de un Milestone antes de dar por cerrada una iteración, en vez de confiar
  en que el paso 7 del workflow se ejecutó para cada US — el barrido documental de cierre de
  baseline es una red de seguridad tardía, no debería ser la primera vez que se detecta.
- El "Zone of Pain" de `ArchitectAnalyst` sigue en 7 críticos sin cambios — sin novedad
  respecto de `BL-010`, la nota de `US-ADJ-19` sigue siendo la referencia correcta mientras
  no se resuelva `software_limpio#77` upstream.

---

## Próximo paso

Retomar el backlog sin incremento asignado (`RF-07`, importación desde PDF — decidido para
Incremento 7 en `PLAN_v1.md`) o evaluar si corresponde abrir el Incremento 7 (Cierre de
Alcance v1) directamente. Ítem abierto aparte: checkpoint de staging del RNF en Fly.io con
WSS real (`PROCEDIMIENTO-UAT.md` §4), y la decisión institucional de infraestructura de
producción pendiente desde `CLAUDE.md` §"Ítems abiertos que requieren decisión".
