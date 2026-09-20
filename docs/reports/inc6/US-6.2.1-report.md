# Reporte de Implementación: US-6.2.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.1 — Cálculo de puntaje server-side de una respuesta en vivo
- **Puntos estimados:** 3
- **Tiempo real:** ~7 min (tracker, 8 fases; PRIN-001 — tiempo del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-20
- **Issue:** [#392](https://github.com/vvalotto/cognion/issues/392)
- **Habilita:** `US-6.2.4` (`ResponderPreguntaEnVivo`), primera consumidora de la fórmula y de `obtener_niveles`

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`puntaje_en_vivo.py`** (nuevo) — `NivelPregunta` (`BAJO`/`MEDIO`/`ALTO`, vocabulario propio: el BC no importa los enums de Banco), `NivelesDePregunta` (VO frozen) y `calcular_puntaje(...)`, función pura. `1000 × FactorTiempo × FactorDificultad × FactorImportancia`, `FactorTiempo` lineal en `[0.5, 1.0]`; incorrecta → 0; tiempo acotado a `[0, límite]`; `límite <= 0` → `ValueError` (se valida antes que la corrección); `round()` único al final. Rango: 500 a 4000.
- ✅ **`PreguntaConsultaPort.obtener_niveles(pregunta_id)`** (`ports/pregunta_consulta_port.py`) — operación abstracta nueva.

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`PreguntaConsultaPortInProcess.obtener_niveles`** — único lugar que conoce los enums de Banco; mapea `Dificultad`/`Importancia` a `NivelPregunta` por valor textual. Pregunta inexistente → `PreguntaNoAsignada` (mismo criterio defensivo que los métodos hermanos).

Sin Use Cases, Interface Adapters ni endpoints (técnica, spec).

### Tests

- ✅ `tests/unit/inc6/test_puntaje_en_vivo.py` — tabla parametrizada (4000, 500, 1125 de la spec + otros), redondeo, monotonía, bordes de tiempo, `ValueError`, inmutabilidad del VO.
- ✅ `tests/integration/inc6/test_pregunta_consulta_niveles.py` — adapter contra la DB real: Opción Múltiple, Verdadero/Falso y pregunta inexistente.
- ✅ `FakePreguntaConsultaPort.niveles` (`tests/unit/inc3/_fakes.py`), default `BAJO/BAJO`.
- Sin `.feature` (`skip_bdd`, como `US-3.1.1`/`US-6.1.1`): los 6 escenarios de la spec quedan cubiertos uno a uno por los tests anteriores.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.80/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 (promedio 2.1) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 70.62 | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`)** | 99% (módulo nuevo 100%) | ≥ 95% | ✅ |
| **mypy (`src/`)** | 0 errores | 0 | ✅ |
| **Tests** | 633 unit + 37 integración inc6 | verde | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.1-quality.json`)

### Detalle de CodeGuard

> `--analysis-type full` con `.venv/bin` en el `PATH` (`quality/reports/inc6/US-6.2.1-codeguard.json`). Sin `.venv/bin` en el `PATH`, `vulture`/`codespell` figuran "not installed" y `mypy` da timeout: la primera corrida salió así y se repitió.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 3 |
| PEP8 | 0 | 2 | 2 |
| Complexity | 0 | 0 | 3 |
| DeadCode | 11 | 21 | 0 |
| Maintainability | 0 | 0 | 3 |
| Pylint | 0 | 0 | 3 |
| Spelling | 0 | 9 | 0 |
| Types | 0 | 0 | 3 |
| UnusedImports | 0 | 0 | 3 |

Los **11 errors de `DeadCode` son falsos positivos**: `vulture` marca como "never used" los parámetros de los métodos abstractos del puerto (`materia_id`, `unidad`, `tema`, `pregunta_id`, `contenido`), que por definición no usan sus argumentos. Este análisis pasa por archivo: al haber tocado el puerto entra en el alcance. Los 2 warnings de `PEP8` son líneas preexistentes del adapter (46 y 61), no de esta US.

---

## Decisiones y notas

- `round()` de Python redondea half-to-even; los tres valores de la spec son exactos, así que no hay diferencia visible. Si algún día se quiere half-up, se cambia en un solo lugar.
- Cero riesgo de romper otras implementaciones del puerto: solo el adapter y el fake lo implementan (grep previo).
