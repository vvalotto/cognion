# BL-006 — Portal del Estudiante y Analytics (Incremento 4)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento |
| Fecha apertura | 2026-09-04 |
| Fecha cierre | 2026-09-06 |
| Git tag inicial | — (continúa desde `v0.5.0`, `BL-004`; `BL-005` no había llegado a taguearse en `main`) |
| Git tag cierre | `v0.6.0` (MINOR — cierre de Incremento de `PLAN_v1.md`), tagueado en `main` el 2026-09-06 en el mismo merge `develop → main` que `v0.5.1` (`BL-005`) — decisión de Víctor: mergear ambas juntas en vez de diferir de nuevo |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | Docente y estudiante tienen visibilidad de desempeño histórico basado en evaluaciones reales ya corridas en el Incremento 3 (`PLAN_v1.md`, Hito Incremento 4). Backend y frontend implementados e integrados juntos por iteración — mismo criterio de cierre que `BL-002`/`BL-003` (`docs/plans/PLAN-CM.md` §7), sin diferir el frontend a otra iteración. |

---

## Descripción

Cierra el Incremento 4 de `PLAN_v1.md`: primer Bounded Context puramente de lectura del
sistema (`ARQ_v1.md`, Analytics = Supporting Subdomain). Sin comando ni evento propio — se
proyecta por consulta directa sobre el event store de Actividad Evaluativa ya existente
(`ADR-002`), sin persistencia propia de escritura. Cubre RF-15, RF-16 y RF-17. Incluye:

- **Iteración 0 — Modelado** (`US-4.0.1`, `US-4.0.2`): diseño de read models
  (`BC-analytics-modelo.md`) y wireframes/prototipo (`wireframes-analytics.md`) del portal de
  desempeño.
- **Iteración 1 — RF-15** (`US-4.1.1` a `US-4.1.3`, backend + frontend juntos): infraestructura
  de consulta (`EvaluacionDesempenoConsultaPort`, adapter in-process, composition root propio),
  Estudiante consulta su propio desempeño (resumen acumulado + detalle por evaluación,
  agregados en memoria sin proyección materializada — mismo criterio que `US-3.2.4`), pantalla
  "Mi desempeño".
- **Iteración 2 — RF-16, RF-17** (`US-4.2.1` a `US-4.2.6`, backend + frontend juntos): Docente
  consulta el desempeño de un estudiante elegido (reutiliza el Use Case de la Iteración 1 sin
  cambios), `ComisionConsultaPort` (query nueva de punta a punta en Identidad —
  `listar_comisiones_por_materia`/`listar_estudiantes`), `PreguntaMetadatoConsultaPort`
  (adapter in-process hacia Banco de Preguntas, reusa `MetadatosPregunta` de `US-ADJ-17`),
  tasa de error por unidad/tema agregada o por comisión, pantallas "Desempeño por alumno"
  (reutiliza el componente visual `DesempenoResumenDetalle` extraído de "Mi desempeño") y
  "Desempeño por tema" (forma propia, severidad por color).

Sin ninguna migración de base de datos nueva — Analytics no persiste nada propio, y las
consultas nuevas de Identidad (`Comisión` por materia/estudiantes) reutilizan tablas ya
existentes desde el Incremento 1.

Dos problemas reales detectados y corregidos durante la preparación de la UAT de la Iteración
1, ninguno parte del alcance formal de `US-4.1.x` (detalle completo en `CLAUDE.md`):
- 🔴 Los 5 formularios de submit sin `useEffect` propio introducidos por `US-ADJ-19`/`20` (BC
  Identidad/Banco de Preguntas) no funcionaban en modo dev — `AbortController` creado en el
  render, abortado por el doble montaje de `StrictMode` antes de cualquier submit real. Fix
  directo sobre código ya en `develop`, sin US-ADJ (track informal).
- 🟡 `tests/uat/inc3/limpiar_uat.sh` y `tests/uat/inc4/limpiar_uat.sh` dejaban huérfanos
  eventos de una `Evaluacion` al limpiar corridas anteriores (`DELETE` fila a fila en vez de
  por stream completo). Corregido en ambos scripts — tooling de test, no código de producción.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D38 | `docs/design/domain/BC-analytics-modelo.md`, `docs/design/ux/wireframes-analytics.md` + prototipo (`analytics-portal-desempeno.html`) | Documento | Read models y wireframes/prototipo del portal de desempeño (`US-4.0.1`, `US-4.0.2`) |
