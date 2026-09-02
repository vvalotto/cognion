# BL-004 — Actividad Evaluativa, período abierto (Incremento 3)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento |
| Fecha apertura | 2026-08-24 |
| Fecha cierre | 2026-09-02 |
| Git tag inicial | — (continúa desde `v0.4.0`, `BL-003`) |
| Git tag cierre | `v0.5.0`, taggeado el 2026-09-02 al mergear `develop → main` (a pedido explícito de Víctor — a diferencia de `BL-001`/`BL-002`/`BL-003`, esta vez se resolvió el merge en el mismo cierre, no diferido) |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | Un estudiante completa una evaluación de período abierto de principio a fin (incluida una desconexión simulada, sin pérdida de respuestas), y el docente extiende el plazo de una actividad activa o la cierra manualmente (`PLAN_v1.md`, Hito Incremento 3). Backend y frontend implementados e integrados juntos — mismo criterio de cierre de baseline que `BL-002`/`BL-003` (`docs/plans/PLAN-CM.md` §7). |

---

## Descripción

Cierra el Incremento 3 de `PLAN_v1.md`: primer Core Domain del sistema (`ARQ_v1.md`, driver 3)
y primer BC con Event Sourcing + CQRS (`ADR-002`), renombrado de "Sesiones" a "Actividad
Evaluativa" (`ADR-015`). Cubre RF-11, RF-11b, RF-12 y RF-13 — modo período abierto completo,
backend + frontend. Incluye:

- **Iteración 0 — Modelado** (`US-3.0.1`, `US-3.0.2`): event storming
  (`BC-actividad-evaluativa-modelo.md`) y wireframes/prototipo
  (`wireframes-actividad-evaluativa.md`) del flujo de período abierto.
- **Iteración 1 — Creación y set aleatorio** (`US-3.1.1` a `US-3.1.3`, backend): infraestructura
  de Event Sourcing (tabla `events` JSONB, Unit of Work por Use Case), creación de actividad de
  período abierto, inicio de evaluación con set aleatorio fijado desde el inicio (reconexión
  idempotente).
- **Iteración 2 — Confiabilidad** (`US-3.2.1` a `US-3.2.4`, backend): confirmación atómica de
  respuestas, suspender/reanudar, finalizar y revisión, `VerificadorDeVencimientos` (suspensión
  y finalización automáticas por inactividad o vencimiento de período).
- **Iteración 3 — Modificación de período** (`US-3.3.1`, `US-3.3.2`, backend): extender (o
  intentar acortar) el plazo de una actividad vigente, cierre manual anticipado con cascada de
  finalización de evaluaciones activas.
- **Iteración 4 — Frontend** (`US-3.4.1` a `US-3.4.10`/`US-ADJ-09`/`10`/`11`, backend + frontend
  integrados): consume las 3 iteraciones de backend de una sola vez. Lado Docente (materias,
  actividades, detalle, extender plazo, cerrar, editar título) y lado Estudiante (materias y
  actividades disponibles, rendir con pausa/reanudación, finalizar y revisión completa).
- **`US-ADJ-12`** (ajuste inmediato, post-UAT): `RendirEvaluacion.tsx` prellena la respuesta
  confirmada y navega sin reintentar registrar sobre una pregunta ya respondida — detectado en
  la revisión manual de Víctor, corregido en la misma sesión sin abrir una iteración de ajuste
  aparte (a diferencia de `SP-ADJ-01` en `BL-003`, el hallazgo era único y acotado).

