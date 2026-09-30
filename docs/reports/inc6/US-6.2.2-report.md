# Reporte de Implementación: US-6.2.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.2.2 — Docente muestra las opciones de la pregunta actual
- **Puntos estimados:** 3
- **Tiempo real:** ~30 min (tracker; ~17 min son la suite completa con cobertura y CodeGuard en Fase 7 — PRIN-001, tiempo real de ejecución del agente, no comparable contra estimación humana)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-20
- **Aporta:** el segundo paso manual de cada pregunta de la sesión en vivo. `opciones_mostradas_en` es la referencia de `tiempo_respuesta` (INV-AEV-08) que consume `US-6.2.4`.

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`ActividadEvaluativaEnVivo.mostrar_opciones(ahora)`** (`actividad_evaluativa_en_vivo.py`) — valida `estado == EnCurso` (`SesionNoEnCurso`) y que las opciones no estuvieran ya mostradas (`OpcionesYaMostradas`, INV-AEV-09), sin mutar si rechaza. Campo nuevo `opciones_mostradas_en`; `reconstruir()` aplica `OpcionesEnVivoMostradas`
- ✅ **`OpcionesEnVivoMostradas`** (`eventos_en_vivo.py`) — tercer evento del stream: `pregunta_actual_indice`, `pregunta_id`, `opciones` (`None` para Verdadero/Falso), `ocurrido_en`; nunca indica la correcta; `desde_sesion(...)`
- ✅ **`SesionNoEnCurso`, `OpcionesYaMostradas`** (`errors.py`) — errores de dominio nuevos (`SesionNoEnCurso` la reutilizan `US-6.2.4` a `6.2.7`)

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`MostrarOpcionesEnVivoUseCase`** (`mostrar_opciones_en_vivo.py`) — reconstruye, valida y transiciona, obtiene las opciones por `PreguntaConsultaPort.obtener_contenido`, persiste con `expected_sequence_number = len(eventos)` y recién entonces publica. Traduce `ConcurrenciaOptimistaError` a `OpcionesYaMostradas` (dos pedidos simultáneos)

### Interface Adapters

- ✅ **`SesionesEnVivoController.mostrar_opciones(...)`** — el controller pasa a inyectar 4 use cases (cambio de firma del constructor)

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`POST /sesiones-en-vivo/{sesion_id}/mostrar-opciones`** (`api/sesiones_en_vivo_router.py`, rol `docente`) — 200 con el mismo `SesionEnVivoResponse`; `SesionNoExiste` → 404, `SesionNoEnCurso`/`OpcionesYaMostradas` → 422
- ✅ **Wiring** del cuarto use case en `dependencies.py`. Sin migración de DB

**Mensaje de broadcast** a todos los conectados:
`{"tipo": "opciones_mostradas", "pregunta_actual_indice": N, "opciones": [...] | null, "tiempo_limite_por_pregunta_segundos": T, "cantidad_respuestas": 0}` — sin la opción correcta; `opciones: null` señala Verdadero/Falso (sin campo `tipo`, decisión confirmada en el plan).

---

## Tests

| Nivel | Cantidad | Resultado |
|-------|----------|-----------|
| Unitarios (`tests/unit/inc6/`) | 109 (15 nuevos: aggregate, evento y use case/controller) | ✅ |
| Integración (`tests/integration/inc6/`) | 58 (11 nuevos: HTTP, carrera real contra la DB, broadcast por WebSocket a Docente y Estudiante) | ✅ |
| BDD (`tests/step_defs/inc6/test_us_6_2_2_steps.py`) | 6 escenarios | ✅ |
| Suite completa | 1384 pasan, 1 falla | ⚠️ flaky preexistente ajeno |

El fallo es `tests/step_defs/inc3/test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente` (ventana de tiempo de ~1 s, ya documentada en `CLAUDE.md`; falla igual en `develop`).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** | 9.87/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática (máx/función)** | 5 (promedio 1.69) | ≤ 10 | ✅ |
| **Índice de Mantenibilidad (mín)** | 63.91 (promedio 82.06) | > 20 | ✅ |
| **Coverage (`src/actividad_evaluativa`, sin `frameworks/`)** | 100% | ≥ 95% | ✅ |
| **CodeGuard** (7 archivos, `--analysis-type full`) | 2 errors, 133 warnings | — | ✅ (ver detalle) |

**Estado General:** ✅ APROBADO (`quality/reports/inc6/US-6.2.2-quality.json`)

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 7 |
| PEP8 | 0 | 1 | 6 |
| Complexity | 0 | 0 | 7 |
| DeadCode | 0 | 64 | 0 |
| Maintainability | 0 | 0 | 7 |
| Pylint | 1 | 0 | 6 |
| Spelling | 0 | 68 | 1 |
| Types | 0 | 0 | 7 |
| UnusedImports | 1 | 0 | 6 |

- Los **2 errors** (`Pylint`, `UnusedImports`) son **timeouts del pylint interno de CodeGuard** (>10 s y >5 s), reproducidos en dos corridas; no son hallazgos de código. Pylint directo sobre los mismos archivos da 9.87/10 y su único mensaje es `R0903 too-few-public-methods`, el mismo patrón del resto de los use cases.
- Los warnings de `DeadCode` y `Spelling` son ruido preexistente del árbol (nombres en español, parámetros de puertos).

---

## Decisiones y notas

- **Sin `tipo` en el broadcast:** el escenario 2 de la spec pedía "indica el tipo"; se respetó §16 al pie de la letra y `opciones: null` señala Verdadero/Falso.
- **CBO del controller:** pasa a 4 use cases con ~7 imports, lejos del umbral 10, así que no se separó por responsabilidad. El valor real se confirma en el pre-push.
- **Firma del constructor:** se grepeó `SesionesEnVivoController(` de antemano y se actualizaron los 3 tests que lo construían.
- **Test viejo ajustado:** un test de `reconstruir` usaba `OpcionesEnVivoMostradas` como "evento sin efecto" — pasó a `PreguntaEnVivoCerrada`.
- **`_helpers.preparar_sesion`** gana `opcion_multiple` para ejercitar opciones reales por la API.
- **Pendiente para `US-6.2.4`:** `tiempo_respuesta` se mide desde `opciones_mostradas_en`, no desde el enunciado.
