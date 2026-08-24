# BL-003 — Banco de Preguntas + Gestión de Cuentas (Incremento 2)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento |
| Fecha apertura | 2026-07-30 |
| Fecha cierre | 2026-08-23 |
| Git tag inicial | `v0.3.0` (asignado retroactivamente a `BL-002` el 2026-08-24 — ver nota abajo) |
| Git tag cierre | `v0.4.0`, taggeado el 2026-08-24 sobre el commit `e31ee67` al mergear `develop → main` junto con `BL-002` en una sola operación (decisión de Víctor: mantener coherencia de hitos con un tag por baseline en vez de un único merge sin tags intermedios). El deploy real (Fly.io/servidor FIUNER) queda como decisión institucional a resolver hacia el final del desarrollo, sin relación con este merge — `cd.yml` solo construye la imagen Docker. |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | El docente arma y mantiene el banco de preguntas completo, filtrable por materia/unidad/tema/dificultad/importancia. El administrador resuelve problemas de cuentas sin depender del docente (`PLAN_v1.md`, Hito Incremento 2). Backend y frontend implementados e integrados juntos — mismo criterio de cierre de baseline que `BL-002` (`docs/plans/PLAN-CM.md` §7). |

---

## Descripción

Cierra el Incremento 2 de `PLAN_v1.md`: BC Banco de Preguntas completo (RF-04, RF-05, RF-06)
y BC Identidad ampliado con gestión de cuentas por administrador y cambio de contraseña propio
(RF-03, RF-19). Incluye:

- **Iteración 0 — Modelado** (`US-2.0.1`, `US-2.0.2`): event storming del BC Banco de
  Preguntas y wireframes de carga/filtrado.
- **Iteración 1 — Banco de Preguntas** (`US-2.1.1` a `US-2.1.13`, backend + frontend): alta de
  materia, dos tipos de pregunta autovalidantes (opción múltiple, verdadero/falso), edición,
  baja lógica, filtrado por metadatos, y toda la UI correspondiente.
- **Iteración 2 — Cuentas** (`US-2.2.1` a `US-2.2.9`, backend + frontend): bloqueo automático
  por 3 intentos fallidos, listado/detalle/reseteo de cuentas por Administrador, cambio de
  contraseña propio, reflejo del bloqueo en el login.
- **`SP-ADJ-01`** (iteración de ajuste conjunta, `US-ADJ-01/03/04/05`): estilo visual alineado
  al prototipo aprobado (Banco de Preguntas y Cuentas) y paginación en ambos listados —
  agrupa la deuda de UX/paginación detectada en la UAT de cierre de Iteración 1, según la
  decisión de secuenciación tomada el 2026-08-19 (no fragmentar en mini-ajustes).
- **Ajuste UX en vivo** post-`SP-ADJ-01` (2026-08-23, PRs #120/#121, sin US formal — track
  informal por tocar solo `frontend/`): correcciones puntuales de breadcrumb, layout y estilo
  detectadas comparando cada pantalla contra su prototipo HTML en navegador real, una de ellas
  (columna "Eliminar" cortada) solo visible al cargar 60 preguntas reales, no con los 3
  fixtures mínimos del prototipo.

