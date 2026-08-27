# Reporte de Implementación: US-3.2.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-3.2.1 — Estudiante confirma una respuesta (persistencia atómica)
- **Puntos estimados:** 5
- **Tiempo real:** ~19 min (suma de fases con tracking activo; PRIN-001 — tiempo real de ejecución del agente, no comparable contra estimación humana; Fase 5 no quedó registrada en el tracker por un olvido de `start-phase 5`, el trabajo en sí se completó igual)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-27

---

## Componentes Implementados

### Entities (`src/actividad_evaluativa/entities/`)

- ✅ **`Respuesta`** (`entities/evaluacion.py`, nuevo) — Entity con `id` propio, inmutable, dentro de `Evaluacion.respuestas`
- ✅ **`Evaluacion.respuestas`** (extendido) — colección de `Respuesta`, `contar_respuestas_de()`, `validar_para_registrar_respuesta()` (INV-AE-07/08/12)
- ✅ **`Evaluacion.reconstruir()`** (reescrito) — pasa de leer solo el primer evento a replay real, acumulando `Respuesta` desde cada `RespuestaRegistrada` del stream
- ✅ **`RespuestaRegistrada`** (`entities/eventos.py`, extendido) — evento repetible del stream de `Evaluacion`
- ✅ **`EvaluacionNoExiste`, `PreguntaNoAsignada`, `IntentosAgotados`, `EvaluacionSuspendida`, `EvaluacionYaFinalizada`** (`entities/errors.py`, extendido)
- ✅ **`PreguntaConsultaPort.evaluar_correccion`** (extendido) — nuevo método del puerto hacia BC Banco de Preguntas (INV-AE-10)

### Use Cases (`src/actividad_evaluativa/use_cases/`)

- ✅ **`RegistrarRespuestaUseCase`** (nuevo) — orquesta INV-AE-07/08/09/10/12, calcula `es_correcta` vía el puerto, concurrencia optimista con `expected_sequence_number = len(eventos_evaluacion)` (protege contra doble submit)

### Interface Adapters (`src/actividad_evaluativa/interface_adapters/`)

- ✅ **`EvaluacionesController.registrar_respuesta`** (extendido) — segundo Use Case inyectado, delega tal cual

### Frameworks (`src/actividad_evaluativa/frameworks/`)

- ✅ **`PreguntaConsultaPortInProcess.evaluar_correccion`** (extendido) — único punto del BC que conoce los tipos concretos de Banco de Preguntas (`PreguntaPlantillaOpcionMultiple` por índice de opción, `PreguntaPlantillaVerdaderoFalso` por `bool`)
- ✅ **`schemas.py`** (extendido) — `RegistrarRespuestaRequest`/`RespuestaResponse` (sin `es_correcta` ni `contenido` — hot spot "sin feedback inmediato")
- ✅ **`evaluaciones_router.py`** (extendido) — `POST /evaluaciones/{evaluacion_id}/respuestas` (rol `estudiante`), mapea `EvaluacionNoExiste`/`PreguntaNoAsignada`→404, `IntentosAgotados`/`EvaluacionSuspendida`/`EvaluacionYaFinalizada`/`FueraDePeriodo`→422
- ✅ **`dependencies.py`** (extendido) — `get_evaluaciones_controller` arma también `RegistrarRespuestaUseCase`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/evaluaciones/{evaluacion_id}/respuestas` | Confirma una respuesta, persistencia atómica | ✅ rol `estudiante` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.73/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 7 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 67.18 | > 20 | ✅ |
| Cobertura de Tests (`entities/`+`use_cases/`+`interface_adapters/`) | 100% | ≥ 95% | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc3/US-3.2.1-quality.json`)

> `codeguard` sobre los 10 `.py` nuevos/modificados de la US: 0 errores, 0 advertencias tras
> corregir una línea >100 caracteres en `entities/errors.py` (mismo patrón ya visto en
> `US-3.1.2`/`US-3.1.3`) — `quality/reports/inc3/US-3.2.1-codeguard.json`. `frameworks/`
> excluido del gate de coverage por `pyproject.toml` (mismo criterio en todos los BCs) —
> cubierto en cambio por 8 tests de integración HTTP y 8 escenarios BDD contra la base local.

