# Plan de Implementación: US-6.2.7 - Docente finaliza la sesión — ranking final

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Validación en la entidad:** `ActividadEvaluativaEnVivo.finalizar()` valida y muta; helper de
   módulo `_validar_para_finalizar`. Orden: `estado == Finalizada` → `SesionYaFinalizada`;
   `estado != EnCurso` (EnEspera) → `SesionNoEnCurso`; `not pregunta_actual_cerrada` →
   `PreguntaActualNoCerrada` (INV-AEV-03). Sin restricción de última pregunta (decisión 2026-09-21).
   Mutación: `estado = Finalizada`.
2. **Sin errores nuevos**: `SesionYaFinalizada`, `SesionNoEnCurso`, `PreguntaActualNoCerrada` ya existen.
3. **Evento `SesionEnVivoFinalizada`** (`eventos_en_vivo.py`): payload `sesion_id`, `ocurrido_en`
   (sin ranking). `reconstruir()` ya lo aplica vía `_ESTADO_POR_EVENTO` — sin cambios.
4. **Use Case** `FinalizarSesionEnVivoUseCase.execute(sesion_id) -> ActividadEvaluativaEnVivo`:
   `load` (`SesionNoExiste`) → `reconstruir` → `finalizar` → `append` con
   `expected_sequence_number = len(eventos)`; `ConcurrenciaOptimistaError` → `SesionYaFinalizada`
   → lee `proyecciones.ranking(sesion_id)` → publica
   `{"tipo": "sesion_finalizada", "ranking": [{posicion, estudiante_id, puntaje_acumulado}]}`
   **después** de persistir. Dependencias: event store, `ProyeccionesEnVivoQueryPort`, canal.
5. **Controller:** `ConduccionEnVivoController.finalizar_sesion(sesion_id)` (pasa a 4 use cases;
   CBO real se confirma en pre-push — si roza 10/10, separar antes de pushear).
6. **Endpoint:** `POST /sesiones-en-vivo/{sesion_id}/finalizar`, rol `docente`, sin body, **200**
   `SesionEnVivoResponse`. `SesionNoExiste` → 404; `SesionYaFinalizada`/`SesionNoEnCurso`/
   `PreguntaActualNoCerrada` → 422.
7. **Sin migración**, sin puertos nuevos, sin cambios en `src/app.py`.
8. **Wiring:** `get_conduccion_en_vivo_controller` inyecta también el use case nuevo.
9. **Limpieza de tests previos:** reemplazar la siembra de `SesionEnVivoFinalizada` en tests de
   `US-6.1.3`/`6.1.4` por el endpoint real donde sea posible (Fase 5); el helper de siembra queda
   solo para lo que no pueda producirse por API. Al cambiar la firma del controller, grepear los
   tests que lo construyen.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/eventos_en_vivo.py`
  - `SesionEnVivoFinalizada` + `desde_sesion`
- [x] `src/actividad_evaluativa/entities/actividad_evaluativa_en_vivo.py`
  - `finalizar()` + `_validar_para_finalizar`

### 2. Use Cases
- [x] `src/actividad_evaluativa/use_cases/finalizar_sesion_en_vivo.py`
  - `FinalizarSesionEnVivoUseCase`

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/conduccion_en_vivo_controller.py`
  - `finalizar_sesion(sesion_id)`

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `POST /{sesion_id}/finalizar` (rol `docente`) y mapeo de errores
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del use case

## Tests (Fases 4–6)
- Unit: `finalizar`/`reconstruir`, use case (Fakes), controller.
- Integración: HTTP + mensaje `sesion_finalizada` completo a **dos WebSockets**. Vacía la DB local.
- BDD: step defs de `tests/features/inc6/US-6.2.7-finalizar-sesion-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-21
**Tareas:** 4/4 secciones completadas

## Desvíos respecto del plan

- Las 9 decisiones de diseño se implementaron como se aprobaron, sin desvíos de `src/`.
- Los tests unitarios que construían `ConduccionEnVivoController` con 3 use cases
  (`test_cerrar_pregunta_actual`, `test_mostrar_opciones_en_vivo`, `test_avanzar_siguiente_pregunta`)
  se actualizaron al constructor de 4.
- Integración/BDD: la siembra de `SesionEnVivoFinalizada` se reemplazó por el endpoint real en
  6 lugares (helpers nuevos `cerrar_pregunta_actual`, `finalizar_sesion`, `iniciar_y_finalizar`);
  `sembrar_evento_de_sesion` se eliminó. El fake local de los unitarios de `unirse` se mantiene
  (no pasa por API).

## Métricas de Tiempo

Tiempos medidos por el tracker (PRIN-001). Detalle en `docs/reports/inc6/US-6.2.7-report.md`.

## Lecciones Aprendidas

- ✅ Con el controller ya separado (`ConduccionEnVivoController`) el cuarto use case entró sin
  tocar su estructura; el CBO real se confirma en el pre-push.
- ✅ El ranking final sale del read model (`ProyeccionesEnVivoQueryPort.ranking`), sin puerto nuevo.
- ⚠️ Los helpers de test que arman el estado por API (iniciar → mostrar → cerrar → finalizar)
  alargan la suite de integración; se centralizaron en `_helpers.iniciar_y_finalizar`.
- ⚠️ `sed -i` con `#` como delimitador falla en macOS/zsh: editar planes con Python.
