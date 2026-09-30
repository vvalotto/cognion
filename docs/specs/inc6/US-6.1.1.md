# US-6.1.1: Infraestructura de tiempo real (WebSockets) y `ComisionConsultaPort` de Actividad Evaluativa

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.1`
**Tipo**: `infra backend` (técnica — sin comando de negocio propio)
**Agregado principal afectado**: — (infraestructura transversal a los dos aggregates del modo en vivo)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **el canal de broadcast en tiempo real por sesión (WebSockets) y el puerto de consulta
de Comisión que resuelve `materia_id` a partir de `comision_id`**,
para **que `US-6.1.2`/`US-6.1.3`/`US-6.1.4` (y toda la Iteración 2) tengan sobre qué transmitir
cada evento de dominio a los participantes conectados, y de dónde resolver la materia de una
sesión creada desde una Comisión puntual**.

---

## Contexto del dominio

### Problema

Primer uso real de WebSockets del proyecto — prometido en `ARQ_v1.md`/`ADR-002` pero nunca
implementado (todo el proyecto hasta `BL-010` es HTTP request/response). El modelo de dominio
(`BC-actividad-evaluativa-modelo.md` §16) ya fija el **contrato** de qué evento dispara qué
mensaje y a quién, pero deja el diseño técnico del canal (protocolo, autenticación,
reconexión) como "pendiente de definir en la spec de implementación" (§17, última nota) — esta
US es esa definición.

Dos problemas técnicos nuevos, sin precedente en el proyecto:

1. **Autenticación sobre WebSocket.** El mecanismo JWT existente (`get_current_user`,
   `shared/interface_adapters/security/get_current_user.py`) depende del header
   `Authorization: Bearer <token>` vía `HTTPBearer` — la API nativa `WebSocket` del navegador
   (`new WebSocket(url)`) no permite fijar headers custom en el handshake. Se resuelve pasando
   el JWT como query param (`?token=...`) en la URL de conexión, verificado con el mismo
   `JWTIssuerPort.verificar()` ya existente — sin mecanismo de auth nuevo, solo un punto de
   entrada distinto para el mismo JWT.
2. **Broadcast desde un Use Case sin romper Clean Architecture.** `use_cases/` solo puede
   importar `entities/` (`CLAUDE.md`) — igual que `NotificacionPort`
   (`entities/ports/notificacion_port.py`, ya usado por `US-3.1.2`/`US-3.3.2`), la publicación
   en tiempo real se abstrae como un puerto nuevo en `entities/ports/`, con la implementación
   real (que sí conoce objetos `WebSocket` de FastAPI) viviendo en `frameworks/`.

Segundo problema, independiente del anterior: `ActividadEvaluativaEnVivo` (`US-6.1.2`) se crea
con `comision_id` única y obligatoria (`BC-actividad-evaluativa-modelo.md` §14, §17 punto 11) —
a diferencia de `ActividadEvaluativaPeriodoAbierto`, que recibe `materia_id` directamente. No
existe hoy ningún puerto en Actividad Evaluativa que resuelva `materia_id` a partir de
`comision_id` (la integración existente, `MateriaConsultaPort`, va en la dirección contraria:
Actividad Evaluativa consulta una `Materia` que ya conoce por id).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (nuevo) | `CanalTiempoRealPort` | `publicar(sesion_id: UUID, mensaje: dict) -> None` — definido en `entities/ports/`, sin conocer FastAPI ni WebSockets. Los Use Case de `US-6.1.2` a `US-6.1.4` y de la Iteración 2 lo invocan tras persistir cada evento de dominio (§16 de la tabla de eventos→mensajes) |
| Adapter (nuevo) | `WebSocketCanalTiempoReal` | Implementa `CanalTiempoRealPort` sobre un `ConnectionManager` en memoria: `dict[UUID, set[WebSocket]]` indexado por `sesion_id` — sin tabla de outbox propia, mismo criterio de "no sobre-diseñar para el volumen real" (30-60 conexiones concurrentes) ya aplicado en `VerificadorDeVencimientos` (§6b) |
| Endpoint FastAPI (nuevo) | `WS /sesiones-en-vivo/{sesion_id}/canal?token=<jwt>` | Acepta la conexión si el JWT es válido (Docente o Estudiante, cualquiera de los dos roles — ambos se suscriben al mismo canal), la registra en el `ConnectionManager` bajo `sesion_id`, y la desregistra al desconectarse (`WebSocketDisconnect`) |
| Port (nuevo) | `ComisionConsultaPort` (Actividad Evaluativa → Identidad) | `obtener_materia_id(comision_id: UUID) -> UUID \| None` — dirección inversa de `MateriaConsultaPort` ya existente, mismo patrón que el puerto homónimo de Banco de Preguntas/Analytics/Notificaciones (cada BC arma su propia copia, sin compartir el puerto entre BCs) |
| Adapter (nuevo) | `ComisionConsultaPortInProcess` | Implementa `ComisionConsultaPort` invocando `ComisionRepositoryPort.obtener_por_id()` de Identidad in-process (`SQLAlchemyComisionRepository`, ya existente) — mismo criterio de acoplamiento consciente (`ADR-006`) que `materia_consulta_port_in_process.py` del propio BC |

---

## Especificacion del comportamiento

### Precondicion

- `BL-010` cerrada. Sin infraestructura de tiempo real en el proyecto — primer WebSocket.
- Event store del BC ya existente (`US-3.1.1`) — no requiere migración ni extensión de código:
  `EventStorePort.append`/`load` ya reciben `aggregate_type` como `str` libre (sin `CHECK`
  constraint en la tabla `events`, verificado en `migrations/versions/9244e3956c69_*.py`), por
  lo que `"ActividadEvaluativaEnVivo"`/`"ParticipacionEnVivo"` no exigen ningún cambio de
  infraestructura — los usará directamente `US-6.1.2` en adelante.

### Postcondicion

- `CanalTiempoRealPort.publicar(sesion_id, mensaje)` entrega `mensaje` (un `dict`
  JSON-serializable) a todas las conexiones WebSocket activas suscriptas a `sesion_id` en el
  momento de la llamada — conexiones que se desconectaron antes se ignoran sin excepción.
- `WS /sesiones-en-vivo/{sesion_id}/canal?token=<jwt>` rechaza la conexión (código de cierre
  `1008`, política violada) si el JWT falta, es inválido o expiró — mismo criterio de error que
  `get_current_user` en HTTP, sin verificación de rol adicional (Docente y Estudiante comparten
  el mismo canal de lectura, §16).
- `ComisionConsultaPort.obtener_materia_id(comision_id)` devuelve el `materia_id` de la
  Comisión, o `None` si `comision_id` no existe — sin lanzar excepción, mismo contrato que
  `MateriaConsultaPort.obtener()`.
- Un test de integración prueba el ciclo completo de `WebSocketCanalTiempoReal`: dos clientes
  conectados al mismo `sesion_id` reciben el mismo mensaje publicado; un cliente conectado a
  otro `sesion_id` no lo recibe; un cliente desconectado no rompe la publicación a los demás.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Un mensaje publicado en `sesion_id=A` nunca llega a una conexión suscripta a `sesion_id=B` — aislamiento por canal, mismo criterio que el aislamiento de streams del event store (`BC-actividad-evaluativa-modelo.md` §6). |
| — | La desconexión de un cliente (`WebSocketDisconnect`, refresh de página, cierre de pestaña) nunca lanza una excepción no controlada hacia `publicar()` — se remueve del `ConnectionManager` de forma silenciosa. |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura de tiempo real y ComisionConsultaPort (US-6.1.1)

  Scenario: Broadcast a todas las conexiones del mismo canal
    Given dos clientes WebSocket conectados a "/sesiones-en-vivo/<sesion_id>/canal" con un JWT válido
    When se invoca CanalTiempoRealPort.publicar(sesion_id, {"tipo": "prueba"})
    Then ambos clientes reciben el mensaje

  Scenario: Aislamiento entre canales
    Given un cliente conectado al canal de sesion_id=A y otro al canal de sesion_id=B
    When se publica un mensaje en el canal de sesion_id=A
    Then solo el cliente de sesion_id=A lo recibe

  Scenario: Rechazo de conexión sin JWT válido
    Given un intento de conexión WebSocket sin query param "token" (o con un JWT expirado/inválido)
    When el servidor procesa el handshake
    Then la conexión se cierra con código 1008, sin quedar registrada en ningún canal

  Scenario: Desconexión no rompe el broadcast a los demás
    Given tres clientes conectados al mismo canal, uno de los cuales cierra su conexión
    When se publica un mensaje inmediatamente después
    Then los dos clientes restantes reciben el mensaje sin error del lado del servidor

  Scenario: Resolución de materia_id desde comision_id
    Given una Comisión existente con materia_id=<uuid-materia>
    When se invoca ComisionConsultaPort.obtener_materia_id(comision_id)
    Then el resultado es <uuid-materia>

  Scenario: Comisión inexistente
    Given un comision_id que no corresponde a ninguna Comisión
    When se invoca ComisionConsultaPort.obtener_materia_id(comision_id)
    Then el resultado es None
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — primer uso de WebSockets del proyecto. Decisión tomada dentro de esta US (no
  amerita ADR propio: es un detalle de implementación de `ADR-002`/`ARQ_v1.md`, que ya
  prometían WebSockets como mecanismo de transporte para este caso de uso): autenticación por
  query param (no hay alternativa nativa de header en el cliente `WebSocket` del navegador) y
  `ConnectionManager` en memoria de un solo proceso, sin outbox ni cola de mensajes — válido a
  la escala real (30-60 conexiones por sesión), documentado como reversible si el volumen
  cambia, mismo criterio ya aplicado al read model de `US-3.2.4`.

**Capa(s) afectadas:**
- [x] Entities — `CanalTiempoRealPort` (`entities/ports/`), `ComisionConsultaPort` (`entities/ports/`)
- [ ] Use Cases — sin Use Case propio (lo consumen `US-6.1.2` en adelante)
- [x] Interface Adapters — sin controller de negocio, pero el endpoint WS vive como router de
  `frameworks/api/`, mismo criterio que el resto de los endpoints del BC
- [x] Frameworks — `WebSocketCanalTiempoReal` + `ConnectionManager`, `ComisionConsultaPortInProcess`, router `sesiones_en_vivo_router.py` (arranca solo con el endpoint `WS .../canal`, sin endpoints de negocio todavía)
- [ ] Frontend — no aplica a esta iteración (backend únicamente, mismo criterio que la Iteración 1 del Incremento 3)

---

## Fuente de verdad UX

No aplica — infraestructura backend pura, sin pantalla.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/canal_tiempo_real_port.py` | `CanalTiempoRealPort` (interfaz `publicar`) |
| `src/actividad_evaluativa/entities/ports/comision_consulta_port.py` | `ComisionConsultaPort` (interfaz `obtener_materia_id`) |
| `src/actividad_evaluativa/frameworks/websockets/connection_manager.py` | `ConnectionManager` — registro/desregistro de `WebSocket` por `sesion_id`, envío a todos los suscriptos |
| `src/actividad_evaluativa/frameworks/websockets/websocket_canal_tiempo_real.py` | `WebSocketCanalTiempoReal` — implementa `CanalTiempoRealPort` sobre el `ConnectionManager` |
| `src/actividad_evaluativa/frameworks/adapters/comision_consulta_port_in_process.py` | `ComisionConsultaPortInProcess` |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py` | Router nuevo, prefix `/sesiones-en-vivo` — arranca con el endpoint `WS .../{sesion_id}/canal` |
| `src/actividad_evaluativa/frameworks/dependencies.py` | Wiring del `ConnectionManager` (singleton del proceso) y de `ComisionConsultaPortInProcess` |
| `src/app.py` | Registra `sesiones_en_vivo_router` |
| `tests/integration/inc6/test_canal_tiempo_real.py` | Tests de broadcast/aislamiento/desconexión sobre `TestClient.websocket_connect` |
| `tests/unit/inc6/test_comision_consulta_port.py` | Tests de `obtener_materia_id` con Fake de `ComisionRepositoryPort` |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §14 (`comision_id`
  única y obligatoria), §16 (contrato evento→mensaje→destinatario), §17 punto 11
- Decisiones: `ADR-002` (Event Sourcing + CQRS, WebSockets prometidos), `ADR-006` (integración
  directa entre BCs vía puerto in-process), `ADR-015` (BC único para ambos modos)
- Patrón a replicar: `src/actividad_evaluativa/entities/ports/notificacion_port.py` (puerto que
  cruza de `use_cases/` hacia infraestructura real sin romper Clean Architecture),
  `src/notificaciones/entities/ports/comision_consulta_port.py` (puerto de Comisión ya existente
  en otro BC, mismo criterio de "cada BC arma su propia copia")
- Consumida por: `US-6.1.2`, `US-6.1.3`, `US-6.1.4` y toda la Iteración 2
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
