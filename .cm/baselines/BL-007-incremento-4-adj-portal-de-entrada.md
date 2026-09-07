# BL-007 — Incremento 4-ADJ: Portal de Entrada y Validación E2E

| Campo | Valor |
|-------|-------|
| Tipo | Incremento (fuera de secuencia, `PLAN_v1.md` no lo numera — mismo criterio que `BL-005`/Incremento 3-ADJ) |
| Fecha apertura | 2026-09-07 |
| Fecha cierre | 2026-09-07 |
| Git tag inicial | `v0.6.0` (`BL-006`) |
| Git tag cierre | `v0.6.1` (PATCH — SP-ADJ fuera de la secuencia de `PLAN_v1.md`, mismo criterio de versionado que `BL-005` → `v0.5.1`) |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | Un Administrador puede dar de alta un Estudiante real de punta a punta desde la UI (Comisión → Docente asignado → invitación → registro); cualquier Docente, Estudiante o Administrador autenticado navega por clic — sin URLs de memoria — desde el login hasta cualquier función de su rol; existe un guion de prueba que valida el flujo completo del MVP (alta de Estudiante → crear contenido → rendir → revisar → analizar) en una sola corrida, arrancando desde el login real. Los tres criterios verificados de punta a punta en `US-ADJ-31`. |

---

## Descripción

