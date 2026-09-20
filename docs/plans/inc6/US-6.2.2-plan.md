# Plan de Implementación: US-6.2.2 - Docente muestra las opciones de la pregunta actual

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Aggregate:** campo nuevo `opciones_mostradas_en: datetime | None`. `mostrar_opciones(ahora)`
   valida y muta, en este orden: `estado != EnCurso` → `SesionNoEnCurso`; `opciones_mostradas` →
   `OpcionesYaMostradas`; si no, `opciones_mostradas = True` y `opciones_mostradas_en = ahora`.
   (`EnEspera` y `Finalizada` dan el mismo error, como pide la spec.)
2. **`reconstruir()`:** `OpcionesEnVivoMostradas` pone `opciones_mostradas = True` y
   `opciones_mostradas_en` desde `ocurrido_en` del payload (ISO → `datetime`). Se agrega al
   dispatch de `_aplicar_evento` existente, sin tocar `SesionEnVivoIniciada`/`Finalizada`.
3. **Payload del evento** (persistido): `{sesion_id, pregunta_actual_indice, pregunta_id,
   opciones (lista o null), ocurrido_en}` — nunca la correcta. Se persiste lo que se mostró, igual
   criterio que `SesionEnVivoIniciada`.
4. **Use Case** `MostrarOpcionesEnVivoUseCase.execute(sesion_id)`: `load` → `SesionNoExiste` si vacío
   → `reconstruir` → `mostrar_opciones(ahora)` → `obtener_contenido(pregunta_id)` → `append` con
   `expected_sequence_number = len(eventos)` → `publicar`. `ConcurrenciaOptimistaError` se traduce a
   `OpcionesYaMostradas` (dos Docentes/clics simultáneos: gana uno; mismo criterio que
   `US-6.1.4`). El evento se construye con `desde_sesion(...)` para no sumar CBO al Use Case.
   El `ahora` se toma del `ocurrido_en` del evento (un solo instante, INV-AEV-08).
5. **Broadcast** (§16, 2ª fila), a todos los conectados y después de persistir: `{"tipo":
   "opciones_mostradas", "pregunta_actual_indice": N, "opciones": [...] | null,
   "tiempo_limite_por_pregunta_segundos": T, "cantidad_respuestas": 0}`.
   **Punto a confirmar:** el escenario 2 de la spec dice que el mensaje "indica el tipo de
   pregunta". El mensaje de §16 no trae `tipo`; en Verdadero/Falso el `null` en `opciones` ya lo
   señala. Propongo **no agregar `tipo`** (respeto §16 al pie de la letra) y que el step BDD
   verifique `opciones is None`. Si preferís `tipo` explícito, es un campo más en el mensaje.
6. **Errores nuevos:** `SesionNoEnCurso(sesion_id)` y `OpcionesYaMostradas(sesion_id)` en
   `errors.py` (`SesionNoEnCurso` la reutilizan `US-6.2.4` a `6.2.7`).
7. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/mostrar-opciones`, rol `docente`, sin body,
   **200** con `SesionEnVivoResponse` (el mismo helper `_a_sesion_response`). `SesionNoExiste` →
   404; `SesionNoEnCurso`/`OpcionesYaMostradas` → 422. Sin cambios de schema.
8. **Controller / CBO:** `SesionesEnVivoController` pasa a **4 use cases**. Sus imports son
   ~7 clases (muy lejos del 10 de `PreguntasController`), así que no separo el controller; el
   CBO real se confirma en el pre-push. Cambia la firma del constructor: grepear los tests que lo
   construyen (`SesionesEnVivoController(`) antes de tocarlo y actualizarlos junto con
   `dependencies.py`.
9. **Sin migración de DB, sin cambios en `src/app.py`.** Sin ownership del Docente sobre la sesión
   (mismo criterio que el resto de los endpoints de la iteración).

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `SesionNoEnCurso`, `OpcionesYaMostradas`
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `opciones_mostradas_en`, `mostrar_opciones(ahora)`, `reconstruir()` con el evento nuevo
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `OpcionesEnVivoMostradas` + `desde_sesion(sesion, opciones, ocurrido_en)`

### 2. Use Case
- [x] `src/actividad_evaluativa/use_cases/mostrar_opciones_en_vivo.py`
  - `MostrarOpcionesEnVivoUseCase.execute(sesion_id)` → `ActividadEvaluativaEnVivo`

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_controller.py`
  - método `mostrar_opciones(sesion_id)`; constructor con 4 use cases

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/mostrar-opciones` (rol `docente`)
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del cuarto use case

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: `mostrar_opciones()`, `reconstruir` con el evento, use case (Fakes existentes), controller.
- Integración: `test_sesiones_en_vivo_mostrar_opciones_router.py` (HTTP + broadcast por WebSocket
  real a Docente y Estudiante; incluye carrera de dos llamadas simultáneas contra la DB).
  Recordar: `tests/integration/` vacía la DB local compartida.
- BDD: step defs de `tests/features/inc6/US-6.2.2-mostrar-opciones-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-20
**Tareas:** 4/4 secciones completadas

## Desvíos respecto del plan

- Ninguno de diseño: las 9 decisiones se implementaron como se aprobaron (sin `tipo` en el
  broadcast, `opciones: null` señala Verdadero/Falso).
- Fuera del checklist:
  - `_helpers.preparar_sesion` gana el parámetro `opcion_multiple` para poder ejercitar
    opciones reales por la API.
  - Un test viejo de `reconstruir` usaba `OpcionesEnVivoMostradas` como "evento sin efecto"
    y pasó a `PreguntaEnVivoCerrada`, porque ahora ese evento sí tiene efecto.
  - Se actualizaron los 3 tests que construían `SesionesEnVivoController(` por la firma nueva.

## Métricas de Tiempo

Tiempos medidos por el tracker (PRIN-001: tiempo real del agente, sin comparar contra estimaciones
humanas). Detalle en `docs/reports/inc6/US-6.2.2-report.md`.

## Lecciones Aprendidas

- ✅ Grepear `SesionesEnVivoController(` antes de cambiar la firma dejó los 3 usos identificados
  desde el plan.
- ⚠️ La suite completa con cobertura tardó ~13 min; el flaky preexistente de `US-3.2.1`
  (`test_rechazo_fuera_del_período_vigente`) volvió a fallar, ajeno a esta US.
- ⚠️ Los 2 `errors` de CodeGuard son timeouts de su check de pylint interno (>5s/>10s),
  reproducidos en dos corridas; pylint directo sobre los mismos archivos da 9.87/10.
- 💡 Con dos WebSockets abiertos en `TestClient` se verifica que Docente y Estudiante reciben el
  mismo mensaje del `POST`, sin fixtures async especiales.