| CI-D39 | `docs/specs/inc4/US-4.0.*` a `US-4.2.6.md`, `docs/plans/inc4/US-4.*-context.md`/`-plan.md`, `docs/plans/inc4/inc4-candidatas.md` | Documento | Specs, contexto y plan de las 9 US-IEDD de las Iteraciones 1 y 2 |
| CI-D40 | `docs/reports/inc4/US-4.1.1-report.md` a `US-4.2.6-report.md` | Documento | Reportes de cierre de las 9 US-IEDD |
| CI-D41 | `quality/reports/uat/inc4/design.md`/`evidencia.md`, `design-iteracion2.md`/`evidencia-iteracion2.md`, `guion-manual-iteracion1.md`, `tests/uat/inc4/guion_manual_iteracion2.sh` | Documento | Diseño y evidencia de UAT de cierre de Iteración 1 e Iteración 2 |
| CI-C17 | `src/analytics/` (BC completo) | Código de backend | Entities/ports, use cases (`ObtenerDesempenoEstudianteUseCase`, `ObtenerTasaErrorPorTemaUseCase`), adapters in-process, controller y router — BC de solo lectura, sin persistencia propia |
| CI-C18 | `src/identidad/entities/ports/comision_query_port.py`, `interface_adapters/gateways/comision_query_repository.py`, `interface_adapters/controllers/comisiones_query_controller.py`, `frameworks/api/{comisiones_router,materias_comisiones_router}.py` | Código de backend | `ComisionConsultaPort` — query nueva de punta a punta en Identidad (`US-4.2.2`), reutilizada como adapter in-process por Analytics |
| CI-F12 | `frontend/src/lib/analytics-api.ts`, `frontend/src/pages/analytics/{MiDesempeno,DesempenoPorAlumno,DesempenoPorTema,DesempenoResumenDetalle}.tsx` | Código de frontend | UI completa de Analytics — vista Estudiante y vista Docente (`US-4.1.3`, `US-4.2.5`, `US-4.2.6`) |
| CI-T07 | `quality/reports/architectanalyst/BL-006-arquitectura.json`, `quality/reports/designreviewer/BL-006-designreviewer.txt` | Herramienta | Salidas de cierre de baseline (`ArchitectAnalyst`/`DesignReviewer` consolidados) |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 852 passed (incluye el test previamente flaky de la Iteración 3 del
  Incremento 3, `test_rechazo_fuera_del_período_vigente` — en verde en esta corrida, sin
  cambios de código; el chip de seguimiento `task_471c8a04` sigue abierto por si reaparece)
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (213 archivos)
- `pylint src/`: 9.59/10 (sin cambios respecto de `BL-005`)
- Cobertura (`pytest --cov=src`): 98.99% (2673 statements, 27 sin cubrir)

**Frontend:**
- `vitest run --coverage --no-file-parallelism`: 261/261 tests, 46 archivos
- Cobertura: 91.34% statements / 80.47% branches (por encima del umbral de 80%, sostenido
  desde `US-ADJ-16`) / 86.61% functions / 93.47% lines
- `oxlint`: 0 errores, 5 warnings preexistentes (`only-export-components` en componentes
  shadcn/ui y en `DesempenoResumenDetalle.tsx` nuevo, mismo patrón ya aceptado; 1 warning de
  test preexistente)
