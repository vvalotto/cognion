# BL-012 — Incremento 7-ADJ: Ciclo de vida de la cuenta y ajustes de la UAT v1

| Campo | Valor |
|-------|-------|
| Tipo | Incremento (fuera de secuencia, `PLAN_v1.md` no lo numera — mismo criterio que `BL-005`/`BL-007`/`BL-010`) |
| Fecha apertura | 2026-10-02 |
| Fecha cierre | 2026-10-15 |
| Git tag inicial | `v0.8.0` (`BL-011`) |
| Git tag cierre | `v0.8.1` (PATCH — incremento fuera de la secuencia de `PLAN_v1.md`, mismo criterio de versionado que `BL-005` → `v0.5.1`, `BL-007` → `v0.6.1`, `BL-010` → `v0.7.1`) |
| Estado | ✅ Completado en `develop`. Merge `develop → main` y tag `v0.8.1`: pendientes de confirmación explícita de Víctor |
| DoD | Las 4 US formales (`US-ADJ-59` a `62`) cerradas con su PR mergeado y su Issue cerrado; spike del hallazgo #1 resuelto; hallazgos #7 y #9 corregidos; un pase de navegador real al cierre con la base resembrada; `BL-012` registrada. **No cumplido, diferido por decisión de Víctor (2026-10-05):** re-prueba del hallazgo #6 con el iPhone (ver "Pendientes que arrastra") |

---

## Descripción

Incremento insertado fuera de la secuencia numérica 0-7 de `PLAN_v1.md` (mismo criterio que
Incremento 3-ADJ a 6-ADJ), **antes** de la Iteración 2 del Incremento 7 (RF-07, importación
desde PDF) por decisión de Víctor del 2026-10-02. Origen: los 11 hallazgos de la UAT manual de
cierre de alcance v1 (Incremento 7, Iteración 1, `quality/reports/uat/inc7/`), de los cuales dos
eran 🔴: una cuenta deshabilitada podía seguir iniciando sesión, y el sistema podía quedar sin
Administrador operativo. Ambos son reglas del ciclo de vida de la cuenta que el sistema no hacía
cumplir; tocan `src/` y por eso fueron por el track formal.

- **`US-ADJ-59`** — una cuenta deshabilitada no puede iniciar sesión (hallazgo #11 🔴). `403` con
  `detail` estructurado `cuenta_deshabilitada`, chequeado antes de la contraseña y de
  `bloqueada`, sin consumir intentos. Solo en el login: las sesiones ya emitidas viven hasta que
  expira el JWT (`ADR-013`). PR #479, Issue #474.
- **`US-ADJ-60`** — el sistema siempre conserva al menos un Administrador operativo (hallazgo #4
  🔴). Un Administrador nunca se borra (la baja es una deshabilitación reversible), `409`
  estructurado si se intenta deshabilitar al último operativo, y el bloqueo automático del último
  Administrador pasa a ser **temporal** (15 minutos, `administrador_bloqueo_temporal_minutos`,
  vencimiento perezoso, sin proceso de fondo). Migración `c4d1f9a27b60`
  (`usuario.bloqueada_hasta timestamptz NULL`, sin backfill). Política extraída a
  `entities/bloqueo_cuenta.py` porque el pre-push gate marcó 3 CRITICAL al crecer `Usuario`.
  PR #480, Issue #475.
- **`US-ADJ-62`** — recuperar la contraseña por email también desbloquea la cuenta (hallazgo #5
  🟡). `Usuario.recuperar_password` delega en `resetear_password`; `ConfirmarNuevaPasswordUseCase`
  emite `CuentaDesbloqueada | None`; libera también al último Administrador bloqueado
  temporalmente; no reactiva una cuenta deshabilitada. **Revierte una decisión de `US-ADJ-39`**
  (spec, feature, steps, wireframe §3.1 e `INV-ID-10` enmendados). La alerta de "Cuenta
  bloqueada" ofrece el link a la recuperación. Backend PR #481, frontend PR #482 (gate UX
  aprobado), Issue #477. El CI detectó un test de `inc1` que seguía afirmando el comportamiento
  viejo (ver retrospectiva).
