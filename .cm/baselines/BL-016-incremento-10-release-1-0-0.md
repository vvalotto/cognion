# BL-016 — Incremento 10: Release 1.0.0 (`v1.0.0`)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento de release (MAJOR: primera versión estable; sin funcionalidad nueva de producto) |
| Fecha apertura | 2026-11-10 |
| Fecha cierre | 2026-11-11 |
| Git tag inicial | `v0.10.0` (`BL-015`) |
| Git tag cierre | `v1.0.0` |
| Milestone | [Incremento 10 — Release 1.0.0](https://github.com/vvalotto/cognion/milestone/20) |
| Estado | ✅ Completado, con límites declarados en *No verificado* |
| DoD | Versión única, paquete de instalación por versión, instalación en servidor Linux con Docker (con respaldo mínimo), local sin Docker y GCP, y una guía única; UAT de estabilidad de la `v0.10.0` y ensayo de instalación limpia en la Mac |

---

## Descripción

Congela el trabajo de los Incrementos 0 a 9 en una **versión estable** y arma lo necesario para instalarla. Sin BC ni RF nuevos. Un PR por iteración hacia `develop`.

- **Iteración 1 — UAT de estabilidad** (`US-10.1.1`, PR #625, #620). Capa 2 HTTP 27/27 y 30 logins simultáneos sobre la `v0.10.0`; sin hallazgos 🔴 y una observación 🟡 (H-1, el link usa `window.location.origin`, documentada en la guía). La prueba en un celular real se **desestimó** por decisión de Víctor.
- **Iteración 2 — Empaquetado** (PR #626). `US-10.2.1` (#621): archivo `VERSION` como fuente única, `/api/health` informa `version`, el CD verifica que el tag coincida y el job `release` publica la GitHub Release con el paquete. `US-10.2.2` (#622): `deploy/servidor/` (compose, Caddy, `cognion.sh`, `respaldar.sh`, `restaurar.sh`) y `docs/INSTALACION.md`.
- **Iteración 3 — Ensayo de instalación** (`US-10.3.1`, PR #627, #623). Instalación limpia en la Mac sin Docker siguiendo solo la guía: Capa 2 27/27, respaldo, restauración real y actualización conservando datos. Hallazgo 🟡: la guía omitía el paso del `.env` (corregido).

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D70 | `docs/specs/inc10/US-10.2.1.md`, `US-10.2.2.md`, `docs/plans/inc10/`, `docs/reports/inc10/`, `quality/reports/uat/inc10/` | Documento | Specs, planes, reportes y evidencia de UAT y del ensayo de instalación |
| CI-D71 | `docs/INSTALACION.md`, `CHANGELOG.md` (`[1.0.0]`) | Documento | Guía única de instalación y notas de la versión |
| CI-C42 | `VERSION`, `src/shared/frameworks/version.py`, `src/app.py`, `Dockerfile` | Código de backend | Versión única e informada en `/api/health` |
| CI-T19 | `.github/workflows/cd.yml`, `scripts/extraer_notas.sh`, `scripts/empaquetar_release.sh` | Tooling | Verificación tag/`VERSION`, Release y paquete |
| CI-T20 | `deploy/servidor/` | Tooling | Servidor Linux con Docker, Caddy y respaldo mínimo |
| CI-T21 | `tests/unit/inc10/`, `tests/uat/inc10/` | Tests | Tests de versión, empaquetado y servidor; scripts de UAT |
| CI-T22 | `quality/reports/designreviewer/BL-016-designreviewer.json`, `quality/reports/architectanalyst/BL-016-arquitectura.json`, `.cm/baselines/BL-016-arquitectura.json` | Herramienta | Salidas de cierre de esta baseline |

---

## Métricas al cerrar

**Backend** (suite completa contra la base descartable `cognion_bl016`, migrada a `head`; `cognion`, `cognion_local` y `cognion_uat` no se tocaron):
- `pytest tests/unit tests/integration tests/step_defs --cov=src`: **2459 pasan**, 0 fallos (`BL-015`: 2378)
- `ruff check src/`: 0 violaciones · `mypy src/`: 0 errores (329 archivos) · `pylint src/`: **9.64/10** (`BL-015`: 9.64)
- Cobertura: **97.03 %** (`BL-015`: 97.03 %)
- `lint-imports`: **4 contratos cumplidos, 0 rotos**

**Frontend:** `vitest run`: **893 pasan** (112 archivos) · `tsc -b`: 0 errores · `oxlint`: 0 errores, solo las advertencias `react(refs)`/`set-state-in-effect` ya presentes. Sin cambios de código de frontend en este incremento.

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: **0 CRITICAL**, 377 advertencias sobre 329 archivos (`BL-015`: 377 sobre 328), `should_block: false`.
- `architectanalyst src --sprint-id BL-016 --config pyproject.toml`: 8 CRITICAL (`DistanceAnalyzer`, "Zone of Pain"), los mismos de `BL-015`; falso positivo aceptado desde `US-ADJ-13`/`19` (`software_limpio#77`). 11 advertencias. `should_block: false`. `coverage.json` se generó antes.

**Migraciones de esquema:** ninguna nueva (19 en total).

---

## UAT de cierre

UAT de estabilidad sobre la `v0.10.0` (`US-10.1.1`, `quality/reports/uat/inc10/report.md`) y ensayo de instalación limpia de la `1.0.0` en la Mac sin Docker (`US-10.3.1`, `quality/reports/uat/inc10/ensayo-instalacion-mac.md`). Ambos por HTTP, más el recorrido en navegador de la `v0.10.0` descripto en el primer informe.

**No verificado** (riesgo aceptado):
- **Camino del servidor Linux con Docker** (`deploy/servidor/`): probado con un `docker` y un `curl` simulados, **no contra Docker real** (#624, backlog).
- **Celular real:** desestimado por decisión de Víctor; el registro se probó con viewport emulado.
- **Canal en vivo con JWT vencido** (#605): solo cubierto por tests automáticos.
- **Job `release` del CD:** no se ejecutó hasta que exista el primer tag `v1.0.0` (si falla, se puede reejecutar sobre el mismo tag).
- **Imagen `ghcr.io/vvalotto/cognion:v1.0.0`:** se publica recién con el tag.
- **Ensayo local:** la actualización se simuló cambiando `VERSION` en la misma carpeta; el rol de PostgreSQL fue el del ejemplo; no hubo navegador ni celular en el ensayo.

---

## Actualización de la matriz de trazabilidad

Sin cambios de estado de RF ni RNF. La cabecera de `docs/traceability/matrix.md` registra el cierre.

---

## Pendiente que queda abierto

- [#624](https://github.com/vvalotto/cognion/issues/624): ensayo del camino del servidor con Docker real (backlog, sin Milestone).
- [#496](https://github.com/vvalotto/cognion/issues/496): `DependencyGraphBuilder` upstream (`software_limpio#77`); `import-linter` cubre la regla mientras tanto.
- **Incremento 11 — Mejoras funcionales** (v1.1.0): #616 a #619. `RF-07` pasa a importación desde JSON; `RF-18` sigue diferido.
- 5 PR de Dependabot (#611 a #615), a propósito sin tocar antes de la 1.0.
- Nube (Iteraciones 2 y 3 del Incremento 8): sin cambios.

---

## Retrospectiva

- **Lo que funcionó:** una rama y un PR por iteración; ensayar con las herramientas simuladas antes de tener Docker real; correr la suite de integración completa antes de pushear (un test que mi búsqueda había excluido rompió el CI del PR #626 y se corrigió).
- **Lo que costó:** la rama protegida exige estar al día con `develop`, así que cada PR en vuelo que se atrasa vuelve a correr ~20 minutos de CI. Además la base descartable de la suite debe migrarse a `head` antes de correr: sin eso fallan ~700 tests de integración con `relation ... does not exist` (me pasó al cerrar esta baseline).
- **Decisión de proceso:** se desestimó el celular real y se mandó el ensayo del servidor Docker a un issue; el DoD de la 1.0.0 lo declara así en lugar de ocultarlo.