Tres hallazgos de UAT en navegador real resueltos en la misma sesión antes de mergear
(`US-ADJ-09`, bug de timezone naive/aware en `datetime-local`; `US-ADJ-10`, edición de título de
actividad; y un gap de UX de frontend-only, botón "Volver" en el detalle) — ver
`CLAUDE.md` para el detalle completo de cada uno.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D29 | `ADR-015-renombrar-bc-sesiones-actividad-evaluativa.md` | Documento | Decisión de renombrar el BC "Sesiones" a "Actividad Evaluativa" antes de escribir código |
| CI-D30 | `docs/design/domain/BC-actividad-evaluativa-modelo.md` (+ diagramas HTML) | Documento | Event storming del BC (`US-3.0.1`), incluye el modelo de Event Sourcing y las reglas del `VerificadorDeVencimientos` (§6b) |
| CI-D31 | `docs/design/ux/wireframes-actividad-evaluativa.md` + prototipo | Documento | Wireframes y prototipo navegable del flujo de período abierto (`US-3.0.2`), gate UX de la Iteración 4 |
| CI-D32 | `docs/specs/inc3/US-3.0.*` a `US-3.4.7.md`, `docs/specs/ajustes/US-ADJ-09/10/11/12.md`, `docs/plans/inc3/inc3-candidatas.md` | Documento | Specs de las 16 US-IEDD del Incremento 3 (Iteraciones 0 a 4) y de los 4 ajustes post-UAT |
| CI-D33 | `quality/reports/uat/inc3/design.md`/`evidencia.md`, `design-iter4.md`/`evidencia-iter4.md`, `guion-manual-iteracion4.md`, `hallazgos-revision-manual.md` | Documento | Diseño y evidencia de UAT de cierre de Iteración 1 (backend) e Iteración 4 (backend+frontend completo), incluida la revisión manual de Víctor |
| CI-D34 | `docs/aprendizajes/HITO-7-VALIDACIONES-INTERSECCION-Y-CONCURRENCIA-EN-UAT-ITER4.md` | Documento | Hallazgos del ensayo IEDD sobre la carrera de concurrencia real y la intersección de invariantes detectadas en la UAT de Iteración 4 |
| CI-C13 | `src/actividad_evaluativa/` (BC completo) | Código de backend | Entities/use_cases/interface_adapters/frameworks — `Evaluacion`, `ActividadEvaluativaPeriodoAbierto`, Event Sourcing + CQRS (`US-3.1.1` a `US-3.3.2`), `VerificadorDeVencimientos` |
| CI-C14 | `src/identidad/use_cases/listar_materias_del_estudiante.py`, endpoint asociado | Código de backend | Endpoint de materias visibles para el Estudiante (`US-3.4.5`), único cambio a `identidad` en este incremento |
| CI-C15 | `migrations/versions/9244e3956c69_actividad_evaluativa_event_store.py` | Código de backend | Tabla `events` (JSONB append-only), única migración del Incremento 3 |
| CI-F10 | `frontend/src/lib/actividad-evaluativa-api.ts`, `pages/{Materias,Mis}Actividades.tsx`, `ActividadDetalle*.tsx`, `Nueva/Editar/Extender/Cerrar*.tsx`, `RendirEvaluacion.tsx`, `EvaluacionSuspendida.tsx`, `FueraDePeriodo.tsx`, `RevisionEvaluacion.tsx` | Código de frontend | UI completa de Actividad Evaluativa — lado Docente y lado Estudiante (`US-3.4.1` a `US-3.4.10`, `US-ADJ-12`) |
| CI-T05 (ext.) | `.claude/skills/run-cognion/smoke.sh`, `tests/uat/inc3/guion_manual_iteracion1.sh`/`guion_manual_iteracion4.sh` | Herramienta | `smoke.sh` extendido con el flujo completo de Actividad Evaluativa; 2 guiones de revisión manual nuevos (Iteración 1 vía Swagger, Iteración 4 vía navegador real) |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 739 passed
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (189 archivos)
- `pylint src/`: 9.50/10
- Cobertura (`pytest --cov=src`): 99% (2407 statements, 27 sin cubrir)

**Frontend:**
- `vitest run --no-file-parallelism`: 229/229 tests, 41 archivos
- Cobertura: 90.8% statements / 77.89% branches / 91.43% functions / 93.14% lines — **branches
  por debajo del umbral configurado (80%)**, ver retro
- `oxlint`: 0 errores, warnings preexistentes (`only-export-components`, patrón shadcn/ui;
  `no-unsafe-optional-chaining` en un test — ninguno introducido en este incremento)