- **`US-ADJ-61`** — la actividad cerrada se ve como cerrada para el Estudiante (hallazgo #10 🟡).
  Nuevo estado `cerrada` en `EstadoVisible` (`finalizada` sigue ganando, RF-13), badge "Cerrada"
  neutro, pantalla "Esta actividad ya cerró" y texto neutro cuando se llega sin contexto (el
  `422` de `IniciarEvaluacion` no dice el motivo); "Mis materias" ya no cuenta una cerrada como
  pendiente. Backend PR #483, frontend PR #484 (gate UX aprobado), Issue #476.
- **Arreglos informales (solo `frontend/`)**: hallazgos #3 y #8 de la UAT v1 (PR #472), #7 y #9
  (PR #485), y los hallazgos H-1 y H-2 de la UAT de este incremento (PR #486).
- **Spike del hallazgo #1** (autoregistro `201` sin persistir): **no reproducible** — 13 envíos
  desde el navegador, modo dev (StrictMode) y build de producción, con el log del backend y
  `psql` contrastando cada uno.
- **UAT de cierre en navegador real** (`quality/reports/uat/inc7-adj/`, PR #494): Bloques 0 a 6
  sin hallazgos 🔴. El hallazgo #6 (demora en el iPhone) quedó fuera por decisión de Víctor.

Entre `v0.8.0` y este cierre entraron también cambios que no son del 7-ADJ pero quedan en esta
baseline: higiene de repositorio (PR #471), el fix de `/` sin sesión que había quedado 22 días
sin mergear (PR #292), bumps de Dependabot verificados con CI (`react-router` 7→8, entre otros)
y la replanificación del Incremento 7 (PR #465).

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D54 | `docs/specs/ajustes/US-ADJ-59.md` a `US-ADJ-62.md` | Documento | Specs US-IEDD del incremento |
| CI-D55 | `docs/reports/inc7-adj/US-ADJ-59-report.md` a `US-ADJ-62-report.md` | Documento | Reportes de cierre de `/implement-us` (`US-ADJ-61`/`62` en dos PRs: Parte A backend y Parte B frontend) |
| CI-D56 | `docs/plans/inc7-adj/` (`inc7-adj-candidatas.md`, `US-ADJ-59` a `62` `-context.md`/`-plan.md`) | Documento | Plan del incremento y trabajo de cada US |
| CI-D57 | `quality/reports/uat/inc7-adj/` (`plan-de-pruebas`, `registro-ejecuciones`, `registro-hallazgos`, `plan-de-correccion`) | Documento | UAT de cierre en navegador real |
| CI-D58 | `docs/design/domain/BC-identidad-modelo.md` (enmienda a `INV-ID-10`, `INV-ID-18` a `21`, `bloqueada_hasta`), `docs/design/ux/wireframes-cuentas-administracion.md`, `wireframes-identidad-autoservicio.md`, `wireframes-actividad-evaluativa.md` + prototipos | Documento | Modelo y UX reconciliados con el incremento |
| CI-D59 | `docs/specs/ajustes/US-ADJ-39.md`, `docs/specs/inc3/US-3.4.5.md` | Documento | Marcadas "enmendada por US-ADJ-62" / "enmendada por US-ADJ-61" |
| CI-C27 | `src/identidad/entities/{usuario,bloqueo_cuenta,errors}.py`, `use_cases/{iniciar_sesion,cambiar_password,eliminar_cuenta,confirmar_nueva_password,politica_bloqueo}.py` | Código de backend | Reglas de ciclo de vida de la cuenta (`US-ADJ-59`, `60`, `62`) |
| CI-C28 | `src/identidad/frameworks/` (`db/models.py`, migración `c4d1f9a27b60`, routers con `403`/`409` estructurados) | Código de backend | Persistencia de `bloqueada_hasta` y contratos HTTP nuevos |
| CI-C29 | `src/actividad_evaluativa/use_cases/listar_actividades_visibles.py` | Código de backend | `_estado_para` con el estado `cerrada` (`US-ADJ-61`) |
| CI-F19 | `frontend/src/pages/identidad/{Login,LoginCuentaBloqueadaError,LoginCuentaBloqueadaTemporalError,LoginCuentaDeshabilitadaError}.tsx`, `pages/cuentas/EliminarCuenta.tsx` | Código de frontend | Alertas de login y baja de cuenta |
| CI-F20 | `frontend/src/pages/actividad-evaluativa/{MisActividades,FueraDePeriodo}.tsx`, `components/ui/badge.tsx`, `lib/cierre-actividad.ts` | Código de frontend | Badge "Cerrada" y pantalla "ya cerró" (`US-ADJ-61`, H-1) |
| CI-F21 | `frontend/src/pages/analytics/{RankingPreguntasFalladas,EvolucionTemporal}.tsx` | Código de frontend | Hallazgos #7, #9 y H-2 |
| CI-T14 | `quality/reports/designreviewer/BL-012-designreviewer.json`, `.cm/baselines/BL-012-arquitectura.json` | Herramienta | Salidas de cierre de esta baseline |

---

## Métricas al cerrar

**Backend** (suite completa contra base descartable, `DATABASE_URL` inline, verificada la base
de desarrollo intacta al terminar):
- `pytest tests/ --cov=src --cov-report=json`: **1883 passed** (unit + integration + BDD), 17 min
- `ruff check src/`: 0 violaciones
- `mypy src/`: 0 errores (303 archivos)
- `pylint src/`: 9.59/10 (igual que `BL-011`)
- Cobertura: **96.94 %** (4968/5125 statements; `ArchitectAnalyst.CoverageAnalyzer` reporta
  96.9 %)

**Frontend:**
- `npx vitest run --coverage`: **827 passed** (108 archivos de test), 0 fallos
- `npx oxlint src`: 0 errores (advertencias preexistentes, sin relación con este incremento)
- `npx tsc -b`: 0 errores
- Cobertura: 93.56 % statements / 86.14 % branches / 90.37 % functions / 96.32 % lines — por
  encima del umbral de 80 % en las 4 métricas

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: **0 CRITICAL**, 334 advertencias sobre 303
  archivos (`BL-011`: 330 sobre 300), `should_block: false`
- `architectanalyst src --sprint-id BL-012 --config pyproject.toml`: 7 CRITICAL
  (`DistanceAnalyzer`, "Zone of Pain"), uno por paquete raíz (`actividad_evaluativa`,
  `analytics`, `banco_preguntas`, `identidad`, `notificaciones`, `settings`, `shared`) — el mismo
  falso positivo aceptado desde `US-ADJ-13`/`19` (`Ca=Ce=0` para todo el proyecto por el bug de
  `DependencyGraphBuilder`, `software_limpio#77`), sin módulo nuevo desde `BL-010`;
  `should_block: false`, sin acción.

**Migración de esquema:** una, `c4d1f9a27b60` (`usuario.bloqueada_hasta timestamptz NULL`), sin
backfill; round-trip `upgrade`/`downgrade` verificado en `US-ADJ-60`.

---

## UAT de cierre

UAT de cierre en navegador real, ejecutada el 2026-10-05 (`quality/reports/uat/inc7-adj/`, PR
#494): 7 bloques planificados, 6 ejecutados (el Bloque 7, hallazgo #6 del iPhone, fuera de
alcance por decisión de Víctor). Backend y frontend levantados contra la base de desarrollo
resembrada (`tests/uat/datos-reales/sembrar.py`: 1 Administrador, 2 Docentes, 17 Estudiantes,
110 preguntas, 2 actividades), cada paso contrastado con el log del backend y `psql`.

| Bloque | Resultado |
|---|---|
| 0 — Preparación (migración, siembra, servidores) | ✅ |
| 1 — Spike del hallazgo #1 | ✅ No reproducible (13 envíos; dev y build) |
| 2 — `US-ADJ-59` | ✅ 3/3 |
| 3 — `US-ADJ-60` | ✅ 5/5 |
| 4 — `US-ADJ-62` | ✅ 5/5 |
| 5 — `US-ADJ-61` | ✅ 6/6 (con H-1) |
| 6 — Hallazgos #7, #9 y fixes #3/#8 | ✅ (con H-2) |

Hallazgos: ninguno 🔴. **H-1** 🟡 (una actividad cerrada a mano mostraba su fecha de cierre
*programada*, futura, como si fuera la de cierre) y **H-2** ⚪ (etiqueta final del eje de
"Evolución temporal" cortada contra el borde) — resueltos en el PR #486 y verificados en
navegador real. **O-1** ⚪ (el 3.er intento fallido, el que bloquea, no avisa del bloqueo; se
informa en el 4.º — es el contrato de la spec) y **O-2** ⚪ (una pregunta de la siembra con `**`
del import del `.docx`) quedaron sin cambio de código. `plan-de-correccion.md` aprobado por
Víctor.

---

## Actualización de la matriz de trazabilidad

**Sin cambio de estado de ningún RF.** `US-ADJ-59`, `60`, `61` y `62` son ajustes sobre RF ya
"Validado" (Identidad: RF-02, RF-03, RF-19, RF-24; Actividad Evaluativa: el listado y la
revisión del Estudiante) y no agregan filas — mismo criterio que
`US-ADJ-57`/`US-ADJ-58`. `docs/traceability/matrix.md` actualizado solo en su nota de cabecera,
referenciando esta baseline.

---

## Retrospectiva

**Qué funcionó:**
- La UAT en navegador real, contrastada contra el log del backend y la base, volvió a detectar lo
  que los tests automatizados (que mockean `fetch`) no ven: la fecha de cierre engañosa (H-1) y
  la etiqueta cortada contra el borde (H-2) pasaron los 506 tests de las carpetas tocadas y sólo
  se vieron en pantalla. Mismo patrón ya documentado desde Identidad.
- Partir cada US en Parte A (backend) y Parte B (frontend, tras el gate UX) permitió mergear lo
  que no dependía del diseño sin esperar la aprobación, y mantuvo cada PR chico y revisable.
- El spike del hallazgo #1 con método explícito (cada envío contrastado con log y base, dev y
  build) dio una conclusión honesta —"no reproducible"— con sus límites declarados, en vez de un
  "cerrado" sin sustento.

**Qué ajustar:**
- **Correr el BC completo, no solo lo que uno cree afectado.** Al invertir la regla de
  `US-ADJ-62` se corrigieron los tests de `inc5-adj` e `inc7-adj`, pero un test de `inc1` seguía
  afirmando el comportamiento viejo y lo detectó recién el CI, con una espera de ~25 minutos para
  corregirlo. Regla práctica: al cambiar la firma o la regla de un use case, correr todo el BC
  contra una base descartable antes de pushear.
- **`DATABASE_URL` inline y verificado, en el mismo comando.** Un `sed -i` con sintaxis GNU
  falló en macOS dentro de una cadena `&&`, dejó sin definir la variable de la base descartable
  y lanzó una corrida de `pytest` que pudo apuntar a la base de desarrollo (cortada a los
  segundos). Ya había pasado en `US-ADJ-60` (la base de desarrollo quedó vacía). En esta
  baseline la suite completa corrió con la URL inline, un guard previo y una verificación final
  de que la base de desarrollo conservaba sus 20 usuarios.
- **`architectanalyst` se corre con `--config pyproject.toml`.** Sin ese flag no lee
  `[tool.architectanalyst]` y su `CoverageAnalyzer` avisa que no encontró `coverage.json` aunque
  exista; anotado en `CLAUDE.md` §Quality gates.
- **Las capturas del navegador integrado a veces muestran el estado anterior de la página** (desfase
  de render). En la UAT se tomó como referencia el DOM y la base, no la captura.
- **El DoD del incremento incluía "#6 re-probado con el iPhone" y se dejó fuera de la UAT.** Es
  una decisión legítima de Víctor, pero el DoD y el alcance real de la UAT divergieron: cuando se
  decide dejar un ítem fuera, conviene reescribir el DoD en el momento, no al cerrar.
- **Observación O-1** (el tercer intento no avisa del bloqueo) cumple la spec pero deja al usuario
  sin información; queda abierta a decisión de producto.

---

## Pendientes que arrastra

- **Hallazgo #6** (demora de ~10 s en el iPhone al mostrar opciones en la sesión en vivo): sin
  reprobar con el iPhone; el iPad anduvo bien. Requiere el dispositivo y/o staging con WSS real
  (`PROCEDIMIENTO-UAT.md` §4, ítem abierto aparte).
- 2 tests BDD de `US-3.2.2` que fallaron en un entorno local (`KeyError: 'id'` en el setup) y
  pasaron en el CI; sin causa identificada.
- 3 PRs de Dependabot abiertos contra `main` (#468, #469, #470) y otros 7 contra `develop`
  (#487 a #493), tres de ellos saltos de versión mayor (`vitest` 4→5, `jsdom` 29→30, `react-dom`).

---

## Próximo paso

Merge `develop → main` y tag `v0.8.1` (con confirmación explícita de Víctor), cierre del Milestone
[#15](https://github.com/vvalotto/cognion/milestone/15). Después, Iteración 2 del Incremento 7:
`RF-07` (importación desde PDF), cuyo spike entre parseo automático y asistido necesita decisión
de Víctor antes de especificar.
