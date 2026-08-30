# Reporte de Implementación: US-3.4.4

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.4.4 — Docente ve el detalle de una actividad, extiende el plazo
  y la cierra manualmente
- **Puntos estimados:** 5
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-30
- **Spec:** `docs/specs/inc3/US-3.4.4.md`

Cuarta US de la Iteración 4 del Incremento 3 (frontend, RF-11b). Agrega el detalle de una
actividad puntual — apertura, cierre, preguntas, intentos, conteos de evaluaciones — y las
acciones de "Extender plazo" y "Cerrar actividad ahora", reutilizando `PATCH /periodo`
(`US-3.3.1`) y `POST /cerrar` (`US-3.3.2`) sin cambios.

---

## Ajuste sobre la spec (detectado en Fase 2)

La spec proponía un tipo nuevo `ActividadDetalle`, que extendería `ActividadResumen` con
`cantidad_preguntas` e `intentos_permitidos`. Al revisar el código de `US-3.4.2` ya en el
repo, `ActividadResumen`/`ActividadResumenResponse` **ya tenían esos campos** — se reutilizan
tal cual, sin crear un tipo redundante. Lo único que faltaba en el borde de la API era
`cerrada_manualmente` (el dominio ya lo tenía desde `US-3.3.2`), agregado a
`ActividadResumenResponse` (schema) y a su contraparte TypeScript.

---

## Componentes Implementados

### Entities / Ports

- ✅ **`ActividadQueryPort.obtener()`** (`entities/ports/actividad_query_port.py`, nuevo
  método abstracto) — devuelve `ActividadResumen | None`

### Use Cases

- ✅ **`ObtenerActividadUseCase`** (`use_cases/obtener_actividad.py`, nuevo) — delega en el
  puerto, lanza `ActividadNoExiste` si no está (mismo patrón que `ObtenerCuentaUseCase`,
  `US-2.2.3`)

### Interface Adapters / Frameworks

- ✅ **`SQLAlchemyActividadQueryRepository.obtener()`** (implementado) — reconstruye el stream
  de una única actividad (`_cargar_actividad`), reutiliza `_contar_evaluaciones`/`_a_resumen`
  ya existentes
- ✅ **`ActividadesQueryController`** (extendido) — inyecta `ObtenerActividadUseCase` además de
  `ListarActividadesUseCase` (2 dependencias, lejos del umbral de CBO)
- ✅ **`GET /actividades/{actividad_id}`** (`frameworks/api/actividades_router.py`, rol
  `docente`) — reutiliza `ActividadResumenResponse`, `ActividadNoExiste` → 404
- ✅ **`ActividadResumenResponse`** (schema, extendido) — gana `cerrada_manualmente`
- ✅ **`dependencies.py`** — `get_actividades_query_controller` arma `ObtenerActividadUseCase`

### Frontend

- ✅ **`obtenerActividad()`** (`actividad-evaluativa-api.ts`) — `GET /actividades/{id}`,
  reutiliza `mapearActividadResumen`; `ActividadResumenResponse` (TS) gana `cerradaManualmente`
- ✅ **`ActividadDetalle.tsx`** (nueva) — detalle completo + acciones "Extender plazo"/"Cerrar
  actividad ahora" condicionadas a `!cerradaManualmente`
- ✅ **`ExtenderPlazo.tsx`** (nueva) — formulario de nuevo cierre, error 422 inline (mismo
  patrón que `NuevaActividad.tsx`)
- ✅ **`CerrarActividad.tsx`** (nueva) — confirmación destructiva, mismo patrón visual que
  `EliminarPregunta.tsx`
- ✅ **`router.tsx`** — reemplaza los 3 `ActividadEvaluativaPlaceholder` cableados desde
  `US-3.4.1`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint (archivos tocados) | 9.84/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 5 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo entre archivos tocados) | 54.63 | > 20 | ✅ |
