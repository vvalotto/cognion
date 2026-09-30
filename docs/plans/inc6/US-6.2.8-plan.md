# Plan de Implementación: US-6.2.8 - Consultar el estado de la sesión, sus participantes y su ranking

**Patrón:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
**Producto:** cognion — BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar en este checkpoint)

1. **Solo lecturas**: sin comando, sin evento, sin escritura, sin migración, sin puertos nuevos.
   Se reutilizan `EventStorePort`, `PreguntaConsultaPort` (`obtener_contenido`,
   `obtener_detalle_correccion`), `ParticipantesSesionQueryPort` y `ProyeccionesEnVivoQueryPort`.
2. **Error nuevo** `RankingNoDisponible(sesion_id)` en `errors.py` → 403 (Estudiante pide el ranking
   con la sesión no `Finalizada`, §17 punto 10).
3. **`ObtenerEstadoSesionUseCase.execute(sesion_id, estudiante_id | None) -> EstadoSesion`**:
   `load` (`SesionNoExiste`) → `reconstruir`. Con pregunta actual: `obtener_contenido` →
   `pregunta_actual = {pregunta_id, enunciado, tipo}`; `opciones` **solo si** `opciones_mostradas`;
   `respuesta_correcta` **solo si** `pregunta_actual_cerrada` (mismo shape que el broadcast
   `pregunta_cerrada`: `{contenido, texto, opciones}`, vía `obtener_detalle_correccion`). Con
   `estudiante_id` (Estudiante) suma `ya_respondio` y `puntaje_acumulado` reconstruyendo su
   `ParticipacionEnVivo` (`id_para`); si todavía no se unió: `ya_respondio = false`, `puntaje = 0`
   (no es error — el estado es público para la sesión). Docente: esos dos campos `null`.
   `EstadoSesion` es un dataclass del propio módulo; helpers a nivel de módulo (anti-CBO).
4. **`ListarParticipantesUseCase.execute(sesion_id)`**: verifica que la sesión exista
   (`SesionNoExiste`) y delega en `ParticipantesSesionQueryPort.listar`.
5. **`ObtenerRankingUseCase.execute(sesion_id, es_estudiante)`**: verifica existencia; si
   `es_estudiante` y `estado != Finalizada` → `RankingNoDisponible`; devuelve
   `ProyeccionesEnVivoQueryPort.ranking`. Docente: en cualquier momento.
6. **Controller propio** `SesionesEnVivoQueryController` (command/query separado, evita CBO) con
   `obtener_estado`, `listar_participantes`, `obtener_ranking`.
7. **Endpoints** (`sesiones_en_vivo_router.py`): `GET /sesiones-en-vivo/{id}` y `.../ranking`
   (`require_estudiante_o_docente`, el rol sale del JWT), `GET .../participantes` (`require_docente`).
   `SesionNoExiste` → 404; `RankingNoDisponible` → 403.
8. **Schemas** nuevos en `schemas.py`: `EstadoSesionEnVivoResponse` (+ `PreguntaActualResponse`,
   `RespuestaCorrectaResponse`), `ParticipanteResponse`, `RankingItemResponse`.
9. **Wiring:** `get_sesiones_en_vivo_query_controller` en `dependencies.py`.
10. **Sin datos escritos**: los tests verifican explícitamente que no se agregan eventos.

## Componentes a Implementar

### 1. Entities
- [x] `src/actividad_evaluativa/entities/errors.py`
  - `RankingNoDisponible`

### 2. Use Cases
- [x] `src/actividad_evaluativa/use_cases/obtener_estado_sesion.py`
  - `ObtenerEstadoSesionUseCase`, `EstadoSesion`
- [x] `src/actividad_evaluativa/use_cases/listar_participantes.py`
  - `ListarParticipantesUseCase`
- [x] `src/actividad_evaluativa/use_cases/obtener_ranking.py`
  - `ObtenerRankingUseCase`

### 3. Interface Adapter
- [x] `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_query_controller.py`
  - `SesionesEnVivoQueryController`

### 4. Frameworks
- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - schemas de respuesta
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - 3 endpoints GET
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - wiring del controller de consultas

## Tests (Fases 4–6)
- Unit: los 3 use cases (Fakes; verificar que no se escribe nada) y el controller.
- Integración: HTTP contra la DB real (estados de la sesión, ranking, participantes, roles). Vacía la DB local.
- BDD: step defs de `tests/features/inc6/US-6.2.8-consultar-estado-sesion-en-vivo.feature`.

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-21
**Tareas:** 4/4 secciones completadas

## Desvíos respecto del plan

- Las 10 decisiones de diseño se implementaron como se aprobaron, sin desvíos de `src/`.
- Único agregado no listado: `EstadoSesion` expone `opciones_mostradas_en` como propiedad para que el
  router no tenga que llegar a `estado.sesion`.
- BDD: el escenario "1200 puntos acumulados" no fija el número — el puntaje real depende del tiempo de
  respuesta (500-4000); el step lo verifica contra el `puntaje_acumulado` que el propio servidor devolvió
  al responder.

## Métricas de Tiempo

Tiempos medidos por el tracker (PRIN-001). Detalle en `docs/reports/inc6/US-6.2.8-report.md`.

## Lecciones Aprendidas

- ✅ Diseñar el controller de consultas separado desde el principio (command/query) evitó el CRITICAL de
  CBO que aparecía en los controllers de comandos.
- ✅ Ninguna consulta necesitó puerto nuevo: se reutilizaron `EventStorePort`, `PreguntaConsultaPort`,
  `ParticipantesSesionQueryPort` y `ProyeccionesEnVivoQueryPort`.
- ⚠️ El puntaje de una respuesta no es determinístico (depende del tiempo): los tests verifican contra el
  feedback del servidor, no contra un valor fijo.
- ⚠️ El único error de CodeGuard (DeadCode `cls`) es un `@classmethod` preexistente de US-6.2.4.
