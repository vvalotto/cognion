# Arquitectura de Referencia — Cognión

> Versión: ARQ_v1  
> Fecha: 2026-07-08  
> Estado: borrador verificado  
> Basado en: RF_v1.md · RNF_v1.md
> Revisión 2026-07-16: el BC "Sesiones" se renombró a "Actividad Evaluativa" (`ADR-015`) —
> este documento no se reescribe, "sesión/sesiones" en el texto original (incluidos ADR-002 a
> ADR-006) se lee con ese significado. `docs/architecture/` usa el nombre nuevo.

---

## Drivers arquitectónicos

| # | Driver | Origen | Implicación |
|---|--------|--------|-------------|
| 1 | **Broadcast sincronizado en tiempo real** | RF-09 + Rendimiento ≤100ms | Canal persistente (WebSockets) para empujar ranking a 60 clientes simultáneos |
| 2 | **Persistencia atómica respuesta a respuesta** | RF-12 + Confiabilidad | Escrituras frecuentes y atómicas por respuesta; Unit of Work obligatorio |
| 3 | **Trazabilidad completa de eventos** | Observabilidad (decidido) | Event sourcing como mecanismo unificado de registro en BC Sesiones |
| 4 | **Equipo unipersonal + deployment sin fricción** | Mantenibilidad + Administrabilidad | Complejidad operacional mínima; CI/CD obligatorio |
| 5 | **Modelo de dominio extensible** | RF-05 + Mantenibilidad | Polimorfismo en tipos de pregunta; dominio aislado de infraestructura |
| 6 | **Control de acceso en toda la frontera** | RF-02 + Seguridad | RBAC + JWT validado en cada operación del servidor |
| 7 | **Dos modos de sesión con ciclo de vida distinto** | RF-08/09/11/12 | Modelo de dominio que capture ambos modos sin contaminar el código de uno con el otro |

---

## Estilo arquitectónico

**Decisión:** Monolito modular con Arquitectura Limpia (Clean Architecture) interna

**Razón:** El driver 4 (equipo unipersonal) descarta microservicios — la complejidad operacional de un sistema distribuido no está justificada. La Clean Architecture responde a los drivers 5 y 7: el dominio vive aislado de la infraestructura, los Use Cases orquestan sin saber qué framework los ejecuta, y los dos modos de sesión pueden modelarse con pureza.

**Trade-off aceptado:** Mayor estructura inicial que un monolito layered clásico. La inversión en capas se justifica por la complejidad del dominio de Sesiones y la necesidad de extensibilidad futura.

**Capas (de adentro hacia afuera):**
```
Entities (reglas de negocio puras)
  └── Use Cases (orquestación de la aplicación)
        └── Interface Adapters (controllers, presenters, gateways)
              └── Frameworks & Drivers (FastAPI, PostgreSQL, React, WebSockets)
```

---

## Bounded Contexts

| BC | Tipo DDD | Estilo interno | Responsabilidad |
|----|----------|---------------|-----------------|
| **Sesiones** | Core Domain | Clean Architecture + Event Sourcing + CQRS | Ciclo de vida de sesiones en vivo y período abierto; ranking; persistencia de respuestas |
| **Banco de preguntas** | Supporting | Clean Architecture + CRUD | PreguntaPlantilla con metadatos; filtrado y selección |
| **Identidad** | Generic | Clean Architecture + CRUD | Usuarios, roles, JWT |
| **Notificaciones** | Generic | Clean Architecture + Event-driven | Email en apertura/cierre de sesiones; extensible a otros canales |
| **Analytics** | Supporting | Read Models (solo lectura) | Proyecciones desde event store de Sesiones; métricas de uso |

### Lenguaje ubicuo por BC

| BC | Términos propios |
|----|-----------------|
| **Sesiones** | Sesión, PreguntaAsignada, Respuesta, Ranking, SesionEnVivo, SesionPeriodoAbierto |
| **Banco de preguntas** | PreguntaPlantilla, TipoPregunta, UnidadTemática, Dificultad, Importancia |
| **Identidad** | Usuario, Rol, Credencial, Token |
| **Notificaciones** | Notificación, Canal, Evento de integración |
| **Analytics** | ReadModel, Proyección, MétricaDeSesión |

---

## Stack tecnológico

| Capa | Tecnología | Estado |
|------|-----------|--------|
| Backend | Python + FastAPI | Decidido |
| API sincrónica | REST (JSON) | Decidido |
| API tiempo real | WebSockets (FastAPI nativo) | Decidido |
| ORM | SQLAlchemy async | Decidido |
| Persistencia | PostgreSQL | Decidido |
| Event store | Tabla append-only en PostgreSQL (payload JSONB) | Decidido |
| Frontend | React + TypeScript | Decidido |
| Estilos / UI | Tailwind CSS + shadcn/ui | Decidido |
| Containerización | Docker | Decidido |
| Hosting | Fly.io (testing y staging) | Decidido — producción pendiente |
| CI/CD | GitHub Actions | Decidido |
| Autenticación | JWT — python-jose | Decidido |

---