| Cobertura de Tests (`entities/` + `use_cases/` + `interface_adapters/`, BC completo) | 100% | ≥ 95% | ✅ |
| mypy (`src/` completo) | 0 errores | 0 errores | ✅ |
| Frontend — oxlint | 0 errores | 0 errores | ✅ |
| Frontend — `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Frontend — cobertura pantallas nuevas | ~90-97% líneas | — (criterio US-2.1.8 a US-3.4.3) | ✅ |

**Estado General:** ✅ APROBADO — `quality/reports/inc3/US-3.4.4-quality.json`

### Detalle de CodeGuard

> Reporte generado con `--analysis-type full` (`PR #168`). Los 16 "errors" no son hallazgos de
> código: `vulture`/`codespell` no están instalados en este entorno (7+7) y 2 timeouts de mypy
> sin cache (`vvalotto/software_limpio#70`) — mypy dedicado sobre `src/` completo corrió limpio.

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 7 |
| PEP8 | 0 | 0 | 7 |
| Complexity | 0 | 0 | 7 |
| DeadCode | 7 (vulture no instalado) | 0 | 0 |
| Maintainability | 0 | 0 | 7 |
| Pylint | 0 | 1 | 6 |
| Spelling | 7 (codespell no instalado) | 0 | 0 |
| Types | 2 (timeout mypy sin cache) | 0 | 5 |
| UnusedImports | 0 | 0 | 7 |

Fuente: `quality/reports/inc3/US-3.4.4-codeguard.json`.

---

## Tests Implementados

### Tests Unitarios (6 tests nuevos)

- ✅ `test_obtener_actividad_use_case.py` (2 tests, nuevo) — devuelve el resumen existente,
  lanza `ActividadNoExiste`
- ✅ `test_actividades_query_controller.py` (+1 test) — delegación de `obtener_actividad()`
- ✅ `FakeActividadQueryPort` (`test_listar_actividades_use_case.py`) — extendida con `obtener()`

### Tests de Integración (5 tests nuevos)

- ✅ `TestObtenerActividadAPIIntegration` (`test_actividades_api_integration.py`) — detalle con
  conteos y estado, detalle de actividad cerrada manualmente, actividad inexistente (404), sin
  autenticación (401), rol insuficiente (403)

### Escenarios BDD (4 escenarios)

- ✅ `US-3.4.4-detalle-actividad.feature`
  - Ver detalle de una actividad
  - Extender plazo exitosamente
  - Rechazo del servidor al intentar acortar con evaluaciones activas
  - Cierre manual de una actividad

### Tests de Frontend (11 tests nuevos)

- ✅ `ActividadDetalle.test.tsx` (5 tests) — datos completos, acciones visibles/ocultas según
  `cerradaManualmente`, navegación a extender plazo y a cerrar
- ✅ `ExtenderPlazo.test.tsx` (3 tests) — extensión exitosa, rechazo 422 inline sin navegar,
  cancelar
- ✅ `CerrarActividad.test.tsx` (3 tests) — aviso con conteo de evaluaciones activas,
  confirmación exitosa, cancelar

**Todos los tests pasando:** ✅ 679/679 backend (unit + integration + BDD) sin regresiones,
199/199 frontend sin regresiones.

---

## Archivos Creados/Modificados

### Código de Producción — Nuevo

- `src/actividad_evaluativa/use_cases/obtener_actividad.py`
- `frontend/src/pages/ActividadDetalle.tsx`
- `frontend/src/pages/ExtenderPlazo.tsx`
- `frontend/src/pages/CerrarActividad.tsx`

### Código de Producción — Modificado

- `src/actividad_evaluativa/entities/ports/actividad_query_port.py`
- `src/actividad_evaluativa/frameworks/adapters/actividad_query_repository.py`
- `src/actividad_evaluativa/frameworks/api/actividades_router.py`
- `src/actividad_evaluativa/frameworks/api/schemas.py`
- `src/actividad_evaluativa/frameworks/dependencies.py`
- `src/actividad_evaluativa/interface_adapters/controllers/actividades_query_controller.py`
- `frontend/src/lib/actividad-evaluativa-api.ts`
- `frontend/src/router.tsx`

