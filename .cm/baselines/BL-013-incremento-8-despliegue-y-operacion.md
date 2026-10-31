# BL-013 — Incremento 8: Despliegue y operación (versión local `v0.9.0`)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento (fuera de la secuencia numérica de `PLAN_v1.md`; sin RF funcional propio) |
| Fecha apertura | 2026-10-16 |
| Fecha cierre | 2026-10-31 |
| Git tag inicial | `v0.8.1` (`BL-012`) |
| Git tag cierre | `v0.9.0` (MINOR, decisión de Víctor: primera versión instalable y operable por un docente en su propia máquina) |
| Estado | ✅ Completado — mergeado a `develop` (PR #578) y a `main`; tag `v0.9.0` aplicado el 2026-10-31 |
| DoD | Un docente puede instalar Cognión en su Mac con un comando, cargar sus materias y preguntas desde archivos, operar clases con alumnos en la red local (incluida la sesión en vivo con celulares), respaldar y restaurar los datos, y todo eso verificado en una UAT sobre una instalación limpia, sin hallazgos bloqueantes abiertos |

---

## Descripción

Incremento sin BC nuevo ni RF funcional nuevo: lo que faltaba para **instalar y operar** el producto fuera
del entorno de desarrollo. Su alcance cambió dos veces por decisiones de Víctor y esta baseline cierra lo
efectivamente hecho:

- **Plan original (2026-10-16):** producción en Fly.io (`ADR-021`), backup mensual a Google Drive (`ADR-022`),
  SMTP por materia (`ADR-023`), dominio `fly.dev` (`ADR-024`).
- **2026-10-17, standby de la nube:** `fly postgres` está deprecado y Managed Postgres cuesta unos 38 USD/mes;
  se espera saber si se puede usar el convenio de la Universidad con Google. `ADR-021` y `ADR-024` pasan a
  *En revisión*. Se ejecuta en su lugar el **despliegue local**.
- **2026-10-24, nube en pausa:** se probó un despliegue en una VM gratuita de GCP con la cuenta personal de
  Víctor (`ADR-025`); se verificó de punta a punta y se destruyó para no generar costo. **La primera versión de
  producción corre en la Mac de Víctor, sin nube**, y después se usará temporalmente su GCP.

**Iteraciones cerradas**
- **0 — Decisiones** (PR #533): `ADR-021` a `ADR-024`.
- **1 — Artefacto desplegable** (`US-8.1.1` a `8.1.7`, PR #535): CORS configurable, URL base resuelta en el build,
  `ENTORNO` con validación que falla al arrancar, migraciones como `release_command`, `bootstrap_administrador`,
  `src/servidor.py` (frontend + API bajo `/api`) y cuentas SMTP por materia.
- **5 — Despliegue local** (`US-8.5.1` a `8.5.4`, PR #544): `scripts/local/` (`levantar`, `detener`, `respaldar`,
  `restaurar`), `ENTORNO=local`, `EMAIL_MODO=consola`, guía `DESPLIEGUE-LOCAL.md`. `US-8.5.5` a `8.5.7`
  desestimadas por Víctor.
- **6 — Despliegue de prueba en GCP** (parcial, PR #559 y #563): `US-8.6.1` (`ADR-025`), `US-8.6.2` (composición
  en `deploy/gcp/`), `US-8.6.3` (plan ejecutado a mano, bitácora en `quality/reports/uat/inc8-gcp/`), `US-8.6.4`
  (`aprovisionar.sh`, `destruir.sh`, `desplegar.sh`, `cognion.sh desplegar|rollback`, imagen en GHCR por etiqueta).
- **7 — Versión local** (`US-8.7.1`, PR #565; `US-8.7.2`, UAT, PR #568): comando `cargar_datos_iniciales`; UAT sobre
  una instalación limpia con Mac, iPad e iPhone.
- **8 — Ajustes de la UAT** (PR #572 plan, PR #578, 26 commits): `US-ADJ-64` (logging), `US-ADJ-65` (contraseña
  del Administrador confirmada) y los arreglos informales de los hallazgos #1, #4, #5, #6, #7 y #10.

**Diferido** (17 Issues, ahora en el Milestone "Incremento 8 — Despliegue en la nube (diferido)"): despliegue
automático, staging y rollback de esquema (`US-8.2.x`), backup automático y restauración (`US-8.3.x`), guía,
runbook y ensayo en el entorno final (`US-8.4.x`), `US-8.6.3` (costo real de la IP), `US-8.6.5` a `8.6.8` y
`US-ADJ-63` (el hash bcrypt bloquea el event loop).

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D60 | `docs/adr/ADR-021` a `ADR-025` | Documento | Decisiones de despliegue (`021` y `024` en revisión; `025` aceptado) |
| CI-D61 | `docs/specs/inc8/` (`US-8.1.1` a `8.7.1`), `docs/specs/ajustes/US-ADJ-63.md` a `US-ADJ-65.md` | Documento | Specs del incremento |
| CI-D62 | `docs/reports/inc8/` | Documento | Reportes de cierre de `/implement-us` (`US-8.1.x`, `8.5.x`, `8.6.2`, `8.6.4`, `8.7.1`, `US-ADJ-64`, `US-ADJ-65`) |
| CI-D63 | `docs/plans/inc8/`, `docs/plans/DESPLIEGUE-LOCAL.md`, `docs/plans/DESPLIEGUE-GCP.md`, `docs/plans/ejemplos/` | Documento | Plan del incremento, guía de instalación local y plan de la prueba en GCP |
| CI-D64 | `quality/reports/uat/inc8/` (`plan-de-pruebas`, `registro-ejecuciones`, `registro-hallazgos`, `plan-de-correccion`), `quality/reports/uat/inc8-gcp/` | Documento | UAT de la versión local y bitácora de la prueba en GCP |
| CI-D65 | `docs/design/ux/wireframes-banco-preguntas.md` §2.3.1, `wireframes-actividad-evaluativa*.md`, `wireframes-identidad*.md` y los prototipos HTML | Documento | Regla Unidad → Tema y "Repetir email" (gate UX aprobado) |
| CI-C30 | `src/servidor.py`, `src/settings.py`, `src/shared/frameworks/{smtp,logging_config}.py`, `src/app.py` | Código de backend | Servidor único, configuración por entorno, SMTP por materia y logging con tokens enmascarados |
| CI-C31 | `src/banco_preguntas/{use_cases/cargar_datos_iniciales.py,interface_adapters/importadores/,frameworks/cli/}` | Código de backend | Carga de datos iniciales desde JSON y Markdown |
| CI-C32 | `src/identidad/frameworks/cli/bootstrap_administrador.py` | Código de backend | Primer Administrador, con contraseña confirmada |
| CI-C33 | `scripts/local/`, `deploy/gcp/`, `.github/workflows/{cd,imagen-smoke}.yml`, `Dockerfile` | Tooling | Despliegue local, scripts de GCP y publicación en GHCR |
| CI-F22 | `frontend/src/lib/{config,fechas,unidad-tema,emails}.ts`, páginas de banco, actividad, sesión en vivo y registros, `frontend/public/` (favicon e ícono) | Código de frontend | URL de API por build, fechas con zona, regla Unidad → Tema, Repetir email, favicon |
| CI-T15 | `quality/reports/designreviewer/BL-013-designreviewer.json`, `.cm/baselines/BL-013-arquitectura.json` | Herramienta | Salidas de cierre de esta baseline |

---

## Métricas al cerrar

**Backend** (suite completa contra base descartable, `DATABASE_URL` inline; las bases `cognion`, `cognion_local` y
`cognion_uat` no se tocaron):
- `pytest tests/unit tests/integration tests/step_defs --cov=src`: **2151 pasan** (2150 en la corrida completa más
  `test_rechazo_fuera_del_período_vigente`, inestable y corregido el mismo día, 3 de 3 verdes)
- `ruff check src/`: 0 violaciones · `mypy src/`: 0 errores (315 archivos) · `pylint src/`: 9.61/10 (`BL-012`: 9.59)
- Cobertura: **97.09 %** (5269/5427 statements; `ArchitectAnalyst.CoverageAnalyzer`: 97.1 %)

**Frontend:**
- `npx vitest run --coverage`: **867 pasan** (112 archivos), 0 fallos · `npx tsc -b`: 0 errores · `oxlint`: 0 errores
- Cobertura: 93.78 % statements / 86.24 % branches / 90.96 % functions / 96.53 % lines

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: **0 CRITICAL**, 362 advertencias sobre 315 archivos (`BL-012`: 334
  sobre 303), `should_block: false`
- `architectanalyst src --sprint-id BL-013 --config pyproject.toml`: 8 CRITICAL (`DistanceAnalyzer`, "Zone of
  Pain"), uno por paquete raíz: los 7 de siempre más **`servidor`** (`src/servidor.py`, nuevo en este incremento).
  Mismo falso positivo aceptado desde `US-ADJ-13`/`19` (`Ca=Ce=0` para todo el proyecto por el bug de
  `DependencyGraphBuilder`, `software_limpio#77`); `should_block: false`, sin acción.

**Migraciones de esquema:** ninguna en este incremento.

---

## UAT de cierre

UAT sobre una instalación limpia (`cognion_uat`, `levantar.sh`), en la Mac y con iPad e iPhone, ejecutada por
Víctor el 2026-10-25 y repetida en lo afectado el 2026-10-28 y 2026-10-31 (`quality/reports/uat/inc8/`, PR #568).
Pasaron la instalación con un comando, la siembra de las 340 preguntas de Gestión de Proyectos (comparadas una a
una con los archivos de origen: 0 diferencias), el alta de actores, el período abierto con pausa y reanudación,
los reportes, la sesión en vivo, el RBAC y el respaldo con ensayo de restauración. **10 hallazgos**, todos
resueltos o reclasificados antes de etiquetar:

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| 2 | `EMAIL_MODO=consola` no escribía nada en el log | 🔴 | `US-ADJ-64` |
| 7 | Las fechas de una actividad se guardaban corridas 3 h (hora local tomada como UTC) | 🔴 | Informal, frontend |
| 8 | El iPhone tardaba segundos en mostrar las opciones de la sesión en vivo | 🔴→🟡 | **Causa: la VPN de Norton del celular, no el servidor**; advertencia en la guía |
| 9 | El log de acceso guardaba JWT e invitaciones completos | 🟡 | `US-ADJ-64` |
| 3 | `bootstrap_administrador` pedía la contraseña una sola vez | 🟡 | `US-ADJ-65` |
| 4 | El link de invitación usa la dirección con la que se abrió la aplicación | 🟡 | Advertencia en la guía |
| 6 | Unidad temática y Tema independientes, sin "Todos" | 🟡 | Regla Unidad → Tema (wireframes aprobados) |
| 1, 5, 10 | Título de pestaña, autoregistro sin "Repetir email", respaldos de dos bases mezclados | ⚪ | Informales |

---

## Actualización de la matriz de trazabilidad

Sin cambios: el incremento no implementa ni valida ningún RF (todo es instalación, operación y ajustes sobre RF ya
`Validado`).

---

## Retrospectiva

**Lo que funcionó**
- **Una UAT sobre una instalación real encontró lo que ningún test automático había visto**: el logging sin
  configurar, las fechas corridas por la zona horaria y la VPN del celular. Los tres convivían con 2000 tests en
  verde. Mismo patrón que en Identidad y Banco de Preguntas: lo que se mockea no se ve.
- **Probar con el proceso de verdad**: los tests nuevos de logging arrancan un `uvicorn` real y los de la contraseña,
  una terminal real (`pty`); sin los arreglos fallan, que es lo que se espera de un test de regresión.
- **Comparar dispositivos antes de culpar al servidor**: el iPad funcionaba y el iPhone no; eso acotó el problema al
  celular y llevó a la VPN, en vez de tocar `src/`.
- **Plan antes de scripts**: ejecutar a mano el plan de GCP y escribir los scripts después (`US-8.6.4`) hizo que los
  scripts nacieran de comandos que ya funcionaron; la verificación real encontró dos defectos (RDP abierto, presupuesto
  duplicado) que los tests con `gcloud` simulado no habían visto.

**Lo que costó**
- **`caplog` pasó por una verificación**: la `US-8.5.2` se cerró con un test que capturaba el mensaje aunque el
  servidor real nunca lo mostrara. La lección quedó en `US-ADJ-64`: un comportamiento de proceso se prueba en el proceso.
- **Una afirmación mía fue incorrecta**: informé que una extensión de plazo "no había llegado" consultando la base
  antes de que el usuario terminara de guardar. Se corrigió y quedó registrado; la verificación contra una base viva
  se hace después de la acción, no durante.
- **Pruebas largas con la máquina cargada**: una corrida completa de Vitest se abortó por "no se pudo arrancar un
  worker" y dejó 13 archivos sin ejecutar; se repitió con menos procesos en paralelo. Un resultado parcial no es
  evidencia.
- **Un test con una ventana de 1 segundo** (`test_rechazo_fuera_del_período_vigente`) estaba señalado desde la
  Iteración 3 del Incremento 3 y recién se corrigió ahora: creaba un estudiante (hash lento) dentro de la ventana.
- **El alcance cambió dos veces** (nube, luego GCP, luego local): cada cambio fue decisión de costo o de convenio,
  no técnica. El resultado es que `US-8.4.3` ("cierre BL-013") quedó con un título que ya no describe esta baseline.

---

## Pendientes que arrastra

- **Borrar la versión de prueba del paquete GHCR** (`v0.0.1-prueba.1`, id 1439899604): GitHub no deja borrar la última
  con etiqueta; se hace con `gh api -X DELETE` ahora que existe `v0.9.0`.
- **Elegir nube o seguir local**: depende de que se resuelva el convenio de la Universidad con Google (`ADR-021`,
  `ADR-025`). Hasta entonces la versión de producción es la local.
- **Probar con alumnos**: la red del aula (puede aislar clientes) y la carga de muchos alumnos a la vez siguen sin
  probar (`DESPLIEGUE-LOCAL.md` §11). Los datos de los alumnos quedan en el equipo del docente.
- **Cuentas SMTP institucionales** para un envío real de emails (`ADR-023`); en local los emails salen por consola.
- **Tarifa de salida de red de GCP** sin confirmar.
- Si se retoma la nube: `US-ADJ-63` antes de las mediciones de `US-8.6.7`.

## Issues abiertos al cerrar (deuda y decisiones para más adelante)

17 Issues, todos en el Milestone "Incremento 8 — Despliegue en la nube (diferido)": `#520` a `#524` (CD, staging,
rollback, checkpoint del RNF y backup, bloqueados por la decisión de nube), `#525` a `#527` (restauración,
observabilidad, `downgrade`), `#528` a `#530` (guía, runbook y ensayo en el entorno final), `#547` y `#549` a `#552`
(prueba en GCP: costo, backup, runbook, mediciones, prueba de uso) y `#562` (`US-ADJ-63`).
Fuera del incremento siguen abiertos `#496` a `#498`, `#500` a `#502` (deuda) y `#532` (RF-07).

## Próximo paso

Elegir entre: (1) la **Iteración 2 del Incremento 7** (RF-07, importación desde PDF), con su spike de decisión
entre parseo automático y asistido pendiente; (2) **RF-18** (KPIs históricos), diferido sin incremento; (3) **probar
con alumnos** la versión local en el aula; (4) retomar la **nube** cuando se resuelva el convenio.