## Aspectos transversales

| Aspecto | Estrategia | Responsable en arquitectura | Estado |
|---------|-----------|----------------------------|--------|
| Observabilidad | Event sourcing en BC Sesiones + healthcheck endpoint público | BC Sesiones / Infrastructure | Decidido |
| Auth / Autorización | JWT + RBAC; validación por dependency injection en FastAPI | Interface Adapters | Decidido |
| Manejo de errores | Excepciones tipadas en dominio; error handler global en FastAPI para infraestructura | Domain + Interface Adapters | Decidido |
| Validación de entrada | Pydantic en frontera API; invariantes de negocio en entidades de dominio | Interface Adapters / Domain | Decidido |
| Configuración y secretos | Variables de entorno; Fly.io secrets para producción; `.env` local fuera del repo | Infrastructure | Decidido |
| Transaccionalidad | Unit of Work con SQLAlchemy async por Use Case | Application / Infrastructure | Decidido |
| Integración Sesiones → Notificaciones | Llamada directa entre Use Cases ⚠️ | Application layer | Decidido (ver ADR-006) |
| Estándares de interfaz | WCAG A; shadcn/ui como librería de componentes | Frontend | Parcial — fuente mínima abierta |

---

## Compromisos documentados

- **Llamada directa vs. evento en memoria (Sesiones → Notificaciones)** — Se eligió llamada directa para simplificar la implementación. Trade-off: acoplamiento entre BCs. Documentado como deuda técnica consciente en ADR-006.

- **Monolito vs. microservicios** — Monolito modular por complejidad operacional mínima con equipo unipersonal. La modularidad por BCs permite partir el monolito en el futuro si la escala lo requiere.

- **PostgreSQL vs. SQLite** — PostgreSQL para manejar escrituras concurrentes en sesiones de período abierto. SQLite descartado por contención de escritura ante 60 alumnos simultáneos.

- **Sin PWA** — Sistema exclusivamente online. La confiabilidad ante desconexión se garantiza mediante persistencia server-side respuesta a respuesta, no capacidad offline del cliente.

---

## Ítems arquitectónicos abiertos

- **Tamaño mínimo de fuente para pantalla proyectada** — se define en etapa de diseño UX. *Desbloqueado por:* inicio del diseño UX del portal del docente.
- **Infraestructura definitiva** — Fly.io confirmado para testing; producción pendiente de decisión (nube vs. servidor institucional FIUNER). *Desbloqueado por:* decisión institucional.
- **Mecanismo de backup** — depende del proveedor de hosting definitivo. *Desbloqueado por:* decisión de infraestructura de producción.

---

## ADRs

---

### ADR-001 — Monolito modular con Clean Architecture (vs. microservicios)

**Estado:** Propuesto  
**Fecha:** 2026-07-08

**Contexto**  
El sistema es desarrollado y mantenido por un único desarrollador. Tiene un dominio de complejidad media-alta (dos modos de sesión, event sourcing, tiempo real) pero una escala modesta (hasta 60 usuarios simultáneos). Se necesita deployment frecuente y CI/CD sin fricción.

**Decisión**  
Monolito modular con Clean Architecture interna. Los Bounded Contexts son módulos del mismo proceso, no servicios independientes.

**Razón**  
Microservicios introducen complejidad operacional (múltiples deployments, comunicación de red entre servicios, distributed tracing) que no está justificada para un equipo de una persona y la escala proyectada. La modularidad por BCs dentro del monolito preserva la separación conceptual sin el overhead de distribución.

**Consecuencias**  
- ✅ Deployment simple: un único artefacto Docker
- ✅ Debugging local sin infraestructura de red entre servicios
- ✅ Menor latencia: comunicación en memoria entre BCs
- ⚠️ Escalar partes independientes en el futuro requerirá partir el monolito

---

### ADR-002 — Event Sourcing + CQRS en BC Sesiones (vs. CRUD estándar)

**Estado:** Propuesto  
**Fecha:** 2026-07-08

**Contexto**  
El BC Sesiones es el Core Domain del sistema. Tiene requerimientos de observabilidad (reconstruir qué pasó en una sesión), confiabilidad (persistencia atómica de respuestas) y ciclo de vida complejo (dos modos con transiciones de estado). El RNF de Observabilidad define event sourcing como decisión tomada.

**Decisión**  
Event Sourcing como mecanismo de persistencia en BC Sesiones, combinado con CQRS: los commands modifican el estado mediante eventos inmutables; los read models (Analytics) se proyectan desde el event store.

**Razón**  
Event sourcing entrega naturalmente el audit trail requerido por Observabilidad, la trazabilidad de sesiones, y el historial de respuestas. CRUD requeriría logging adicional para lograr el mismo nivel de trazabilidad. Los read models de Analytics son una consecuencia directa sin duplicar lógica de persistencia.

**Consecuencias**  
- ✅ Trazabilidad completa de cualquier sesión sin logging adicional
- ✅ Read models generados desde el mismo stream de eventos
- ✅ Reconstrucción del estado del aggregate desde eventos (event replay)
- ⚠️ Mayor complejidad conceptual que CRUD
- ⚠️ Consultas ad-hoc sobre el estado actual requieren proyecciones