### Tests

- `tests/unit/inc3/test_obtener_actividad_use_case.py` (nuevo)
- `tests/unit/inc3/test_listar_actividades_use_case.py` (modificado — `FakeActividadQueryPort`)
- `tests/unit/inc3/test_actividades_query_controller.py` (modificado)
- `tests/integration/inc3/test_actividades_api_integration.py` (modificado —
  `TestObtenerActividadAPIIntegration`)
- `tests/features/inc3/US-3.4.4-detalle-actividad.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_4_4_steps.py` (nuevo)
- `frontend/src/pages/ActividadDetalle.test.tsx` (nuevo)
- `frontend/src/pages/ExtenderPlazo.test.tsx` (nuevo)
- `frontend/src/pages/CerrarActividad.test.tsx` (nuevo)

### Documentación

- `docs/specs/inc3/US-3.4.4.md` (preexistente, redactada antes de esta ejecución)
- `docs/plans/inc3/US-3.4.4-context.md`
- `docs/plans/inc3/US-3.4.4-plan.md`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)
- `docs/reports/inc3/US-3.4.4-report.md` (este archivo)
- `quality/reports/inc3/US-3.4.4-quality.json`, `US-3.4.4-codeguard.json`,
  `US-3.4.4-coverage.json`

---

## Decisiones de diseño

1. **Reutilizar `ActividadResumen`/`ActividadResumenResponse` en vez de crear
   `ActividadDetalle`** — ambos ya tenían todos los campos que pide el wireframe del detalle,
   evita un tipo redundante y una capa de mapeo extra.
2. **`ObtenerActividadUseCase` lanza `ActividadNoExiste`** en vez de que el router maneje un
   `Optional` — mismo patrón que `ObtenerCuentaUseCase` (`US-2.2.3`), consistente con el resto
   del proyecto.
3. **`GET /actividades/{id}` responde `ActividadResumenResponse`**, no un schema nuevo — reusa
   el mismo shape que ya consume `Actividades.tsx` (`US-3.4.2`), sin duplicar contrato de API.

---

## Criterios de Aceptación (spec `docs/specs/inc3/US-3.4.4.md`)

- [x] El Docente ve apertura, cierre, cantidad de preguntas, intentos, evaluaciones activas y
      finalizadas al elegir una actividad
- [x] "Extender plazo" con una fecha de cierre posterior actualiza el cierre y vuelve al
      detalle mostrando el nuevo valor
- [x] Acortar el plazo con evaluaciones activas es rechazado por el backend (422
      `NoSePuedeAcortarConEvaluacionesActivas`), mostrado inline sin navegar
- [x] "Cerrar actividad ahora" cierra la actividad y finaliza en cascada sus evaluaciones
      activas, mostrando el estado `Cerrada`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Continuar con `US-3.4.5` (Estudiante ve sus materias y las actividades disponibles) —
      arranca el lado estudiante de la Iteración 4, en paralelo al lado docente ya completo
      (`US-3.4.2` a `US-3.4.4`)

---

## Lecciones Aprendidas

- ✅ Revisar el código ya existente del mismo BC antes de diseñar un tipo nuevo propuesto por
  la spec evitó una capa redundante (`ActividadResumen` ya cubría el detalle completo).
- ⚠️ En los step_defs BDD, anclar las fechas de prueba (`nueva_fecha_cierre`) al período real
  de la actividad creada en el propio step, no a una ventana fija basada solo en
  `datetime.now()` — un cálculo independiente producía `PeriodoInvalido` en vez del escenario
  de rechazo por acortamiento que se quería probar.
- 💡 Duplicar `ETIQUETA_ESTADO`/`VARIANTE_ESTADO` entre `Actividades.tsx` y
  `ActividadDetalle.tsx` (en vez de extraerlos) mantuvo el cambio acotado — mismo criterio de
  "no generalizar prematuramente" ya aplicado en otras US del proyecto.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-30