---

## Tests Implementados

### Tests Unitarios (21 tests nuevos — `tests/unit/inc3/`)

- ✅ `test_evaluacion.py` (+8) — replay con `Respuesta` acumuladas, `contar_respuestas_de`, `validar_para_registrar_respuesta` (numero de intento, las 4 invariantes)
- ✅ `test_registrar_respuesta_use_case.py` (nuevo, 7) — respuesta válida, segundo intento, intentos agotados, pregunta no asignada, evaluación inexistente, evaluación de otro estudiante, fuera de período
- ✅ `test_errors.py` (+5) — los 5 errores de dominio nuevos
- ✅ `test_evaluaciones_controller.py` (+1) — delegación de `registrar_respuesta` al use case
- ✅ `_fakes.py` (extendido) — `FakePreguntaConsultaPort.evaluar_correccion`

### Tests de Integración (8 tests nuevos — `tests/integration/inc3/`)

- ✅ `test_registrar_respuesta_api_integration.py` (nuevo, 8) — respuesta válida verdadero/falso, corrección de opción múltiple verificada contra el event store, segundo intento, intentos agotados, pregunta no asignada, evaluación inexistente, 401 sin auth, 403 con rol insuficiente

### Escenarios BDD (8 escenarios — `tests/features/inc3/US-3.2.1-registrar-respuesta.feature`)

- ✅ Estudiante confirma una respuesta válida (opción múltiple)
- ✅ Segundo intento sobre la misma pregunta dentro del límite
- ✅ Rechazo por intentos agotados
- ✅ Rechazo por pregunta no asignada
- ✅ Rechazo sobre evaluación suspendida (a nivel de dominio — ver Lecciones Aprendidas)
- ✅ Rechazo sobre evaluación finalizada (a nivel de dominio — ver Lecciones Aprendidas)
- ✅ Rechazo fuera del período vigente (ventana real de ~1.5s + `sleep`)
- ✅ Persistencia atómica ante desconexión simulada (verificado con `SessionLocal` independiente)

**Todos los tests pasando:** ✅ suite completa `unit/` + `integration/` + `step_defs/` sin regresiones (484 tests totales del proyecto, +37 de esta US)

---

## Archivos Creados

### Código de Producción

- `src/actividad_evaluativa/entities/evaluacion.py` (extendido)
- `src/actividad_evaluativa/entities/eventos.py` (extendido)
- `src/actividad_evaluativa/entities/errors.py` (extendido)
- `src/actividad_evaluativa/entities/ports/pregunta_consulta_port.py` (extendido)
- `src/actividad_evaluativa/use_cases/registrar_respuesta.py` (nuevo)
- `src/actividad_evaluativa/interface_adapters/controllers/evaluaciones_controller.py` (extendido)
- `src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py` (extendido)
- `src/actividad_evaluativa/frameworks/api/schemas.py` (extendido)
- `src/actividad_evaluativa/frameworks/api/evaluaciones_router.py` (extendido)
- `src/actividad_evaluativa/frameworks/dependencies.py` (extendido)

### Tests

- `tests/unit/inc3/_fakes.py` (extendido)
- `tests/unit/inc3/test_evaluacion.py`, `test_errors.py`, `test_evaluaciones_controller.py` (extendidos)
- `tests/unit/inc3/test_registrar_respuesta_use_case.py` (nuevo)
- `tests/integration/inc3/test_registrar_respuesta_api_integration.py` (nuevo)
- `tests/features/inc3/US-3.2.1-registrar-respuesta.feature` (nuevo)
- `tests/step_defs/inc3/test_us_3_2_1_steps.py` (nuevo)

### Documentación

- `docs/specs/inc3/US-3.2.1.md`
- `docs/plans/inc3/US-3.2.1-context.md`, `US-3.2.1-plan.md`
- `docs/reports/inc3/US-3.2.1-report.md` (este archivo)
- `quality/reports/inc3/US-3.2.1-quality.json`, `US-3.2.1-codeguard.json`
- `docs/traceability/matrix.md` (actualizado — RF-13 suma `US-3.2.1` a su columna de US-IEDD, sigue en Especificado)

---

## Criterios de Aceptación (`docs/specs/inc3/US-3.2.1.md`)

