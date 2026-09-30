# Plan de Implementación: US-6.2.6 - Docente avanza a la siguiente pregunta

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Validación en la entidad:** `ActividadEvaluativaEnVivo.avanzar()` valida y muta; la validación
   vive en un helper de módulo `_validar_para_avanzar` (mismo criterio anti-CBO que
   `_validar_para_cerrar`). Orden: `estado != EnCurso` → `SesionNoEnCurso`;
   `not pregunta_actual_cerrada` → `PreguntaActualNoCerrada` (INV-AEV-03);
   `indice + 1 >= len(preguntas)` → `NoQuedanPreguntas`. Mutación: `pregunta_actual_indice += 1`,
   `opciones_mostradas = False`, `opciones_mostradas_en = None`, `pregunta_actual_cerrada = False`.
2. **Errores nuevos** en `errors.py`: `PreguntaActualNoCerrada`, `NoQuedanPreguntas` (mismo molde
   que `PreguntaYaCerrada`).
3. **Evento `SiguientePreguntaPresentada`** (`eventos_en_vivo.py`): mismo shape que
   `SesionEnVivoIniciada` (`sesion_id`, `pregunta_actual_indice`, `pregunta_id`, `enunciado`,
   `tipo`, `ocurrido_en`) con `desde_sesion(sesion, enunciado, tipo)`. Se persiste tras `avanzar()`,
   por lo que el índice ya es el nuevo.
4. **`reconstruir()`**: `_aplicar_evento` gana la rama `SiguientePreguntaPresentada` (índice del
   payload; opciones ocultas; sin cerrar).
5. **Función compartida del mensaje** (spec: no duplicar): módulo nuevo
   `use_cases/pregunta_presentada.py` con `payload_pregunta_presentada(evento)` y
   `mensaje_pregunta_presentada(evento)`, tipados sobre `SesionEnVivoIniciada |
   SiguientePreguntaPresentada`. `iniciar_sesion_en_vivo.py` deja de definir `_payload` y
   `_mensaje_pregunta` y los importa; el mensaje `pregunta_presentada` sale idéntico al de hoy.
   También se extrae ahí `tipo_de_pregunta(contenido)` (`"verdadero_falso"` si `opciones is None`).
6. **Use Case** `AvanzarSiguientePreguntaUseCase.execute(sesion_id) -> ActividadEvaluativaEnVivo`:
   `load` (`SesionNoExiste`) → `reconstruir` → `avanzar` → `obtener_contenido` de la nueva pregunta
   → `append` con `expected_sequence_number = len(eventos)`; `ConcurrenciaOptimistaError` →
   `PreguntaActualNoCerrada` (el ganador ya dejó la pregunta nueva sin cerrar, según la spec) →
   publica `pregunta_presentada` **después** de persistir. Dependencias: event store,
   `PreguntaConsultaPort`, canal (igual que `IniciarSesionEnVivo`, sin riesgo de CBO).
7. **Controller:** `ConduccionEnVivoController.avanzar_siguiente_pregunta(sesion_id)` (pasa a 3 use
   cases; el CBO real se confirma en el pre-push).
8. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/avanzar`, rol `docente`, sin body, **200**
   `SesionEnVivoResponse`. `SesionNoExiste` → 404; `SesionNoEnCurso`/`PreguntaActualNoCerrada`/
   `NoQuedanPreguntas` → 422.
9. **Sin migración de DB**, sin puertos nuevos, sin cambios en `src/app.py`.
10. **Wiring:** `get_conduccion_en_vivo_controller` inyecta también el use case nuevo.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `PreguntaActualNoCerrada`, `NoQuedanPreguntas`
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `SiguientePreguntaPresentada` + `desde_sesion`
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `avanzar()` + `_validar_para_avanzar` + rama en `_aplicar_evento`

### 2. Use Cases
- [x] `src/actividad_evaluativa/use_cases/pregunta_presentada.py`
  - función compartida de payload/mensaje/tipo (extraída de `iniciar_sesion_en_vivo.py`)
- [x] `src/actividad_evaluativa/use_cases/iniciar_sesion_en_vivo.py`
  - usar la función compartida (sin cambio de comportamiento)
- [x] `src/actividad_evaluativa/use_cases/avanzar_siguiente_pregunta.py`
  - `AvanzarSiguientePreguntaUseCase`

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/conduccion_en_vivo_controller.py`
  - `avanzar_siguiente_pregunta(sesion_id)`

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/avanzar` (rol `docente`) y mapeo de errores
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del use case en `get_conduccion_en_vivo_controller`

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: `avanzar`/`reconstruir`, use case (Fakes), controller (actualizar su constructor: grepear
  los tests que lo construyen antes de cambiar la firma).
- Integración: HTTP + mensaje completo a **dos WebSockets**. Recordar: vacía la DB local compartida.
- BDD: step defs de `tests/features/inc6/US-6.2.6-avanzar-siguiente-pregunta.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-21
**Tareas:** 4/4 secciones completadas

## Desvíos respecto del plan

- Las 10 decisiones de diseño se implementaron como se aprobaron. Único agregado no listado: el
  helper `_pasar_a_pregunta` en la entidad, compartido por `avanzar()` y por `_aplicar_evento`
  (`reconstruir`) para que ambos dejen el estado inicial de la pregunta de forma idéntica.
- Los tests unitarios existentes que construían `ConduccionEnVivoController` con 2 argumentos
  (`test_cerrar_pregunta_actual_use_case.py`, `test_mostrar_opciones_en_vivo_use_case.py`) se
  actualizaron al constructor de 3 use cases.

## Métricas de Tiempo

Tiempos medidos por el tracker (PRIN-001). Detalle en `docs/reports/inc6/US-6.2.6-report.md`.

## Lecciones Aprendidas

- ✅ Extraer el armado de `pregunta_presentada` a `use_cases/pregunta_presentada.py` evitó duplicar
  payload y mensaje entre inicio y avance; el mensaje de `US-6.1.4` no cambió (sus tests siguen
  en verde sin tocarlos).
- ✅ El controller ya separado (`ConduccionEnVivoController`) absorbió el tercer use case sin
  riesgo de CBO; el resultado real se confirma en el pre-push.
- ⚠️ `ActividadEvaluativaEnVivo.crear` baraja las preguntas: los tests no pueden asumir que el
  "Enunciado 1" queda en el índice 1; el contenido se asigna según `sesion.preguntas`.
- ⚠️ `ruff format src` reformatea archivos de otros BCs (`identidad`, `notificaciones`): acotarlo
  a los archivos de la US para no ensuciar el diff.
- ⚠️ El flake preexistente `test_us_3_2_1_steps::test_rechazo_fuera_del_período_vigente` volvió a
  fallar en la suite completa (ventana de ~1 s en su setup); no guarda relación con esta US.
