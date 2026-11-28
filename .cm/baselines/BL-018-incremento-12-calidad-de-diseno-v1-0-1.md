# BL-018 — Incremento 12: Calidad de diseño, Iteraciones 1 y 2 (`v1.0.1`)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento de calidad (PATCH: sin funcionalidad nueva; tres endurecimientos de seguridad y operación declarados) |
| Fecha apertura | 2026-11-15 |
| Fecha cierre | 2026-11-28 |
| Git tag inicial | `v1.0.0` (`BL-016`) |
| Git tag cierre | `v1.0.1` |
| Milestone | [Incremento 12 — Calidad de diseño](https://github.com/vvalotto/cognion/milestone/21) (16 Issues cerrados, 0 abiertos; **queda abierto hasta `BL-019`/`v1.1.0`**, que cierra las Iteraciones 3 y 4) |
| Estado | ✅ Completado, con límites declarados en *No verificado* |
| DoD | Hallazgos de la revisión de diseño de las Iteraciones 1 y 2 cerrados con evidencia; suite, calidad y seguridad sin regresión respecto de `BL-016`; UAT de regresión sin hallazgos 🔴 |

---

## Descripción

Primera entrega del **Incremento 12 — Calidad de diseño**, que se ejecuta antes que el 11 (Mejoras funcionales) por la congelación funcional del 2026-11-15: no entra funcionalidad nueva a `develop` hasta tener una versión estable con las mejoras de la revisión de diseño (`docs/revision-diseno-2026-11/`). Sin BC ni RF nuevos. Una rama y un PR por historia.

- **Iteración 1 — Cierres rápidos y operación** (Issues #645 a #649, #654, #658; cerrada el 2026-11-18). `US-12.1.1`: el canal en vivo solo lo abre quien pertenece a la comisión (`IM-04`). `US-12.1.2`: unirse, consultar el estado y ver el ranking de la sesión en vivo exigen pertenecer a la comisión. `US-12.1.3`: el token de sesión pasa de 1 a 8 horas (`AQ-04`). Operación (`DO-01`, `DO-02`, `DO-04`, `DO-05`): respaldo programado y vigilado, imagen sin privilegios y con `uv` fijo, healthcheck contra `/api/health/ready`, `fly.toml` borrado. Herramientas (`CA-02`, `IQ-04`, `IQ-05`, `IQ-06`, `VT-03`): una versión de Python, `tsc -b` y auditoría de dependencias en el CI, hook de push, base de tests protegida. Documental (`DC-01`, `DC-02`): `README.md` y `CLAUDE.md`.
- **Iteración 2 — Los bordes de cada contexto** (Issues #665 a #673; cerrada el 2026-11-28). Red de seguridad (cobertura de `frameworks/`, Playwright, smoke del servidor) y guardas con lista de excepciones que no pueden crecer; `ADR-028` a `ADR-031`. `US-12.2.1` (`ADR-028`): una unidad de trabajo por pedido. `US-12.2.2` (`ADR-029`): errores de dominio con categoría y un único manejador. `US-12.2.3` (`ADR-030`): repositorios SQL en `frameworks/repositories/`. `US-12.2.4` (`ADR-031`): los controllers devuelven un tipo de salida armado en presentadores y los routers no leen entidades. `US-12.2.5`: el motor de base sale de la configuración (pool en ejecución, `NullPool` en los tests; `ADR-018` enmendado) y el verificador toma un bloqueo para correr una sola vez (`IM-05`). `US-12.2.6`: `max_cbo = 12` medido sin atajos y fijado por una guarda.
- **Arreglo asociado** (PR #687): una carrera entre el estado de React y su referencia en `SesionEnVivoEstudiante.tsx` causaba una falla intermitente de Playwright.

Las **Iteraciones 3** (Los eventos) y **4** (Las fronteras entre contextos), que cierran con `BL-019` y `v1.1.0`, siguen pendientes y no forman parte de esta baseline.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D72 | `docs/specs/inc12/`, `docs/plans/inc12/`, `docs/reports/inc12/`, `docs/revision-diseno-2026-11/` | Documento | Specs, planes, reportes de cada historia y la revisión de diseño que origina el incremento |
| CI-D73 | `docs/adr/ADR-028` a `ADR-031`, `ADR-018` (enmendado), `ADR-013` (enmendado), `CHANGELOG.md` (`[1.0.1]`) | Documento | Decisiones de los bordes de cada contexto y notas de la versión |
| CI-C43 | `src/shared/`, `src/<bc>/entities/errors.py`, `src/<bc>/frameworks/repositories/`, `src/<bc>/interface_adapters/presenters/`, `src/app.py` | Código de backend | Unidad de trabajo, errores categorizados con manejador único, repositorios, presentadores, motor de base y bloqueo del verificador |
| CI-T23 | `tests/unit/inc12/`, `tests/integration/inc12/`, `tests/uat/inc12/` | Tests | Guardas de arquitectura con excepciones, pool, un solo proceso, presentadores; scripts de Capa 2 (regresión y autorización) |
| CI-T24 | `scripts/calidad.sh`, `.githooks/`, `.github/workflows/ci.yml`, `Dockerfile`, `deploy/servidor/` | Tooling | Script único de calidad, hook de push, CI con auditoría y Playwright, imagen endurecida y respaldo programado |
| CI-T25 | `quality/reports/designreviewer/BL-018-designreviewer.json`, `quality/reports/architectanalyst/BL-018-arquitectura.json`, `.cm/baselines/BL-018-arquitectura.json`, `quality/reports/uat/inc12/` | Herramienta | Salidas de cierre de esta baseline y evidencia del UAT |

---

## Métricas al cerrar

**Backend** (suite completa contra la base descartable `cognion_bl018_test`, migrada a `head`; `cognion`, `cognion_local` y `cognion_uat` no se tocaron). Dos corridas independientes, ambas limpias:
- `pytest tests --cov=src`: **2831 pasan**, 1 omitido, 0 fallos (`BL-016`: 2459); segunda corrida sin cobertura: 2831 pasan, 1 omitido
- `ruff check src/`: 0 violaciones · `mypy src/`: 0 errores (351 archivos) · `pylint src/`: **9.58/10** (`BL-016`: 9.64; baja de 0,06, causa no analizada)
- Cobertura: **96.72 %** (`BL-016`: 97.03 %)
- `lint-imports`: **9 contratos cumplidos, 0 rotos** (`BL-016`: 4)
- `pip-audit` (dependencias de producción): sin vulnerabilidades conocidas

**Frontend:** `vitest run`: **894 pasan** (112 archivos; `BL-016`: 893) · `tsc -b`: 0 errores · `oxlint`: 0 errores y 51 advertencias, las mismas 51 de `v1.0.0` (`react(refs)`/`set-state-in-effect`) · `npm audit`: 0 vulnerabilidades.

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: **0 CRITICAL**, 346 advertencias sobre 351 archivos (`BL-016`: 377 sobre 329), `should_block: false`.
- `architectanalyst src --sprint-id BL-018 --config pyproject.toml`: 8 CRITICAL (`DistanceAnalyzer`, "Zone of Pain"), los mismos de `BL-016`; falso positivo aceptado desde `US-ADJ-13`/`19` (`software_limpio#77`). 11 advertencias. `should_block: false`. `coverage.json` se generó antes.

**Migraciones de esquema:** ninguna nueva (19 en total).

**Rendimiento (Mac, 30 logins simultáneos):** 1,51 s con pool contra 2,90 s sin pool en `BL-016`; `/health` durante la ráfaga, mediana 8 ms y máximo 107 ms.

---

## UAT de cierre

UAT de regresión sobre `develop` (`quality/reports/uat/inc12/report.md`, diseño en `design.md`), en un servidor instalado con `scripts/local/levantar.sh` y el pool real:

- **Capa 1:** la suite completa, dos corridas.
- **Capa 2 HTTP/WebSocket:** `capa2_http.py` 27/27, `capa2_regresion.py` 21/21 (60 estudiantes, 60 respuestas casi simultáneas) y `capa2_autorizacion.py` 22/22 (dos comisiones: miembros y ajenos frente a la sesión en vivo y su canal; vencimiento del token).
- **Navegador:** docente (Banco, edición de una pregunta, Reportes) en escritorio; estudiante a 375 px emulados (login, sesión en vivo completa, pantalla de registro). Sin errores de consola; todas las llamadas 200.
- Sin hallazgos 🔴. Una observación 🟡 (H-1): un `.env` viejo que fije `ACCESS_TOKEN_EXPIRE_MINUTES=60` pisa el nuevo valor por defecto de 480; se documenta en el `CHANGELOG`.

**No verificado** (riesgo aceptado):
- **Servidor con dominio, certificado y firewall** (Issue #624): el smoke del CI ejercita Docker real en `localhost`, pero la medición del pool y la carga se hicieron en la Mac, no en un servidor.
- **Celular real:** el recorrido del estudiante se hizo con un viewport emulado de 375 px.
- **Falla intermitente de integración sin identificar:** una corrida parcial (inc3, inc5, inc6) tuvo un fallo una sola vez bajo carga; no volvió a aparecer en tres corridas completas posteriores. Si reaparece, se investiga con el log completo.
- **Secuencias de runtime** de `docs/architecture/30-runtime-interactions.md`: no se ejecutaron.
- **Alta de estudiante enviando el formulario a mano:** el navegador mostró la pantalla de registro y su medidor de contraseña; el alta se cubrió por HTTP (60 registros).
- **`.env` de desarrollo de esta máquina:** sigue con `ACCESS_TOKEN_EXPIRE_MINUTES=60`; es un archivo local no versionado.
- **Job `release` del CD e imagen `ghcr.io/vvalotto/cognion:v1.0.1`:** se ejecutan recién con el tag.

---

## Actualización de la matriz de trazabilidad

Sin cambios de estado de ningún RF ni RNF. La cabecera de `docs/traceability/matrix.md` registra el cierre. Los escenarios de calidad de `RNF_v1.md` afectados (administrabilidad y seguridad de la sesión en vivo) se siguen leyendo en `docs/architecture/70-trazabilidad-rnf-vistas.md`.

---

## Pendiente que queda abierto

- **Iteraciones 3 y 4 del Incremento 12** (Milestone 21): llevan a `BL-019` y `v1.1.0`; sus Issues se crean al abrir cada una.
- `DM-04` ("Limitación conocida"): único hallazgo de las Iteraciones 1 y 2 que no se cerró.
- [#624](https://github.com/vvalotto/cognion/issues/624): ensayo del camino del servidor con Docker real en un servidor con dominio.
- [#496](https://github.com/vvalotto/cognion/issues/496): `DependencyGraphBuilder` upstream (`software_limpio#77`); `import-linter` cubre la regla mientras tanto.
- **Incremento 11 — Mejoras funcionales** (#616 a #619): postergado; pasa a apuntar a `v1.2.0`.
- Nube (Iteraciones 2 y 3 del Incremento 8): sin cambios.

---

## Retrospectiva

- **Lo que funcionó:** refactors con red de seguridad previa (cobertura de `frameworks/`, Playwright, snapshot de OpenAPI y guardas con listas de excepciones que no pueden crecer); separar un controller por responsabilidad command/query cuando el CBO lo pedía, en vez de esquivar la métrica.
- **Lo que costó:** mi primer diseño de UAT decía que las Iteraciones 1 y 2 eran invisibles desde afuera; era falso para la Iteración 1 (autorización y token), y se corrigió al repasar los merges desde `v1.0.0` antes de redactar las notas. También: tras una pausa larga hubo que recrear PostgreSQL por un `postmaster.pid` obsoleto, y la primera corrida completa se contaminó al correr Vitest en paralelo con la suite.
- **Decisión de proceso:** la lista de cambios observables de una versión se arma desde los merges desde el tag anterior, no desde el nombre de la iteración; y las verificaciones pesadas (suite completa, frontend) no se corren en paralelo.