- `tsc -b`: 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml` (consolidado, estado final del incremento): 0
  CRITICAL, 131 advertencias (antes, `BL-005`: 118 — suba esperada por el código nuevo de
  Analytics/Identidad, sin cluster nuevo relevante), 95.4h de deuda técnica estimada (0h
  bloqueante)
- `architectanalyst src/ --sprint-id BL-006`: 6 críticos (mismo "Zone of Pain" ya documentado
  y aceptado — `identidad`, `settings`, `shared`, `banco_preguntas`, `actividad_evaluativa` —
  más `analytics`, nuevo este incremento, mismo patrón de módulo raíz de BC con `Ca=Ce=0`), 10
  warnings, 133 infos, `should_block: false`
  (`.cm/baselines/BL-006-arquitectura.json`, copia de
  `quality/reports/architectanalyst/BL-006-arquitectura.json`)

**UAT (`PROCEDIMIENTO-UAT.md`):**
- Iteración 1 (RF-15, backend + frontend): `quality/reports/uat/inc4/design.md`/`evidencia.md`
  — Capa 1 (775 pytest + 242 Vitest) y Capa 2 (`smoke.sh`) aprobadas; recorrido con Víctor
  mirando el navegador en vivo, sin hallazgos nuevos
- Iteración 2 (RF-16/RF-17, backend + frontend): `design-iteracion2.md`/`evidencia-iteracion2.md`
  — Capa 1 (851/852 pytest, único fallo preexistente ajeno a esta iteración; 261/261 Vitest) y
  Capa 2 (`smoke.sh` extendido) aprobadas; recorrido en navegador real con datos sembrados a
  propósito, confirmado por Víctor sin hallazgos
- RF-15, RF-16, RF-17 pasan de Implementado a **Validado** en `docs/traceability/matrix.md`,
  referenciando esta baseline

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Merge `develop → main` con `BL-005` + `BL-006` juntas, no diferido de nuevo | `BL-005` (Incremento 3-ADJ) había cerrado en `develop` sin mergearse a `main` — mismo ítem abierto de infraestructura/Docker desde `BL-001`. A diferencia de las 5 baselines anteriores, esta vez Víctor decidió no seguir acumulando: un único merge `develop → main`, dos tags sobre los commits reales de cierre de cada una (`v0.5.1` para `BL-005`, PATCH por ser incremento técnico fuera de `PLAN_v1.md`; `v0.6.0` para `BL-006`, MINOR por ser Incremento de `PLAN_v1.md`). El build de imagen Docker corre en ambos tags (`cd.yml`); el `flyctl deploy`/healthcheck siguen comentados — sin impacto de infraestructura real. |
| Sin frontend diferido a otra iteración, a diferencia de Actividad Evaluativa | Mismo criterio que Banco de Preguntas — cada iteración cierra su propio RF de punta a punta porque no hay un modelo de dominio nuevo que estabilizar entre iteraciones (Analytics no tiene aggregate ni evento propio). |
| `US-4.2.1` sin restricción de pertenencia a comisión | Hot spot de autorización resuelto con Víctor en la Iteración 0: cualquier docente autenticado puede consultar el desempeño de cualquier estudiante — RBAC estándar, sin invariante adicional. |
| Selector de materia de "Mi desempeño" no ejercitable con una cuenta real | El dominio actual liga un Estudiante a una única comisión/materia — limitación detectada en la Iteración 1, no bloquea el DoD (el wireframe ya contemplaba "sin selector si cursa una sola materia"), pendiente si se decide modelar multi-inscripción. |
| Fix de `AbortController`/`StrictMode` y de los scripts de limpieza de UAT sin US-ADJ | Ambos detectados en la preparación de la UAT de Iteración 1, ninguno en el alcance de `US-4.1.x` — el primero toca `src/`/`frontend/` pero es un bug preexistente de `US-ADJ-20` (`BL-005`), no un hallazgo nuevo de este incremento; el segundo es tooling de test. Resueltos directo sobre `develop`, mismo criterio que otros fixes de sesión ya documentados. |

---

## Retrospectiva

### ¿Qué funcionó?

- Diseñar los read models antes de escribir código (`US-4.0.1`) evitó cualquier revisión de
  contrato tardía — a diferencia de incrementos anteriores, acá no hubo ningún gap de spec
  detectado en Fase 2 ni ajuste de diseño a mitad de implementación en ninguna de las 9 US.
- Reutilizar el Use Case de la Iteración 1 sin cambios para `US-4.2.1` (Docente consulta el
  desempeño de un estudiante elegido) confirmó que separar "de quién es el `estudiante_id`"
  (parámetro) de "qué hace la consulta" (Use Case) paga dividendos reales — ninguna lógica de
  agregación se duplicó entre las dos vistas.
- Extraer `DesempenoResumenDetalle.tsx` de `MiDesempeno.tsx` para reutilizar el mismo
  componente visual entre estudiante y docente (`US-4.2.5`) mantuvo consistencia de UI sin
  esfuerzo adicional — mismo patrón de "un componente, dos consumidores" que ya había
  funcionado en Identidad.
- El patrón "command/query separados desde el diseño" (`ComisionQueryPort` distinto de
  `ComisionRepositoryPort`, `US-4.2.2`) evitó repetir el CRITICAL de CBO que apareció varias
  veces en Incremento 2 al forzar una query nueva sobre un puerto de escritura existente.

### ¿Qué fue más difícil de lo esperado?

- El bug de `AbortController`/`StrictMode` (afecta 5 pantallas de dos BCs distintos) solo se
  hizo visible al probar el flujo completo en modo dev antes de la UAT — ni Vitest ni el modo
  build lo detectan, porque el mock de `fetch` no interpreta `AbortSignal` y `npm run build`
  no monta dos veces. Tercer episodio consecutivo del patrón "UAT en navegador real detecta lo
  que Vitest mockeado no ve" (`[[feedback_uat_navegador_real]]`), esta vez con `npm run dev`
  como el entorno que expone el gap, no el navegador de producción.
- El "Zone of Pain" de `ArchitectAnalyst` suma un sexto módulo crítico (`analytics`) — mismo
  falso positivo aceptado, pero la lista sigue creciendo con cada BC nuevo sin que el bug
  upstream (`software_limpio#77`) tenga ETA.
- `BL-005` sin mergear a `main` antes de abrir esta baseline deja acumulándose una segunda
  baseline pendiente de tag — la decisión de infraestructura/Docker ya lleva 6 baselines sin
  resolverse (`BL-001` a `BL-006`).

### ¿Qué ajustar en el próximo incremento?

- Resuelto en el cierre de esta misma baseline: Víctor confirmó mergear `BL-005` + `BL-006`
  juntas en vez de seguir difiriendo — evitar que se repita el patrón implica decidir el merge
  a `main` en el momento de cada cierre, no dejarlo como "ítem abierto" recurrente.
- Evaluar si el bug de `AbortController`/`StrictMode` amerita una US-ADJ formal en el próximo
  incremento técnico (mismo criterio que `US-ADJ-13`/`19`: un fix de sesión sin spec deja el
  hallazgo sin trazabilidad si se pierde el hilo de `CLAUDE.md`).
- Si se decide modelar multi-inscripción de un Estudiante a más de una comisión/materia más
  adelante, revisar el selector de materia de "Mi desempeño" — hoy no puede ejercitarse con una
  cuenta real.

---

*Creado: 2026-09-06*