Cierra el Incremento 4-ADJ, insertado fuera de la secuencia numérica 0-7 de `PLAN_v1.md`
(mismo criterio que Incremento 3-ADJ: no se renumeran los Incrementos 5-7 ya mapeados a RF).
Origen: pregunta directa de Víctor tras el cierre de `BL-006` ("¿a dónde va cada usuario una
vez que se loguea?"), que reveló que los 3 roles caían en `InicioPlaceholder` sin menú de
navegación persistente desde `US-1.1.7` (Incremento 1) — ninguna de las 4 rondas de UAT
manual anteriores había recorrido el camino real login → función
(`docs/aprendizajes/HITO-9-PORTAL-DE-ENTRADA-SIN-DUENO-DE-PRODUCTO.md`). Ampliado en la
misma sesión de planificación al detectar que tampoco existía UI para crear una Comisión ni
asignar un Docente — sin eso, el alta de un Estudiante real (`RF-01`) estaba rota de punta a
punta en la interfaz, a pesar de que el backend existe desde `US-1.1.1`.

- **Iteración 0 — Modelado** (`US-ADJ-21`, `US-ADJ-22`): mapa de navegación por rol
  (`portal-entrada-modelo.md`, incluida la ampliación de Comisiones) y wireframes/prototipo
  (`wireframes-portal-entrada.md`) aprobados por Víctor.
- **Iteración 1a — Comisiones e Invitación** (`US-ADJ-23` a `US-ADJ-26`, backend + frontend
  juntos): listado de Comisiones por Materia (ampliando el guard de rol a
  `administrador`), alta de Comisión, asignación de Docente, generación del link de
  invitación desde la vista Docente (exponiendo el `token` en la respuesta, antes solo se
  enviaba por email). Completa la UI de `RF-01` (ya "Validado" desde `BL-002`) sin mover
  fila de la matriz de trazabilidad.
- **Iteración 1b — Portal de entrada** (`US-ADJ-27` a `US-ADJ-30`, frontend puro): menú de
  navegación persistente (`AppNav.tsx`) y las 3 homes por rol (Docente, Estudiante,
  Administrador), con `Inicio.tsx` como despacho por rol para la ruta índice.
- **Iteración 2 — Validación E2E** (`US-ADJ-31`, UAT/Verificación, sin código de producción
  propio): guion E2E consolidado ejecutado en navegador real, atravesando los 4 BC en una
  sola corrida desde un login real — Administrador crea Comisión y asigna Docente → Docente
  genera invitación → Estudiante se registra → Docente crea materia, carga preguntas, crea
  actividad → Estudiante rinde (con pausa/reanudación), finaliza, ve revisión y su desempeño
  → Docente ve el desempeño del alumno y la tasa de error por tema. Detectó y corrigió un
  bug real (ver más abajo).

Sin ninguna migración de base de datos nueva en Iteración 1b/2. Iteración 1a agrega el campo
`token` a `InvitacionResponse` y vuelve `email_destinatario` opcional en
`GenerarInvitacionRequest`, sin cambio de esquema.

**Bug real detectado y corregido durante `US-ADJ-31`, fuera del alcance formal de esa US:**
🔴 el fix de `AbortController`/`StrictMode` (documentado en `BL-006` para 5 formularios) no
se había auditado contra el resto del proyecto — quedaron **7 formularios más** con el mismo
patrón roto (`NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`,
`EditarPregunta.tsx`, `NuevaActividad.tsx`, `ExtenderPlazo.tsx`,
`EditarTituloActividad.tsx`, `ResetearPassword.tsx`), 3 de ellos bloqueando directamente el
guion E2E. Corregido en el mismo PR con el patrón ya validado (crear el controller dentro
del `useEffect` y reasignarlo al ref). Track informal (frontend puro), PR #289.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D42 | `docs/design/domain/portal-entrada-modelo.md`, `docs/design/ux/wireframes-portal-entrada.md` + `prototipos/portal-entrada.html` | Documento | Mapa de navegación por rol y wireframes/prototipo del portal de entrada y pantallas de Comisiones (`US-ADJ-21`, `US-ADJ-22`) |
| CI-D43 | `docs/plans/inc4-adj/US-ADJ-2*-context.md`/`-plan.md`, `docs/plans/inc4-adj/inc4-adj-candidatas.md` | Documento | Contexto y plan de las 11 US-IEDD del incremento |
| CI-D44 | `docs/reports/inc4-adj/US-ADJ-23-report.md` a `US-ADJ-26-report.md` | Documento | Reportes de cierre de la Iteración 1a |
| CI-D45 | `quality/reports/uat/inc4-adj/design.md`/`evidencia.md` | Documento | Diseño y evidencia de la UAT E2E consolidada (`US-ADJ-31`) |
| CI-C19 | `src/identidad/interface_adapters/security/*` (guard `require_docente_o_administrador`), `frameworks/api/{comisiones_router,materias_comisiones_router}.py`, `interface_adapters/gateways/comision_query_repository.py` | Código de backend | Amplía el rol autorizado a `administrador` en los endpoints de Comisiones/Materias ya existentes; corrige `docentes_asignados=[]` hardcodeado en `SQLAlchemyComisionQueryRepository` (`US-ADJ-23`) |
| CI-C20 | `src/identidad/entities/invitacion.py` (evento `InvitacionResponse` con `token`), `frameworks/api/comisiones_router.py` (`GenerarInvitacionRequest.email_destinatario` opcional) | Código de backend | Expone el token de invitación en la respuesta HTTP para mostrarlo en pantalla (`US-ADJ-26`) |
| CI-C21 | `src/identidad/interface_adapters/controllers/comisiones_query_controller.py` (`obtener_comision`) | Código de backend | `GET /comisiones/{id}` nuevo — pass-through fino sobre `ComisionRepositoryPort.obtener_por_id()` (`US-ADJ-25`) |
| CI-F13 | `frontend/src/pages/identidad/{Comisiones,NuevaComision,ComisionDetalle}.tsx`, `frontend/src/pages/actividad-evaluativa/{ComisionesDeMateria,ComisionDetalleDocente}.tsx`, `frontend/src/lib/identidad-comisiones-api.ts` (ampliado), `frontend/src/lib/session.ts` (`obtenerUsuarioId()`) | Código de frontend | Pantallas de Comisiones — vista Administrador y vista Docente (Iteración 1a) |
| CI-F14 | `frontend/src/components/AppNav.tsx`, `frontend/src/layouts/AppLayout.tsx` (integración), `frontend/src/pages/{HomeDocente,HomeEstudiante,HomeAdministrador,Inicio}.tsx` | Código de frontend | Menú de navegación persistente y las 3 homes por rol (Iteración 1b) |
| CI-F15 | 7 formularios con fix de `AbortController` (ver Descripción) | Código de frontend | Fix del bug de submit en modo dev detectado en `US-ADJ-31`, PR #289 |
| CI-T08 | `quality/reports/architectanalyst/BL-007-arquitectura.json`, `quality/reports/designreviewer/BL-007-designreviewer.txt` | Herramienta | Salidas de cierre de baseline (`ArchitectAnalyst`/`DesignReviewer` consolidados) |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 892 passed, 0 failed
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (213 archivos)
- `pylint src/`: 9.59/10 (sin cambios respecto de `BL-006`)
- Cobertura (`pytest --cov=src --cov-report=json`): 98.99% (2680 statements, 27 sin cubrir)

**Frontend:**
- `vitest run`: 329/329 tests, 55 archivos
- Cobertura: 90.38% statements / **79.74% branches** / 84.79% functions / 92.73% lines —
  **por debajo del umbral de 80% de branches** (deuda preexistente ya reportada como chip
  aparte, `task_ec36dcbe`, al cerrar `US-ADJ-24`: `Comisiones.tsx` quedó con 27.77% de
  cobertura de branches sin tests propios; no es una regresión introducida en esta
  baseline — el propio chip documenta que el umbral ya estaba roto en `develop` antes de
  `US-ADJ-24`). Queda como deuda técnica explícita para una US de ajuste futura, no bloquea
  este cierre (mismo criterio que otras deudas ya aceptadas del proyecto, p. ej. "Zone of
  Pain" de `ArchitectAnalyst`).
- `oxlint`: 0 errores, 5 warnings preexistentes (`only-export-components`, 1 warning de test)
- `tsc -b`: 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml` (consolidado, estado final del incremento): 0
  CRITICAL, 132 advertencias (`BL-006`: 131 — suba mínima, sin cluster nuevo relevante; el
  incremento fue mayormente frontend/`identidad`), 95.8h de deuda técnica estimada (0h
  bloqueante)
- `architectanalyst src/ --sprint-id BL-007`: 6 críticos (mismo "Zone of Pain" ya
  documentado y aceptado — `identidad`, `settings`, `shared`, `banco_preguntas`,
  `actividad_evaluativa`, `analytics` — sin módulo nuevo este incremento), 10 warnings, 133
  infos, `should_block: false` (`.cm/baselines/BL-007-arquitectura.json`, copia de
  `quality/reports/architectanalyst/BL-007-arquitectura.json`)

**UAT (`PROCEDIMIENTO-UAT.md`):**
- `US-ADJ-31`: `quality/reports/uat/inc4-adj/design.md`/`evidencia.md` — Capa 1 (892 pytest +
  329 Vitest, control de regresión) en verde; Capa 2 = guion E2E completo en navegador real
  (Claude Browser), sin seeds, arrancando desde el login real — 19/19 pasos completados sin
  hallazgos 🔴 Bloqueantes tras el fix de `AbortController`. 2 observaciones 🟡 registradas y
  revisadas: una descartada como falso positivo (carrera entre el screenshot de la sesión y
  la respuesta async, reproducida de nuevo sin el problema), la otra era solo un orden de
  guion a corregir en el propio documento (Materia antes que Comisión) — ninguna requirió
  cambio de código adicional. **Confirmado por Víctor** (2026-09-07).
- Ningún RF de `RF_v1.md` pasa de estado en `docs/traceability/matrix.md` — la mayoría de
  las US-IEDD de este incremento no tiene RF asociado (mismo criterio que `US-1.1.0`); las
  de Comisiones/Invitación completan la UI de `RF-01`, ya "Validado" desde `BL-002`.

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Insertar el incremento fuera de la secuencia 0-7 de `PLAN_v1.md`, sin renumerar | Mismo criterio que `Incremento 3-ADJ` — deuda de producto detectada después de cerrar un incremento ya numerado, no vale la pena reordenar toda la numeración restante. |
| Ampliar el alcance original (solo navegación) a incluir Comisiones/Invitación | Detectado en la misma sesión de planificación (Iteración 0): sin pantalla para crear Comisión y asignar Docente, la Validación E2E planeada (`US-ADJ-31`) no podía ejecutarse con un alta de Estudiante real — se agregó al mismo incremento por cerrar un prerrequisito de una iteración ya adentro, no un incremento nuevo. |
| `GET /comisiones/{id}` nuevo, sin Use Case dedicado | Pass-through fino sobre `ComisionRepositoryPort.obtener_por_id()` ya existente — mismo criterio que `listar_estudiantes`, evita ceremonia innecesaria para una lectura simple (`US-ADJ-25`). |
| Exponer el token de invitación en la respuesta HTTP | El endpoint original (`US-1.1.1`) estaba diseñado para enviar el token solo por email — la UI de `US-ADJ-26` necesita mostrarlo/copiarlo en pantalla. Se agregó el campo sin invariante de dominio nueva, y `email_destinatario` pasó a opcional para no forzar un envío real en este flujo. |
| Fix de `AbortController` en 7 formularios sin US-ADJ propia | Bug preexistente de `US-ADJ-20` (`BL-005`) no auditado contra el resto del proyecto, detectado recién al ejercitar el guion completo — mismo criterio de "fix directo sobre código ya en `develop`" ya aplicado en `BL-006` para los primeros 5 formularios. |
| Deuda de cobertura de branches del frontend no resuelta en esta baseline | `Comisiones.tsx` (`US-ADJ-23`) sin tests propios de branches — ya reportada como chip aparte antes de este cierre; se documenta y se deja pendiente en vez de improvisar tests de último momento solo para cerrar el número. |

---

## Retrospectiva

### ¿Qué funcionó?

- La pregunta de Víctor ("¿a dónde va cada usuario?") disparó todo el incremento — un
  recordatorio de que el `HITO-9` (UAT sin dueño de producto) seguía siendo un gap real
  después de 4 incrementos y 4 rondas de UAT manual sin detectarlo.
- Ampliar el alcance en la propia Iteración 0 (antes de escribir código) en vez de
  descubrir el gap de Comisiones a mitad de la Iteración 1a evitó un retrabajo — el
  `portal-entrada-modelo.md` ya documentó la ampliación con su razón antes de que existiera
  ninguna spec de US.
- Separar Iteración 1a (Comisiones, toca `src/`) de Iteración 1b (portal puro, frontend) dejó
  clara la frontera entre "completa un RF ya Validado" y "navegación transversal sin RF
  propio" — ninguna de las 8 US de esas dos iteraciones tuvo ambigüedad de alcance.
- La Validación E2E (`US-ADJ-31`) sin seeds — todo por clic desde el login — resultó ser la
  forma más efectiva hasta ahora de encontrar bugs reales: encontró en una sola corrida un
  bug que 3 baselines anteriores (con seeds) no habían expuesto.

### ¿Qué fue más difícil de lo esperado?

- El fix de `AbortController` de `BL-006` cubrió solo 5 de 12 formularios con el mismo
  patrón — un fix puntual sin un grep de auditoría completa dejó la mayoría del bug sin
  corregir. Cuarto episodio del patrón "UAT en navegador real detecta lo que Vitest mockeado
  no ve" (`[[feedback_uat_navegador_real]]`), y el primero donde el propio fix anterior
  quedó incompleto por alcance, no por un bug nuevo.
- Los inputs `datetime-local` del navegador no aceptan `type` de teclado estándar en la
  automatización — hubo que usar `form_input` con el valor ISO directo en vez de simular
  tecleo, dato a tener en cuenta para cualquier guion E2E futuro con este tipo de campo.
- Una observación registrada durante la corrida ("UI no refresca sola") resultó ser un falso
  positivo — una carrera entre el screenshot de la propia sesión y la respuesta async, no un
  bug del código. Vale la pena esperar un instante antes de leer la pantalla tras una acción
  async, en vez de asumir que el primer screenshot ya refleja el estado final.

### ¿Qué ajustar en el próximo incremento?

- Cuando se corrija un bug con un patrón repetido en varios archivos (como
  `AbortController`), correr un `grep` de auditoría sobre todo `frontend/src/` antes de
  cerrar la US — no confiar en que el fix puntual cubrió todos los casos.
- Resolver la deuda de cobertura de branches de `Comisiones.tsx` (y cualquier otro archivo
  bajo el umbral) en la próxima iteración de ajuste técnico, antes de que se acumule más
  deuda sin resolver como en `Incremento 3-ADJ`.
- Seguir usando guiones E2E sin seeds (por clic desde el login) como parte del cierre de
  cada Incremento, no solo como excepción — el valor de encontrar bugs reales superó
  ampliamente el costo de tiempo frente a un guion con seeds.

---

*Creado: 2026-09-07*