- `tsc --noEmit` (`tsc -b`): 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml` (consolidado, estado final del incremento): 0
  CRITICAL, 159 advertencias, 130.0h de deuda técnica estimada (0h bloqueante)
- `architectanalyst src/ --sprint-id BL-004`: 5 críticos (Zone of Pain: `identidad`, `settings`,
  `shared`, `banco_preguntas` — mismos de `BL-002`/`BL-003` — más `actividad_evaluativa`, nuevo
  este incremento), 8 warnings, `should_block: false`
  (`.cm/baselines/BL-004-arquitectura.json`, copia de
  `quality/reports/architectanalyst/BL-004-arquitectura.json`)

**UAT (`PROCEDIMIENTO-UAT.md`):**
- Iteración 1 (backend, vía Swagger/HTTP): `quality/reports/uat/inc3/design.md`/`evidencia.md`
  — Capa 1 + Capa 2 aprobadas, revisión manual de Víctor sin hallazgos de ninguna severidad
- Iteración 4 (backend + frontend, navegador real): `design-iter4.md`/`evidencia-iter4.md` —
  Capa 1 + Capa 2 aprobadas; 2 hallazgos 🔴 Bloqueantes de la propia sesión resueltos antes de
  mergear (`US-ADJ-11`); revisión manual de Víctor (`guion-manual-iteracion4.md`) con 1
  hallazgo 🔴 Bloqueante (`US-ADJ-12`, prellenado/navegación en `RendirEvaluacion`), corregido
  y verificado en la misma sesión — sin hallazgos abiertos al cierre
- RF-11, RF-11b, RF-12, RF-13 pasan de Especificado a **Validado** en
  `docs/traceability/matrix.md`; RNF-DISP-2, RNF-CONF-1, RNF-OBS-1 pasan a **Validado**

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Merge `develop → main` y tag diferidos otra vez | Mismo ítem abierto que `BL-001`/`BL-002`/`BL-003`: no hay Docker en el entorno de desarrollo local. A confirmar con Víctor al cerrar esta baseline. |
| Frontend diferido a una sola Iteración 4, no repartido en las Iteraciones 1 a 3 | Decisión de `PLAN_v1.md` para este incremento — a diferencia de Banco de Preguntas/Cuentas (backend+frontend por iteración), Actividad Evaluativa consume las 3 iteraciones de backend de una sola vez en la Iteración 4, dado que Event Sourcing + CQRS requería estabilizar el modelo de dominio completo antes de exponer UI. |
| `US-ADJ-12` resuelto sin abrir una iteración de ajuste (`SP-ADJ`) | A diferencia de `SP-ADJ-01` en `BL-003` (3 no conformidades agrupadas), acá fue un único hallazgo acotado — mismo criterio que `US-ADJ-09`/`10`/`11`: track formal (toca `src/`), resuelto en la misma sesión de UAT. |
| ArchitectAnalyst — 5to crítico "Zone of Pain" (`actividad_evaluativa`) | Mismo falso positivo de granularidad de paquete raíz que `identidad`/`banco_preguntas`/`shared`/`settings` en `BL-002`/`BL-003`. Esta vez sí se tomó una decisión concreta (no solo diferir de nuevo): el próximo incremento técnico recalibra el análisis a nivel de subpaquete (`entities/`, `use_cases/`, etc.), en vez de seguir aceptando el falso positivo sin acción. |
| `CoverageAnalyzer` sigue sin encontrar `coverage.json` | Se generó `coverage.json` en la raíz del repo antes de correr `architectanalyst`, pero el warning persistió — la herramienta probablemente espera la ruta relativa a `src/`, no a la raíz. No se investigó a fondo; queda agrupado en el mismo incremento técnico que el ajuste de umbrales. |
| Cobertura de branches del frontend por debajo del umbral (77.89% < 80%) | Detectado recién al correr la suite completa con `--coverage` para esta baseline — no bloqueó ningún PR individual porque el gate de Fase 7 corre por archivo tocado, no la cobertura global del proyecto. Queda como ítem de retro, no bloqueante para el cierre (ninguna US individual incumplió su propio umbral). |

---

## Retrospectiva

### ¿Qué funcionó?

- Diferir todo el frontend a una única Iteración 4 (en vez de repartirlo iteración por
  iteración como en Banco de Preguntas/Cuentas) permitió estabilizar el modelo de Event
  Sourcing + CQRS completo antes de exponer UI — ninguna pantalla tuvo que rehacerse por un
  cambio de contrato de dominio tardío.
- El mecanismo de reutilizar `FinalizarEvaluacionUseCase`/`SuspenderEvaluacionUseCase` con
  `actor="sistema"` (`US-3.2.4`) evitó duplicar lógica de negocio para el
  `VerificadorDeVencimientos` y para el cierre manual en cascada (`US-3.3.2`) — cero
  invariantes nuevas, cero comandos/eventos nuevos para esas dos funcionalidades.
- La revisión manual de Víctor en navegador real (Iteración 4) volvió a encontrar lo que
  Vitest mockeado no ve — esta vez un bug de navegación real en `RendirEvaluacion.tsx`
  (`US-ADJ-12`) invisible a cualquier test unitario porque requiere el flujo completo
  responder→avanzar→volver→reintentar.

### ¿Qué fue más difícil de lo esperado?

- El ajuste de umbrales de `ArchitectAnalyst` sigue sin aplicarse — tercera baseline
  consecutiva (`BL-002`, `BL-003`, ahora `BL-004`) señalando el mismo falso positivo de
  granularidad, esta vez con un 5to módulo (`actividad_evaluativa`). A diferencia de las dos
  veces anteriores, esta vez sí se tomó la decisión de resolverlo en el próximo incremento
  técnico en vez de seguir difiriéndolo sin fecha.
- La cobertura de branches del frontend (77.89%) quedó por debajo del umbral configurado
  (80%) al medirla de punta a punta — ninguna US individual lo detectó porque el gate mide por
  archivo tocado, no de forma global. Falta decidir si vale la pena escribir tests de branches
  adicionales o ajustar el umbral global.
- El merge a `main`/tag de baseline sigue diferido por cuarta vez consecutiva (`BL-001` a
  `BL-004`) — la decisión de infraestructura/Docker lleva más de mes y medio sin resolverse.

### ¿Qué ajustar en el próximo incremento?

- Ejecutar el incremento técnico ya decidido: recalibrar `ArchitectAnalyst` a nivel de
  subpaquete (o documentar el falso positivo como aceptado permanente), arreglar la detección
  de `coverage.json` por `CoverageAnalyzer`, y reordenar `frontend/src/pages/` por BC — un solo
  PR de housekeeping, sin US funcional.
- Decidir qué hacer con la cobertura de branches del frontend (77.89% vs. umbral 80%): subir
  la cobertura real o ajustar el umbral configurado con criterio explícito, no dejarlo como
  una discrepancia silenciosa.
- Resolver la decisión de infraestructura/Docker — cada baseline que se acumula sin ella hace
  más costoso el eventual `merge → main` con 4 tags pendientes de una sola vez.

---

*Creado: 2026-09-02*
