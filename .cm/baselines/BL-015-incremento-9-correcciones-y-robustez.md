# BL-015 — Incremento 9: Correcciones y robustez (`v0.10.0`)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento de correcciones y robustez (MINOR; incluye una funcionalidad nueva, el link de invitación grupal) |
| Fecha apertura | 2026-11-07 |
| Fecha cierre | 2026-11-09 |
| Git tag inicial | `v0.9.1` (`BL-014`) |
| Git tag cierre | `v0.10.0` |
| Milestone | [Incremento 9 — Correcciones y robustez](https://github.com/vvalotto/cognion/milestone/18) |
| Estado | ⚠️ Completado **sin UAT formal** (decisión de Víctor, 2026-11-09) — ver *UAT de cierre* |
| DoD | Correcciones de la prueba real con estudiantes en GCP, guardas de arquitectura en el CI, observabilidad mínima, adaptadores sin lectura de modelos ORM ajenos y el link de invitación grupal |

---

## Descripción

El incremento nace de **la prueba real con estudiantes sobre la VM de GCP (2026-11-06)**: el sistema aguantó (0 respuestas 5xx, 7
evaluaciones finalizadas, una sesión en vivo con 6 participantes), pero dejó hallazgos de uso, y de la deuda técnica pendiente de
`BL-012`/`BL-013`. Sin BC nuevo ni RF funcional nuevo. Un PR por iteración hacia `develop`.

- **Iteración 0 — Decisiones y spikes.** Sesión de decisiones (#593), `ADR-026` (acoplamiento entre BC por datos, #498) y spikes de la
  prueba real (#595 registro, #596 canal WebSocket). Sin código propio; sus conclusiones se implementaron en las iteraciones 1 y 2.
- **Iteración 1 — Correcciones con impacto en el uso real** (PR #599). `US-ADJ-68`: el log de acceso enmascara `/invitaciones/<token>`
  (#594). `US-ADJ-63`: el hash de contraseñas deja de bloquear el event loop (`hash_async`/`verificar_async` con ejecutor propio,
  #562). `US-8.3.4`: `alembic downgrade base` funciona y una guarda impide que vuelva el error (#527).
- **Iteración 2 — Link de invitación grupal** (PR #606). `US-ADJ-67`: invitación reutilizable con vencimiento de 15 min, 1 h o 1 día,
  revocable y con conteo de registros, que reemplaza a la individual en la UI (`ADR-027`, migración `f7a3c9d15e82`, #590).
  `US-ADJ-69`: el login avisa "te queda 1 intento" tras el 2.º fallo (#604, cierra #502). Correcciones de frontend de los spikes
  (#605): el registro exige y enfoca la política de contraseña y el canal en vivo detecta el JWT vencido.
- **Iteración 3 — Guardas de arquitectura y observabilidad** (PR #607). `import-linter` en el CI hace cumplir las capas y el
  aislamiento entre BC (#497). `US-8.3.3`: `GET /health/ready` y logs estructurados con `LOG_FORMAT=json` (#526).
- **Iteración 4 — Adaptadores sin modelos ORM ajenos** (PR #608, `ADR-026`). `US-9.4.1` (#600), `US-9.4.2` (#601) y `US-9.4.3` (#602):
  los tres adaptadores que leían modelos de otro BC pasan a usar puertos del proveedor; ya no queda ninguna excepción en
  `ignore_imports`. En `US-9.4.2` el método se puso en un puerto propio porque en `CuentaQueryPort` el CBO subía a 11.
- **Fuera del plan, ya en `develop`:** `lang="es"` y recreación del bloque de la pregunta en rendir evaluación, por la posible
  traducción automática del navegador (PR #591, sin confirmar con la estudiante afectada).

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D67 | `docs/specs/ajustes/US-ADJ-63.md`, `US-ADJ-67.md`, `US-ADJ-68.md`, `US-ADJ-69.md`, `docs/specs/inc8/US-8.3.3.md`, `US-8.3.4.md`, `docs/specs/inc9/US-9.4.1.md` a `US-9.4.3.md` | Documento | Especificaciones de las US del incremento |
| CI-D68 | `docs/plans/inc9/` (candidatas, contexto y plan por US), `docs/reports/inc9/` | Documento | Plan del incremento y reportes por US |
| CI-D69 | `docs/adr/ADR-026-acoplamiento-entre-bc-por-datos.md`, `docs/adr/ADR-027-invitacion-grupal.md`, nota en `ADR-012`, `BC-identidad-modelo.md` | Documento | Decisiones de arquitectura y modelo de Identidad |
| CI-C36 | `src/identidad/entities/invitacion.py`, casos de uso `*_invitacion_grupal`, `invitaciones_grupales_{controller,router}.py`, migración `f7a3c9d15e82_invitacion_grupal.py` | Código de backend | Link de invitación grupal (`US-ADJ-67`) |
| CI-C37 | `src/identidad/frameworks/security/password_hasher.py`, `PasswordHasherPort`, 8 casos de uso de Identidad | Código de backend | Hash de contraseñas asíncrono (`US-ADJ-63`) |
| CI-C38 | `src/shared/frameworks/logging_config.py`, `src/shared/frameworks/salud.py`, `src/app.py`, `deploy/gcp/salud.sh` | Código de backend | Enmascarado de token, logs JSON y readiness (`US-ADJ-68`, `US-8.3.3`) |
| CI-C39 | `src/identidad/entities/errors.py`, `iniciar_sesion.py`, router de login | Código de backend | Aviso del último intento (`US-ADJ-69`) |
| CI-C40 | `NombreUsuarioQueryPort` y su gateway, `EstudianteEvaluacionesQueryPort` y su gateway, `ComisionQueryPort.existe_comision_en_materia`, los tres adaptadores `*_port_in_process` | Código de backend | Adaptadores sin modelos ORM ajenos (`US-9.4.1` a `US-9.4.3`) |
| CI-C41 | `migrations/versions/dd44a181d7fc_estudiante_comision_id.py`, `tests/uat/inc8/verificar_migraciones.sh` | Migración / tooling | `downgrade base` funcional (`US-8.3.4`) |
| CI-F24 | `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx`, `frontend/src/pages/identidad/` (`InvitacionPreview`, `Registro`, `RegistroError`, `Login`, `LoginError`) y el canal en vivo | Código de frontend | Tarjeta de invitación grupal, motivos de error del registro, aviso de intento y JWT vencido |
| CI-T17 | `pyproject.toml` (`[tool.importlinter]`), `tests/unit/inc9/test_guarda_arquitectura.py`, CI | Tooling | Contratos de `import-linter` |
| CI-T18 | `quality/reports/designreviewer/BL-015-designreviewer.json`, `quality/reports/architectanalyst/BL-015-arquitectura.json`, `.cm/baselines/BL-015-arquitectura.json`, `quality/reports/inc9/` | Herramienta | Salidas de cierre de esta baseline |

---

## Métricas al cerrar

**Backend** (suite completa contra una base descartable, `DATABASE_URL` inline; `cognion`, `cognion_local` y `cognion_uat` no se tocaron):
- `pytest tests/unit tests/integration tests/step_defs --cov=src`: **2378 pasan**, 0 fallos (`BL-014`: 2169)
- `ruff check src/`: 0 violaciones · `mypy src/`: 0 errores (328 archivos) · `pylint src/`: **9.64/10** (`BL-014`: 9.63)
- Cobertura: **97.03 %** (`BL-014`: 97.22 %)
- `lint-imports`: **4 contratos cumplidos, 0 rotos**

**Frontend:** `npx vitest run`: **893 pasan** (112 archivos), 0 fallos (`BL-014`: 867) · `npx tsc -b`: 0 errores · `oxlint`: 0 errores,
solo advertencias de las reglas `react(refs)`/`set-state-in-effect`, ya presentes en `BL-014`.

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: **0 CRITICAL**, 377 advertencias sobre 328 archivos (`BL-014`: 362 sobre 315),
  `should_block: false`.
- `architectanalyst src --sprint-id BL-015 --config pyproject.toml`: 8 CRITICAL (`DistanceAnalyzer`, "Zone of Pain"), los mismos de
  `BL-014`. Falso positivo aceptado desde `US-ADJ-13`/`19` (`Ca=Ce=0`, `software_limpio#77`); `should_block: false`, sin acción.
  Además 11 advertencias (`GodPackageAnalyzer`, `RelationalCohesionAnalyzer`). `coverage.json` se generó antes de correrlo.

**Migraciones de esquema:** una nueva, `f7a3c9d15e82_invitacion_grupal` (3 columnas en `invitacion`, `downgrade` verificado), más la
corrección del `downgrade` de `dd44a181d7fc`. Total: 19 migraciones.

---

## UAT de cierre

**No se hizo UAT formal** (Capa 1 + Capa 2) **ni verificación en navegador real**, por decisión de Víctor del 2026-11-09. Lo que sí hay
como evidencia: la suite completa y los tests por US (incluidos escenarios BDD con `alembic` real, pruebas con un `uvicorn` real como
subproceso para el log y el readiness, y la caracterización de los tres adaptadores antes de migrarlos).

**No verificado** (queda como riesgo aceptado hasta la próxima prueba real):
- El flujo de invitación grupal de punta a punta en un navegador real y con celular: generar el link, copiarlo, registrarse varios
  estudiantes, vencimiento, desactivación, contador de registrados. Vitest con `fetch` mockeado no ve CORS, cascada CSS ni `AbortSignal`.
- El aviso "te queda 1 intento" en la pantalla de login.
- Las correcciones de frontend de #605 (registro con contraseña rechazada, canal en vivo con JWT vencido).
- El efecto de `US-ADJ-63` y de `lang="es"` bajo carga o en la VM de GCP (la prueba de carga de logins de `US-6.2.9` no se repitió).
- El despliegue: `v0.10.0` no se desplegó a la VM.

---

## Actualización de la matriz de trazabilidad

Sin cambios de estado de RF: ajustes y robustez sobre RF ya `Validado` (Identidad, registro por invitación y login). El
link grupal amplía el registro por invitación sin agregar filas. Como no hubo UAT, **ningún RF ni RNF pasa a `Validado` con esta baseline**.

---

## Pendiente que queda abierto

- [#597](https://github.com/vvalotto/cognion/issues/597) `US-9.0.3`: spike de memoria y swap de la VM con una clase completa. Necesita
  la VM de GCP, que hoy no existe, y medir después de `US-ADJ-63`.
- [#496](https://github.com/vvalotto/cognion/issues/496): corregir `DependencyGraphBuilder` upstream (`software_limpio#77`) y reactivar
  `LayerViolationsAnalyzer`. Depende de un arreglo en otro repositorio; `import-linter` cubre la regla mientras tanto.
- Nube (Iteraciones 2 y 3 del Incremento 8), `RF-07` (PDF) y `RF-18` (KPIs): sin cambios.
- Una pasada UAT del incremento queda recomendada antes de la próxima prueba con estudiantes.

---

## Retrospectiva

- **Lo que funcionó:** una rama y un PR por iteración; el test de caracterización antes de cada migración; medir el CBO a mano en la
  Fase 7 (en `US-9.4.2` evitó que el CRITICAL apareciera recién en el pre-push).
- **Lo que costó:** el PostgreSQL local de Homebrew no arranca desde el 2026-11-09 (`postmaster.pid` viejo, el PID 912 ahora es otro
  proceso); toda la integración corrió en clusters descartables fuera del repo. Es una falla del entorno, no del código, y hay que
  arreglarla antes de la próxima UAT.
- **Decisión de proceso a revisar:** cerrar una baseline sin UAT contradice la regla vigente de `CLAUDE.md` ("Debe aprobar antes de merge
  a main"). Se hizo por pedido expreso, y queda documentado arriba.