Quedan 3 candidatas documentadas y explícitamente diferidas, fuera del alcance de esta
baseline: `US-ADJ-06` (nombre real en el header), `US-ADJ-07` (`comisionId` sin resolver a
nombre legible), `US-ADJ-08` (chip de materia/comisión en Registro antes de completar el
formulario) — las tres tocan `src/`, quedan en cola como US-IEDD de un próximo incremento.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D22 | `docs/design/domain/BC-banco-preguntas-modelo.md` | Documento | Event storming del BC Banco de Preguntas (`US-2.0.1`), incluye el "hot spot" de `Comisión.materia` resuelto en `US-2.1.2` |
| CI-D23 | `docs/design/ux/wireframes-banco-preguntas.md` + prototipo `banco-preguntas-carga-filtrado.html` | Documento | Wireframes y prototipo navegable del Banco de Preguntas (`US-2.0.2`), gate UX de la Iteración 1; revisado en `US-ADJ-01`/`US-ADJ-03` para reflejar el rediseño visual y la paginación |
| CI-D24 | `ADR-019-jwt-rbac-en-shared.md` | Documento | Decisión de extraer JWT/RBAC de `src/identidad` a `src/shared` (`US-2.1.1`), habilita RBAC por rol fuera de Identidad sin imports cruzados entre BCs |
| CI-D25 | `docs/design/ux/wireframes-cuentas-administracion.md` + prototipo `identidad-cuentas-administracion.html` | Documento | Wireframes y prototipo navegable de gestión de cuentas y cambio de contraseña (aprobados 2026-08-19), gate UX de la Iteración 2; revisado en `US-ADJ-04`/`US-ADJ-05` |
| CI-D26 | `docs/specs/inc2/US-2.0.*` a `US-2.2.9.md`, `docs/specs/ajustes/US-ADJ-01/03/04/05.md`, `docs/plans/inc2/inc2-candidatas.md` | Documento | Specs de las 25 US-IEDD del Incremento 2 (Iteraciones 0, 1, 2) y de la iteración de ajuste `SP-ADJ-01`, más el plan de candidatas del incremento |
| CI-D27 | `quality/reports/uat/inc2/design.md`/`evidencia.md` + `design-iter2.md`/`evidencia-iter2.md` | Documento | Diseño y evidencia de UAT de cierre de Iteración 1 e Iteración 2 (`PROCEDIMIENTO-UAT.md`), incluye las 3 no conformidades 🟡 que originaron `SP-ADJ-01` |
| CI-D28 | `docs/specs/ajustes/US-ADJ-06/07/08.md` | Documento | Candidatas de ajuste detectadas durante el ajuste visual en vivo (nombre real en header, comisión legible en Detalle, comisión visible antes de registrar) — especificadas, no implementadas, sin iteración asignada |
| CI-C08 | `src/shared/entities/{tipo_perfil,jwt,errors}.py`, `entities/ports/jwt_issuer_port.py`, `frameworks/security/jwt_pyjwt.py`, `interface_adapters/security/{get_current_user,require_rol}.py` | Código de backend | JWT/RBAC transversal extraído de `identidad` a `shared` (`ADR-019`, `US-2.1.1`), primer consumo por un BC distinto de Identidad |
| CI-C09 | `src/banco_preguntas/` (BC completo) | Código de backend | Entities/use_cases/interface_adapters/frameworks — `Materia`, `Banco`, `PreguntaPlantillaOpcionMultiple`/`VerdaderoFalso` (INV-BP-00 a 04), alta/edición/baja lógica/filtrado y paginación opt-in (`US-2.1.1` a `US-2.1.7`, `US-ADJ-03`) |
| CI-C10 | `src/identidad/entities/comision.py`, `entities/ports/materia_port.py`, `use_cases/{crear_comision,registrar_estudiante}.py`, gateways/controllers asociados | Código de backend | Refactor `Comisión.materia_id` referenciado por puerto (`MateriaPort`) hacia Banco de Preguntas, sin imports directos entre BCs (`US-2.1.2`) |
| CI-C11 | `src/identidad/entities/usuario.py` (bloqueo/contadores/`creado_en`/validación de password), `entities/ports/cuenta_query_port.py`, `use_cases/{listar_cuentas,obtener_cuenta,resetear_password,cambiar_password}.py`, `interface_adapters/controllers/{cuentas_controller,perfil_controller}.py` | Código de backend | Bloqueo automático de cuenta, listado/detalle/reseteo de cuentas por Administrador, cambio de password propio y paginación fija del listado (`US-2.2.1` a `US-2.2.5`, `US-ADJ-05`) |
| CI-C12 | `migrations/versions/*` (Incremento 2) | Código de backend | Migraciones Alembic del Incremento 2 (tablas `materia`/`banco`/`pregunta_plantilla`, `respuesta_correcta`, bloqueo/contadores, `creado_en`, `fecha_creacion`, `Comisión.materia_id`), todas con backfill sin `UPDATE` manual |
| CI-F06 | `frontend/src/lib/banco-preguntas-api.ts`, `pages/{Materias,NuevaMateria,Banco,NuevaPreguntaTipo,NuevaPreguntaOpcionMultiple,NuevaPreguntaVerdaderoFalso,EditarPregunta,EliminarPregunta}.tsx` | Código de frontend | UI completa del Banco de Preguntas — alta de materia, carga por tipo, filtrado, edición y baja lógica (`US-2.1.8` a `US-2.1.13`) |
| CI-F07 | `frontend/src/lib/cuentas-api.ts`, `pages/{Cuentas,CuentaDetalle,ResetearPassword,CuentaReseteada,CambiarPassword,LoginCuentaBloqueadaError}.tsx` | Código de frontend | UI completa de gestión de cuentas — listado/filtro, detalle, reseteo/desbloqueo, cambio de password propio y reflejo de bloqueo en login (`US-2.2.6` a `US-2.2.9`) |
| CI-F08 | `frontend/src/components/ui/{card,badge,button,pagination}.tsx`, `components/Breadcrumb.tsx` | Código de frontend | Primitivas visuales nuevas alineadas al prototipo aprobado (cards, tags de color, paginación reusable, breadcrumb) — base de `US-ADJ-01`/`US-ADJ-04`, reusada íntegra por `US-ADJ-05` |
| CI-F09 | `frontend/src/pages/{Login,Registro,RegistroError,RegistroExito,LoginCuentaBloqueadaError,CuentaDetalle,Cuentas,Banco,EditarPregunta,EliminarPregunta,NuevaPreguntaTipo,NuevaPreguntaOpcionMultiple,NuevaPreguntaVerdaderoFalso}.tsx`, `layouts/AuthLayout.tsx` | Código de frontend | Ajuste visual en vivo post-`SP-ADJ-01` (PRs #120/#121, mergeados directo a `develop` sin US formal) — alineación de Registro/Login/Cuentas/Banco al prototipo HTML aprobado (breadcrumb, encabezados, columnas, texto envuelto en filas) |
| CI-T05 (ext.) | `.claude/skills/run-cognion/smoke.sh` | Herramienta | Extendido con el flujo end-to-end del Banco de Preguntas y de bloqueo/reseteo de cuentas (`US-2.1.*`, `US-2.2.1` a `US-2.2.5`) — mismo CI abierto en `BL-002`, sin renumerar |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 374 passed
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (136 archivos)
- `pylint src/`: 9.44/10
- Cobertura (`pytest --cov=src`): 99% (1410 statements, 13 sin cubrir)

**Frontend:**
- `vitest run`: 165/165 tests, 29 archivos
- Cobertura: 92.13% statements / 84.41% branches / 91.04% functions
- `oxlint`: 0 errores, 3 warnings preexistentes (`only-export-components`, patrón shadcn/ui — no introducidos en este incremento)
- `tsc --noEmit`: 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml` (consolidado, estado final del incremento): 0 CRITICAL, 103 advertencias, 90.6h de deuda técnica estimada (0h bloqueante)
- `architectanalyst src/ --sprint-id BL-003`: 4 críticos (Zone of Pain: `identidad`, `settings`, `shared` — mismos de `BL-002` — más `banco_preguntas`, nuevo este incremento), 6 warnings, `should_block: false` (`.cm/baselines/BL-003-arquitectura.json`, copia de `quality/reports/architectanalyst/BL-003-arquitectura.json`)

**UAT (`PROCEDIMIENTO-UAT.md`):**
- Iteración 1: `quality/reports/uat/inc2/design.md`/`evidencia.md` — Capa 1 + Capa 2 aprobadas, 3 no conformidades 🟡 Observación (ninguna 🔴 Bloqueante) → originan `SP-ADJ-01`
- Iteración 2: `quality/reports/uat/inc2/design-iter2.md`/`evidencia-iter2.md` — Capa 1 + Capa 2 aprobadas, sin no conformidades nuevas
- `SP-ADJ-01` y el ajuste UX en vivo verificados en navegador real (Chrome), sin hallazgos 🔴 Bloqueantes
- RF-03, RF-04, RF-05, RF-06, RF-19 pasan de Implementado a **Validado** en `docs/traceability/matrix.md`

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Merge `develop → main` y tag diferidos otra vez | Mismo ítem abierto que `BL-001`/`BL-002`: no hay Docker en el entorno de desarrollo local. Confirmado con Víctor al cerrar esta baseline (no se resuelve en este cierre). |
| Paginación opt-in en Banco de Preguntas, siempre aplicada en Cuentas | `US-ADJ-03`: `PreguntaRepositoryPort.filtrar()` es compartido por 5 pantallas, algunas necesitan el resultado completo sin paginar. `US-ADJ-05`: el listado de cuentas tiene un único consumidor a cada lado (verificado por grep), así que la paginación se aplicó siempre, con default fijo — sin el diseño opt-in de `US-ADJ-03`. |
| JWT/RBAC extraído a `shared` antes de que Banco de Preguntas lo necesitara | `ADR-019`/`US-2.1.1`: primera vez que un BC distinto de Identidad consume RBAC — se resolvió moviendo la lógica transversal a `shared/entities`+`frameworks/security`+`interface_adapters/security`, sin imports directos entre BCs. |
| CRITICAL de CBO recurrente en controllers, resuelto por separación command/query | Mismo patrón en `US-2.1.2`, `US-2.1.5`, `US-2.1.6` (resuelto separando `BancosController` de `PreguntasController` en `US-2.1.7`) y en `US-2.2.2` (resuelto con `CuentaQueryPort`/`SQLAlchemyCuentaQueryRepository` propios). No volvió a aparecer en las US siguientes que ya nacieron con esa separación. |
| Prototipo HTML manda sobre la spec escrita | Detectado en el ajuste UX en vivo (PR #120, login con cuenta bloqueada): la spec describía un layout que no coincidía con el prototipo aprobado — se corrigió el texto de la spec, no la implementación, y se preguntó a Víctor antes de asumir cuál era la fuente de verdad. |
| ArchitectAnalyst — 4to crítico "Zone of Pain" (`banco_preguntas`) | Mismo falso positivo de granularidad que `identidad`/`shared`/`settings` en `BL-002`: el BC nuevo mide D≈0.94 a nivel de paquete raíz por quedar fuera de las 4 capas que la herramienta reconoce como unidad de análisis. No amerita abstracciones artificiales — sigue pendiente el ajuste de umbrales propuesto en la retrospectiva de `BL-002`, todavía no aplicado. |

---

## Retrospectiva

### ¿Qué funcionó?

- La decisión de secuenciación (completar Iteración 2 entera → UAT → una sola iteración de
  ajuste conjunta) evitó fragmentar el trabajo en mini-iteraciones — `SP-ADJ-01` agrupó de
  una vez la deuda de UX y paginación de ambas iteraciones del incremento.
- El ajuste UX en vivo comparando cada pantalla contra su prototipo HTML en navegador real
  (no solo contra la spec escrita) encontró bugs reales que ninguna otra capa detectaba: el
  breadcrumb hardcodeado y, sobre todo, el problema de ancho de columnas que **solo apareció
  al cargar 60 preguntas reales** — los 3 fixtures mínimos del prototipo nunca lo hubieran
  revelado.
- La separación command/query (`CuentaQueryPort` en `US-2.2.2`) aplicada preventivamente en
  `US-2.2.3` evitó repetir el CRITICAL de CBO que ya había aparecido tres veces en la
  Iteración 1.

### ¿Qué fue más difícil de lo esperado?

- El ajuste de umbrales de `[tool.architectanalyst]` propuesto en la retrospectiva de
  `BL-002` no se aplicó — el mismo "Zone of Pain" de granularidad de paquete raíz volvió a
  aparecer, ahora con un 4to módulo (`banco_preguntas`). Sigue siendo un ajuste pendiente,
  no una decisión tomada.
- La UAT formal de Iteración 1 no capturó el bug de layout de la tabla del Banco (columna
  "Eliminar" cortada) porque se probó con fixtures mínimos — recién se manifestó semanas
  después, con datos reales de la materia "Ingeniería de Software" (70 preguntas de un
  `.docx`). La UAT formal no sustituye una prueba de volumen realista.
- El merge a `main`/tag de baseline sigue diferido por tercera vez consecutiva (`BL-001`,
  `BL-002`, ahora `BL-003`) — la decisión de infraestructura/Docker lleva más de un mes sin
  resolverse.

### ¿Qué ajustar en el próximo incremento?

- Aplicar de una vez el ajuste de umbrales de `ArchitectAnalyst` a nivel de paquete raíz
  (decisión pendiente desde `BL-002`), o documentar explícitamente que se acepta como falso
  positivo permanente de la herramienta para no seguir señalándolo baseline tras baseline
  sin acción.
- Incluir al menos un caso de prueba de UAT con volumen de datos realista (no solo fixtures
  mínimos) en el diseño de UAT formal (`quality/reports/uat/incN/design.md`), no solo en
  sesiones informales posteriores.
- Resolver la decisión de infraestructura/Docker antes de que el Incremento 3 (primer flujo
  de valor real con datos de estudiantes, según `PLAN_v1.md`) la vuelva bloqueante en vez de
  solo diferible.

---

*Creado: 2026-08-23*