- [x] Confirma una respuesta válida y se emite `RespuestaRegistrada`, sin informar la corrección en la respuesta HTTP
- [x] Segundo intento dentro del límite crea una segunda `Respuesta`, ambas conviven, la más reciente es la vigente
- [x] Rechaza con `IntentosAgotados` al superar `cantidad_intentos_permitidos`
- [x] Rechaza con `PreguntaNoAsignada` si la pregunta no está en el set asignado
- [x] Rechaza con `EvaluacionSuspendida`/`EvaluacionYaFinalizada` según el estado
- [x] Rechaza con `FueraDePeriodo` fuera de la ventana vigente
- [x] Persistencia atómica verificada: la respuesta sobrevive a un reinicio del proceso backend (verificado con una sesión de BD independiente, no un mock)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-3.2.2` (Suspender/ReanudarEvaluacion) — habilita alcanzar el estado `Suspendida` vía HTTP real en futuros tests de esta US si se quisiera reforzar
- [ ] `US-3.2.3` (FinalizarEvaluacion + revisión, RF-13) — consume `respuestas` para el puntaje y la revisión completa
- [ ] `US-3.2.4` (`VerificadorDeVencimientos`, técnica) — usa `ultima_actividad_en`, que debería actualizarse con cada `RespuestaRegistrada` (todavía no implementado en esta US — el read model `evaluaciones_activas_por_actividad` llega recién con `US-3.2.4`)
- [ ] `docs/traceability/matrix.md` — RF-13 sigue en Especificado hasta que Iteración 2 completa (backend) y Iteración 4 (frontend) cierren

---

## Lecciones Aprendidas

- 💡 `Evaluacion.reconstruir` pasó de leer solo `eventos[0]` a un replay real acumulando
  `Respuesta` desde `eventos[1:]` — primer caso del BC donde un aggregate necesita reproducir
  más de un evento de su propio stream. El cambio quedó contenido en un único método.
- 💡 Separar `validar_para_registrar_respuesta` (valida invariantes + calcula `numero_intento`)
  de la construcción de la `Respuesta` en sí evitó una vuelta rara de "construir con
  `es_correcta` provisorio y reconstruir con el real" — el Use Case es quien conoce
  `es_correcta` (consulta a Banco de Preguntas), la Entity no necesita saberlo para validar.
- 🐛 Dos de los 8 escenarios BDD (`Rechazo sobre evaluación suspendida`/`finalizada`) no se
  pudieron implementar end-to-end vía HTTP porque `SuspenderEvaluacion`/`FinalizarEvaluacion`
  todavía no existen (llegan con `US-3.2.2`/`US-3.2.3`) — se implementaron a nivel de dominio
  (`Evaluacion.validar_para_registrar_respuesta` directo), detectado recién al escribir los
  steps en Fase 6, no en Fase 1 al redactar el `.feature`. Vale la pena chequear en Fase 1 si
  todos los `Given` de un escenario son alcanzables con lo que la Iteración ya tiene construido.
- 🐛 El escenario "Rechazo fuera del período vigente" tampoco es alcanzable con una actividad
  ya cerrada desde el vamos (`IniciarEvaluacion` la rechazaría antes de llegar a
  `RegistrarRespuesta`) — se resolvió con una ventana de vigencia muy corta (~1.5s) y un `sleep`
  real antes de confirmar la respuesta, sin necesitar el endpoint de modificación de período de
  `US-3.3.1` (Iteración 3, todavía no implementado).
- ✅ El patrón recurrente de CRITICAL de CBO de Incremento 2 no se repitió: `EvaluacionesController`
  con 2 Use Cases inyectados quedó lejos del umbral.
- ✅ `codeguard` detectó una línea >100 caracteres en `entities/errors.py` — tercera vez que
  aparece este mismo tipo de hallazgo en el BC (`US-3.1.2`, `US-3.1.3`), confirma que el límite
  real del proyecto es 100, no el default genérico de la herramienta.
- ⚠️ Se olvidó ejecutar `tracker_cli.py start-phase 5` antes de escribir los tests de
  integración — el trabajo se hizo completo igual, pero la Fase 5 no quedó con tiempo
  registrado en el tracking de esta US.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-27
