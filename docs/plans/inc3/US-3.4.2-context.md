# Contexto de Ejecución — US-3.4.2

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc3/US-3.4.2.md` (Issue #171)
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first, backend); React 19 +
  TypeScript + Vite (frontend). UX: `docs/design/ux/wireframes-actividad-evaluativa.md` §2.0
  (`#doc-materias`), §2.1 (`#doc-actividades`); prototipo
  `docs/design/ux/prototipos/actividad-evaluativa-periodo-abierto.html`.

## Historia de Usuario
- **ID:** US-3.4.2
- **Título:** Docente ve sus materias y el listado de actividades de una materia
- **Tipo:** Nueva funcionalidad (backend + frontend)
- **Puntos:** 5
- **Prioridad:** Alta — primera pantalla real de la Iteración 4, bloquea `US-3.4.3`/`US-3.4.4`.

## Gap 1 — campo `titulo` (resuelto con Víctor, 2026-08-30)

El prototipo HTML (`#doc-actividades`, autoridad sobre el texto de la spec — mismo criterio que
`feedback_prototipo_html_autoridad`) muestra un título de texto libre por actividad
(`"Parcial 1 — Unidades 1 a 3"`), y el wireframe lo confirma ("Tarjetas: título, ventana...").
Pero `ActividadEvaluativaPeriodoAbierto` (`US-3.1.2`) **no tiene ningún campo `titulo`** —
verificado en la entidad, el evento `ActividadEvaluativaCreada` y `CrearActividadPeriodoAbiertoUseCase`.
Consultado con Víctor: **se agrega `titulo` al dominio.**

**Decisión de implementación para minimizar blast radius:** `titulo: str = ""` **opcional**
(no obligatorio), en vez de campo requerido. 25+ archivos de tests de las Iteraciones 1-3
(`US-3.1.2` a `US-3.3.2`) crean actividades sin `titulo` — hacerlo requerido rompería todos esos
fixtures por un cambio fuera del alcance real de esta US. Con default `""`:
- `ActividadEvaluativaPeriodoAbierto.crear()` y `.reconstruir()` sin romper llamadas existentes
  (todas posicionales, `titulo` va al final)
- `CrearActividadRequest.titulo: str = ""` — los bodies JSON existentes en tests de integración
  (sin `titulo`) siguen siendo válidos
- El formulario de alta (`US-3.4.3`, todavía no implementado) es quien realmente le da un valor
  al usuario — hasta entonces, cualquier actividad creada por endpoints/tests existentes tiene
  `titulo=""`
- El frontend de esta US (`Actividades.tsx`) muestra un fallback (`"Actividad del {fecha
  apertura formateada}"`) cuando `titulo` está vacío, para no renderizar una tarjeta sin texto

## Gap 2 — conteo de evaluaciones activas/finalizadas por actividad

La spec de la US solo menciona reutilizar `EvaluacionActivaQueryPort.listar_no_finalizadas()`
(`US-3.2.4`) para el conteo de activas. Pero el wireframe/prototipo también pide el conteo de
**finalizadas** para actividades `Cerrada` (`"41 evaluaciones finalizadas"`) — ese puerto no lo
expone (por diseño, solo lista no-finalizadas). Decisión de implementación (sin ensanchar
`EvaluacionActivaQueryPort`, mismo criterio de la spec): el nuevo `ActividadQueryPort` calcula
ambos conteos con su propia consulta sobre `events` (mismo patrón "agrupar en memoria" de
`SQLAlchemyEvaluacionActivaQueryRepository`, `US-3.2.4`), sin tocar el puerto existente.

## Gap 3 — "Comisión" y conteo en `#doc-materias` (simplificación de UI)

El wireframe/prototipo de `#doc-materias` muestra "Comisión A" y "N actividades en curso" por
tarjeta de materia. `GET /materias` (`US-2.1.9`, `MateriaListItemResponse`) no expone comisión
(ese dato vive en el BC Identidad, sin puerto hacia Actividad Evaluativa) ni conteo de
actividades. Agregar cualquiera de los dos ensancha el alcance de esta US más allá de lo
necesario para desbloquear `US-3.4.3`/`US-3.4.4`. Simplificación: la tarjeta de materia solo
muestra el nombre — mismo dato mínimo que ya usa `Materias.tsx` de Banco de Preguntas. No
requiere aprobación de Víctor por ser puramente cosmético (sin impacto de dominio ni de RF).

## Adaptación de fases del skill

| Fase del skill | Backend | Frontend |
|---|---|---|
| 4/5 — Tests | pytest (unit + integration), fixtures en `conftest.py` de `tests/unit/inc3`/`tests/integration/inc3` | Vitest + React Testing Library |
| 6 — BDD | pytest-bdd, `tests/step_defs/inc3/test_us_3_4_2_steps.py` | Verificado contra Vitest existentes, sin step_defs propios (mismo criterio que `US-3.4.1`) |
| 7 — Quality Gates | pylint/CC/MI/coverage (perfil `clean-architecture-bc`) | oxlint, `tsc --noEmit`, cobertura ≥80% referencia |

## Decisiones de Ejecución
- **BDD:** Sí — 3 escenarios ya definidos en la spec (ver materias, ver actividades de una
  materia, materia sin actividades).
- **skip_bdd:** false
- **Fases a ejecutar:** 0 a 9, backend con pytest-bdd real (primera vez en esta US que se
  ejecuta backend+frontend juntos desde `implement-us` en el Incremento 3 — Iteraciones 1-3
  fueron backend puro).

## Perfil Activo
- **Perfil:** `clean-architecture-bc` para backend; adaptación documental para frontend (mismo
  criterio que `US-3.4.1`/`US-2.1.9`).
- **Umbrales de calidad backend (config.json, perfil activo):** pylint ≥ 8.0, CC ≤ 10 por
  función, MI ≥ 20, coverage ≥ 95%.
- **Umbrales de calidad frontend:** oxlint 0 errores, `tsc --noEmit` 0 errores, cobertura ≥80%
  referencia.

## Rutas de Artefactos
- Contexto: `docs/plans/inc3/US-3.4.2-context.md`
- BDD feature: `tests/features/inc3/US-3.4.2-listado-materias-actividades-docente.feature`
- Plan: `docs/plans/inc3/US-3.4.2-plan.md`
- Reporte: `docs/reports/inc3/US-3.4.2-report.md`
- Quality report: `quality/reports/inc3/US-3.4.2-quality.json`
