# Reporte de Implementación: US-6.2.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.3 — Read models de ranking e histograma de la sesión en vivo
- **Puntos estimados:** 3
- **Tiempo real:** ~9 min (tracker, 8 fases; PRIN-001 — tiempo del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-20
- **Issue:** [#394](https://github.com/vvalotto/cognion/issues/394)
- **Habilita:** `US-6.2.4`, `6.2.5`, `6.2.7`, `6.2.8`

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/ports/`)

- ✅ **`proyecciones_en_vivo_port.py`** (nuevo) — `ProyeccionesEnVivoPort` (escritura: `inicializar_participante`, `registrar_respuesta`, `descartar_pendientes`) y `ProyeccionesEnVivoQueryPort` (lectura: `ranking`, `distribucion`, `cantidad_respuestas`), con los VOs `ParticipanteEnRanking` y `OpcionDistribuida`. El docstring del módulo fija el **contrato de atomicidad**: las escrituras no hacen `commit`; lo confirma el `append` del event store, y ante `ConcurrenciaOptimistaError` el Use Case llama a `descartar_pendientes`.

### Use Cases

- ✅ **`UnirseASesionEnVivoUseCase`** — 5° dependiente (`ProyeccionesEnVivoPort`). Inicializa la fila del ranking (0 puntos) solo cuando **crea** la participación, antes del `append`; en el camino idempotente no la toca (unirse dos veces no reinicia el puntaje). Si pierde la carrera de concurrencia, descarta la proyección pendiente antes de releer.

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **Modelos ORM** `RankingPorSesionModel` (PK `sesion_id, estudiante_id`) y `DistribucionPorPreguntaModel` (PK `sesion_id, pregunta_id, opcion`).
- ✅ **Migración** `a6c2d4f8b1e3_read_models_sesion_en_vivo.py` — reversible; verificada por round-trip (`downgrade` → `upgrade`) contra la DB real, también como test.
- ✅ **`SQLAlchemyProyeccionesEnVivo`** (escritura) y **`SQLAlchemyProyeccionesEnVivoQuery`** (lectura) — upserts atómicos (`ON CONFLICT DO NOTHING` / `DO UPDATE SET x = x + …`), nunca leer-modificar-escribir. Ranking: `puntaje DESC, ultima_actualizacion ASC, estudiante_id ASC`; la posición se calcula al leer.
- ✅ **Wiring** en `dependencies.py`.

### Tests

- ✅ Unitarios: `FakeProyeccionesEnVivo`; `UnirseASesionEnVivo` deja al participante en 0 puntos, no reinicia al reunirse, descarta la proyección al perder la carrera. Se actualizaron los 3 tests que construyen el use case.
- ✅ Integración (`test_proyecciones_en_vivo.py`, 10 tests contra la DB real): ranking con 0 puntos, idempotencia, suma de puntaje + opción, orden y desempate, aislamiento entre sesiones, distribución/total, **60 respuestas simultáneas sin perder ninguna**, atomicidad evento + proyección (commit conjunto y rollback conjunto), migración reversible.
- Sin `.feature` (`skip_bdd`, técnica).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.70/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 (promedio 1.5) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 62.47 | > 20 | ✅ |
| **Coverage (`entities`/`use_cases` tocados)** | 100% | ≥ 95% | ✅ |
| **mypy (`src/`)** | 0 errores | 0 | ✅ |
| **DesignReviewer** | 0 CRITICAL (245 warnings) | 0 CRITICAL | ✅ |
| **Tests** | 636 unit + 47 integración inc6 | verde | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.3-quality.json`)

> `frameworks/*` está excluido del gate de coverage (`pyproject.toml`); el adapter, la migración y la concurrencia se validan con los 10 tests de integración.

### Detalle de CodeGuard

> `--analysis-type full` con `.venv/bin` en el `PATH` (`quality/reports/inc6/US-6.2.3-codeguard.json`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 4 |
| PEP8 | 0 | 0 | 4 |
| Complexity | 0 | 0 | 4 |
| DeadCode | 12 | 39 | 0 |
| Maintainability | 0 | 0 | 4 |
| Pylint | 1 | 0 | 3 |
| Spelling | 0 | 5 | 2 |
| Types | 0 | 0 | 3 |
| UnusedImports | 1 | 0 | 3 |

- Los **12 errors de `DeadCode`** son falsos positivos: `vulture` marca como "never used" los parámetros de los métodos abstractos del puerto.
- Los **2 errors restantes** (`Pylint`, `UnusedImports`) son **timeouts de pylint** (>10 s y >5 s) dentro de CodeGuard sobre módulos que importan SQLAlchemy; no son hallazgos de código. Pylint directo sobre los mismos archivos da 9.70/10.

---

## Decisiones y notas

- **Un CRITICAL detectado y corregido antes del PR:** el diseño del plan usaba un único adapter que implementaba los dos puertos; `NOPAnalyzer` lo marcó CRITICAL (2 clases base, umbral 1). Se separó en escritura y consulta, el mismo command/query de `US-3.2.4`.
- **`SQLAlchemyEventStore` no se modificó:** el gap (`append` rechaza por concurrencia sin `rollback`) se resolvió con `descartar_pendientes()` en el puerto, sin tocar el comportamiento de los Use Case ya cerrados.
- **CBO del Use Case:** con 5 dependientes no llegó a CRITICAL (0 CRITICAL en el pre-push).
- **Pendiente para `US-6.2.4`:** el desempate del ranking usa `ultima_actualizacion`; el fake unitario no lo modela (solo se prueba en integración).
