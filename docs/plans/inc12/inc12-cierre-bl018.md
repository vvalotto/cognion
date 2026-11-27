# Plan de cierre — BL-018 y `v1.0.1` (Incremento 12, Iteraciones 1 y 2)

Procedimiento de `docs/plans/WORKFLOW-DESARROLLO.md` §7 con la diferencia de `inc12-proceso.md` («Baselines»): el UAT es **de regresión**, no de aceptación. Estado de partida (2026-11-28): `develop` en `774ca3e`, Milestone 21 con 16 Issues cerrados y 0 abiertos, los hallazgos de las Iteraciones 1 y 2 en *Cerrado* (única excepción: `DM-04`, *Limitación conocida*, documentada).

## Qué garantiza `v1.0.1`

Riesgos de operación y de datos cerrados; unidad de trabajo por request; errores con categoría y un manejador; repositorios y presenters en su capa; pool de conexiones y verificador de un solo proceso; umbral de CBO medido. **Sin funcionalidad nueva ni cambios de contrato:** el esquema OpenAPI es idéntico al de la `1.0.0`.

## Pasos

| # | Paso | Detalle y evidencia |
|---|---|---|
| 1 | Rama y base descartable | `chore/bl-018-cierre` desde `develop`; base `cognion_bl018` migrada a `head` (`alembic upgrade head`); `cognion`, `cognion_local` y `cognion_uat` no se tocan |
| 2 | Regresión completa | `pytest tests --cov=src` **dos veces** (para ver si reaparece la falla intermitente de integración de la US-12.2.6), Vitest, `tsc -b`, `oxlint`, `ruff`, `mypy`, `pylint`, `lint-imports`, DesignReviewer, `pip-audit` y `npm audit` (`scripts/calidad.sh --completo --seguridad`). Métricas contra las de `BL-016` |
| 3 | ArchitectAnalyst | Siempre manual y después de generar `coverage.json`, con `--config pyproject.toml`: `quality/reports/architectanalyst/BL-018-arquitectura.json` y copia en `.cm/baselines/` |
| 4 | UAT de regresión | Diseño en `quality/reports/uat/inc12/design.md`, evidencia en `report.md` y archivos de datos, sobre una instalación local (`ENTORNO=local`, base `cognion_uat`, **pool real**). **Capa 1:** la suite del paso 2. **Capa 2:** `tests/uat/inc10/capa2_http.py` (27 comprobaciones HTTP y WebSocket) y `carga_logins.py` (30 logins simultáneos); se agregan comprobaciones de lo que cambió: intento fallido de login que cuenta para el bloqueo (unidad de trabajo), cuerpos y códigos de 401/403/404/409/422 (manejador único), y 60 respuestas casi simultáneas en una sesión en vivo (pool). **Navegador real:** los circuitos de la `1.0.0` con una persona docente y tres estudiantes (período abierto y sesión en vivo) en el navegador del panel, con viewport de escritorio y de celular emulado; se busca diferencias, no aceptación. Hallazgos clasificados antes de resolverse; sin 🔴 Bloqueantes |
| 5 | Matriz de trazabilidad | `docs/traceability/matrix.md`: se revisa que ningún RF o RNF cambie de estado; se anota `BL-018` donde corresponda. No se espera ningún RF nuevo en *Validado* |
| 6 | Versión y notas | `VERSION` 1.0.0 → 1.0.1, `CHANGELOG.md` `[1.0.1]` (el CD verifica que el tag coincida con `VERSION`) |
| 7 | `BL-018.md` | Formato de `BL-016`: inventario de CI, métricas, *No verificado*, retrospectiva. Actualizar `CLAUDE.md` (Estado actual), `inc12-candidatas.md` (Iteraciones 1 y 2 cerradas) y el mapa documental si hace falta |
| 8 | PR a `develop` | `chore(cm): registrar BL-018 ...`, con CI completo |
| 9 | Release | PR `develop → main` y tag `v1.0.1` **en `main`**: el CD construye la imagen, la publica en GHCR y crea el GitHub Release. Se verifica el job `release` y el paquete |
| 10 | Seguimiento | Estado en la memoria del proyecto; Milestone 21 sigue abierto (ver D2) |

## No verificado (se declara en `BL-018`)

Camino del servidor con dominio, certificado y firewall (Issue #624) y la medición del pool en el servidor; celular real; la falla intermitente de integración de la US-12.2.6 si reaparece sin causa; las secuencias de runtime de `docs/architecture/30-runtime-interactions.md`.

## Decisiones a confirmar con Víctor

| # | Decisión | Propuesta |
|---|---|---|
| D1 | Quién ejecuta el UAT en navegador real | Lo recorro yo en el navegador del panel (como en `BL-016`) y dejo la evidencia; si querés repetirlo vos en tu navegador o en un celular real, queda anotado como paso opcional |
| D2 | Milestone 21 | **Se deja abierto**: el Incremento 12 sigue con las Iteraciones 3 y 4 hasta `v1.1.0`; se cierra con `BL-019` |
| D3 | Versión | `v1.0.1` (parche): sin funcionalidad nueva ni cambios de contrato |
| D4 | Confirmaciones al publicar | El merge de la PR a `develop` y, aparte, el merge `develop → main` con el tag, los pido cada uno por separado: el segundo publica una versión |
