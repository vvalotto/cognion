# Plan de Implementación: US-6.1.1 - Infraestructura de tiempo real (WebSockets) y ComisionConsultaPort

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC: actividad_evaluativa)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-18

## Métricas de Tiempo (tracking real del agente — PRIN-001, no comparable a esfuerzo humano)

Tiempo total: 22 min (1320s), fases 0/2/3/4/5/7 registradas, 7/7 tareas de Fase 3.

## Lecciones Aprendidas

- 💡 El precedente de `US-3.1.1` (`skip_bdd: true` para US técnicas de infraestructura) evitó
  generar un `.feature` que no hubiese aportado sobre lo que ya cubren los tests de
  integración/unitarios.
- ⚠️ `codeguard` necesita `.venv/bin` en el `PATH` del proceso — sin eso, `vulture`/`codespell`
  (instalados en el venv) se reportan como "not installed" pese a estar disponibles.
- 💡 Testear WebSockets con `TestClient` requiere publicar mensajes vía `client.portal.call(...)`
  (no `asyncio.run(...)` desde el thread del test) para correr en el mismo loop de eventos que
  las conexiones abiertas — de lo contrario los objetos `WebSocket` no son thread-safe entre loops.
- ✅ El patrón de "reemplazar el atributo privado por un Fake después de construir el adapter"
  (ya usado en `tests/unit/inc5/test_comision_consulta_port_in_process.py`) se replicó sin
  fricción para `ComisionConsultaPortInProcess`.

---

## Componentes a Implementar

### 1. Entities — Puertos nuevos (sin dependencias externas)

- [x] `src/actividad_evaluativa/entities/ports/canal_tiempo_real_port.py`
  - `CanalTiempoRealPort` (ABC) — `async def publicar(sesion_id: UUID, mensaje: dict) -> None`
  - Sin conocer FastAPI ni WebSockets, mismo criterio que `NotificacionPort`
- [x] `src/actividad_evaluativa/entities/ports/comision_consulta_port.py`
  - `ComisionConsultaPort` (ABC) — `async def obtener_materia_id(comision_id: UUID) -> UUID | None`
  - Dirección inversa de `MateriaConsultaPort` ya existente

### 2. Frameworks — Canal de tiempo real (WebSockets)

- [x] `src/actividad_evaluativa/frameworks/websockets/__init__.py`
- [x] `src/actividad_evaluativa/frameworks/websockets/connection_manager.py`
  - `ConnectionManager` — `dict[UUID, set[WebSocket]]` por `sesion_id`
  - `conectar(sesion_id, websocket)`, `desconectar(sesion_id, websocket)`, `enviar_a_sesion(sesion_id, mensaje: dict)`
  - `enviar_a_sesion` ignora silenciosamente conexiones ya cerradas (no propaga excepción)
- [x] `src/actividad_evaluativa/frameworks/websockets/websocket_canal_tiempo_real.py`
  - `WebSocketCanalTiempoReal(CanalTiempoRealPort)` — delega en un `ConnectionManager` inyectado

### 3. Frameworks — Adapter de ComisionConsultaPort

- [x] `src/actividad_evaluativa/frameworks/adapters/comision_consulta_port_in_process.py`
  - `ComisionConsultaPortInProcess(ComisionConsultaPort)` — invoca
    `SQLAlchemyComisionRepository(session).obtener_por_id(comision_id)` de Identidad in-process
    (único punto de este BC que importa `src.identidad` para este propósito)

### 4. Dependencies (composition root del BC)

- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - Wiring de un `ConnectionManager` singleton del proceso (vive fuera del ciclo de request/response, mismo criterio que el `lifespan` de `US-3.2.4`)
  - Wiring de `WebSocketCanalTiempoReal` sobre ese singleton
  - Wiring de `ComisionConsultaPortInProcess(session)`

### 5. Frameworks — Router y autenticación WebSocket

- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - Router nuevo, prefix `/sesiones-en-vivo`
  - `WS /sesiones-en-vivo/{sesion_id}/canal?token=<jwt>`:
    - Verifica el JWT (query param, vía `JWTIssuerPort.verificar()` ya existente) antes de
      aceptar la conexión — código de cierre `1008` si falta/inválido/expirado
    - Acepta y registra en `ConnectionManager` bajo `sesion_id`
    - En `WebSocketDisconnect`, desregistra sin propagar la excepción

### 6. Integración con `src/app.py`

- [x] Registrar `sesiones_en_vivo_router` en `src/app.py` (mismo patrón que los routers ya
  registrados del BC)

---

## Tests — solo referencia (no ejecutar en esta fase)

> Nota: Tests → Fases 4 y 5. No se implementan en Fase 3, solo se referencian acá para que la
> secuencia de componentes los deje listos para probar.

- `tests/integration/inc6/test_canal_tiempo_real.py` — broadcast/aislamiento/desconexión sobre `TestClient.websocket_connect`
- `tests/unit/inc6/test_comision_consulta_port.py` — `obtener_materia_id` con Fake de `ComisionRepositoryPort`

---

## Orden de implementación (bottom-up, por dependencia)

1. `CanalTiempoRealPort` + `ComisionConsultaPort` (entities/ports) — sin dependencias
2. `ConnectionManager` (frameworks/websockets) — sin dependencias del BC
3. `WebSocketCanalTiempoReal` — depende de (2)
4. `ComisionConsultaPortInProcess` — depende de `SQLAlchemyComisionRepository` (Identidad, ya existente)
5. `sesiones_en_vivo_router.py` (endpoint WS) — depende de (2)/(3) y de `JWTIssuerPort` (ya existente)
6. `dependencies.py` — wiring de todo lo anterior
7. `src/app.py` — registra el router

**Estado:** 6/6 tareas completadas
