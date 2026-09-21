# Plan de Implementación: US-6.2.5 - Docente cierra la pregunta actual en vivo

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Validación en la entidad:** `ActividadEvaluativaEnVivo.cerrar_pregunta()` muta
   `pregunta_actual_cerrada = True`; la validación vive en un helper a nivel módulo
   `_validar_para_cerrar` (mismo criterio anti-CBO que `mostrar_opciones`). Orden:
   `estado != EnCurso` → `SesionNoEnCurso`; `not opciones_mostradas` →
   `OpcionesNoMostradasTodavia` (INV-AEV-09); `pregunta_actual_cerrada` → `PreguntaYaCerrada`.
   Los tres errores ya existen en `errors.py` (los creó `US-6.2.4`) — **sin errores nuevos**.
2. **`reconstruir()` ya aplica `PreguntaEnVivoCerrada`** (lo agregó `US-6.2.4`): no requiere cambio.
3. **Evento `PreguntaEnVivoCerrada`** (`eventos_en_vivo.py`) con `desde_sesion(sesion, ocurrido_en)`;
   payload mínimo: `sesion_id`, `pregunta_actual_indice`, `pregunta_id`, `ocurrido_en`. Ranking e
   histograma **no** se persisten (viven en los read models).
4. **Use Case** `CerrarPreguntaActualUseCase.execute(sesion_id) -> ActividadEvaluativaEnVivo`:
   `load` (`SesionNoExiste`) → `reconstruir` → `cerrar_pregunta` → `append` con
   `expected_sequence_number = len(eventos)`; `ConcurrenciaOptimistaError` → `PreguntaYaCerrada`
   (carrera de dos cierres simultáneos, igual que `OpcionesYaMostradas` en `US-6.2.2`). **Después**
   de persistir: lee `ProyeccionesEnVivoQueryPort.ranking` y `.distribucion` y
   `PreguntaConsultaPort.obtener_detalle_correccion` (reutiliza el puerto existente: ya devuelve
   texto, contenido correcto y opciones — **sin puerto nuevo**), y publica **un único**
   `pregunta_cerrada` (§16). Canal best-effort. Sin trabajo pesado: 3 lecturas + 1 broadcast (RNF).
5. **CBO del Use Case:** dependencias event store, `ProyeccionesEnVivoQueryPort`,
   `PreguntaConsultaPort`, canal. Se parte en helpers de módulo (`_payload`, `_mensaje_cierre`)
   como `US-6.2.2`. El CBO real se confirma en el pre-push.
6. **Controller:** `ConduccionEnVivoController.cerrar_pregunta(sesion_id)` (ya separado en el
   refactor `992b0ea`; queda con 2 use cases, sin riesgo de CBO). El tipo de retorno es
   `ActividadEvaluativaEnVivo`, mismo que `mostrar_opciones`.
7. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/cerrar-pregunta`, rol `docente`, sin body,
   **200** `SesionEnVivoResponse` (`_a_sesion_response` ya existente). `SesionNoExiste` → 404;
   `SesionNoEnCurso`/`OpcionesNoMostradasTodavia`/`PreguntaYaCerrada` → 422.
8. **Cierre sin respuestas:** distribución vacía y ranking con todos los participantes en su puntaje
   actual (todos tienen fila desde `US-6.1.3`); no requiere lógica especial.
9. **Sin migración de DB**, sin cambios en `src/app.py`, sin puertos nuevos.
10. **Wiring:** `get_conduccion_en_vivo_controller` pasa a inyectar también
    `CerrarPreguntaActualUseCase` (con `SQLAlchemyProyeccionesEnVivoQuery`).

## Componentes a Implementar

### 1. Entities
- [ ] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `cerrar_pregunta()` + helper `_validar_para_cerrar`
- [ ] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `PreguntaEnVivoCerrada` + `desde_sesion`

### 2. Use Case
- [ ] `src/actividad_evaluativa/use_cases/cerrar_pregunta_actual.py`
  - `CerrarPreguntaActualUseCase`

### 3. Interface Adapter
- [ ] `src/actividad_evaluativa/interface_adapters/controllers/conduccion_en_vivo_controller.py`
  - `cerrar_pregunta(sesion_id)`

### 4. Frameworks
- [ ] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/cerrar-pregunta` (rol `docente`)
- [ ] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del use case en `get_conduccion_en_vivo_controller`

## Tests (Fases 4–6, no forman parte de las tareas de Fase 3)
- Unit: `cerrar_pregunta`/`reconstruir`, use case (Fakes; `FakeProyeccionesEnVivo` ya expone
  ranking/distribución), controller `ConduccionEnVivoController` (actualizar su constructor).
- Integración: HTTP + mensaje completo a **dos WebSockets** + doble cierre simultáneo. Recordar:
  vacía la DB local compartida.
- BDD: step defs de `tests/features/inc6/US-6.2.5-cerrar-pregunta-en-vivo.feature`.