---

### ADR-003 — FastAPI como framework backend (vs. Django + Channels)

**Estado:** Propuesto  
**Fecha:** 2026-07-08

**Contexto**  
El sistema requiere WebSockets para sesiones en vivo y REST para las demás operaciones. El lenguaje es Python. Se necesita un framework que soporte async nativo, WebSockets, y que no imponga estructura que conflictúe con Clean Architecture.

**Decisión**  
FastAPI como único framework backend.

**Razón**  
FastAPI es async nativo y soporta WebSockets en el mismo proceso sin infraestructura adicional. Django Channels requiere un channel layer (típicamente Redis) y workers separados, añadiendo complejidad operacional que el driver 4 (equipo unipersonal) no puede absorber. FastAPI es delgado: no impone modelo de datos ni estructura de directorios, lo que permite implementar Clean Architecture sin fricciones.

**Consecuencias**  
- ✅ WebSockets y REST en el mismo proceso async
- ✅ Sin infraestructura adicional de mensajería
- ✅ Pydantic integrado para validación en Interface Adapters
- ✅ OpenAPI/Swagger automático
- ⚠️ Sin admin integrado (no es necesario para este sistema)

---

### ADR-004 — PostgreSQL como base de datos (vs. SQLite)

**Estado:** Propuesto  
**Fecha:** 2026-07-08

**Contexto**  
El sistema necesita soportar hasta 60 alumnos confirmando respuestas simultáneamente en sesiones de período abierto. El event store requiere escrituras append-only frecuentes. El hosting es Fly.io.

**Decisión**  
PostgreSQL como única base de datos. El event store es una tabla append-only dentro de la misma instancia PostgreSQL.

**Razón**  
SQLite permite un único escritor a la vez. Con 60 respuestas simultáneas en período abierto, la contención de escritura en SQLite es un riesgo real contra el driver 2 (persistencia atómica). PostgreSQL maneja escrituras concurrentes correctamente. Fly.io ofrece PostgreSQL administrado, eliminando el overhead de operación. El soporte JSONB de PostgreSQL es ideal para los payloads del event store.

**Consecuencias**  
- ✅ Escrituras concurrentes sin contención
- ✅ JSONB para payloads del event store (consultable e indexable)
- ✅ Fly.io Postgres administrado sin overhead de operación
- ⚠️ Ligeramente más complejo de configurar localmente que SQLite (mitigado con Docker Compose)

---

### ADR-005 — WebSockets para sesiones en vivo (vs. polling o SSE)

**Estado:** Propuesto  
**Fecha:** 2026-07-08

**Contexto**  
Las sesiones en vivo requieren sincronización bidireccional: el docente envía comandos (cerrar pregunta, avanzar) y el servidor hace broadcast del ranking a todos los clientes. El tiempo de procesamiento server-side debe ser ≤100ms.

**Decisión**  
WebSockets para toda la comunicación durante sesiones en vivo.

**Razón**  
SSE es unidireccional (servidor → cliente) — no permite que el alumno envíe respuestas ni que el docente cierre preguntas por el mismo canal. Polling agrega latencia variable y carga innecesaria al servidor. WebSockets mantiene una conexión TCP persistente y bidireccional: el docente envía el comando de cierre, el servidor calcula el ranking y hace push a los 60 clientes conectados, todo en el mismo ciclo async de FastAPI.

**Consecuencias**  
- ✅ Comunicación bidireccional sin overhead de polling
- ✅ Latencia predecible (no hay round-trips adicionales)
- ✅ Soportado nativamente por FastAPI sin dependencias adicionales
- ⚠️ Las conexiones WebSocket persisten durante toda la sesión (recurso TCP por cliente — aceptable a 60 conexiones)

---

### ADR-006 — Integración directa entre BC Sesiones y BC Notificaciones (vs. evento en memoria)

**Estado:** Propuesto  
**Fecha:** 2026-07-08

**Contexto**  
Cuando se abre o cierra una sesión de período abierto, el BC Notificaciones debe enviar un email al alumno. Se necesita definir cómo el BC Sesiones desencadena esa acción sin violar los límites de BC.

**Decisión**  
El Use Case de Sesiones llama directamente al Use Case de Notificaciones al completar la operación que desencadena la notificación.

**Razón**  
Un event bus en memoria (observer, mediator) desacoplaría los BCs correctamente pero agrega un mecanismo de infraestructura adicional a mantener. Para un sistema con un único desarrollador y dos integraciones concretas (apertura y cierre de sesión), el overhead no se justifica en esta etapa.

**Consecuencias**  
- ✅ Implementación simple y directa
- ✅ Sin infraestructura adicional de mensajería
- ⚠️ Acoplamiento entre BC Sesiones y BC Notificaciones — cambios en la interfaz de Notificaciones impactan en Sesiones
- ⚠️ Deuda técnica consciente: si Notificaciones crece (más canales, más eventos), conviene migrar a evento en memoria
