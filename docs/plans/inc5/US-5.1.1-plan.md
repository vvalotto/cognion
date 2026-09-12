# Plan de Implementación: US-5.1.1 - Infraestructura del BC Notificaciones

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion

## Decisiones tomadas con Víctor antes de este plan

- **Librería SMTP:** reusar el patrón ya probado de `src/identidad/frameworks/smtp/notificador_smtp.py`
  (`smtplib` estándar + `asyncio.to_thread`, sin dependencias nuevas) en vez de `aiosmtplib`
  (candidata original de `BC-notificaciones-modelo.md` §5, descartada). Los dos adaptadores
  SMTP (Identidad y Notificaciones) quedan separados por BC — mismo criterio de duplicación
  consciente que `ADR-012` — pero comparten técnica.
- **Servidor SMTP para verificación automatizada:** sin Mailhog/Mailtrap instalado en este
  entorno. Se reutiliza el mismo patrón ya existente en
  `tests/integration/inc1/test_invitaciones_api_integration.py` (fixture `fake_smtp_server`,
  un servidor SMTP-stub embebido con `asyncio.start_server`) para el test de integración, y
  mocking de `smtplib.SMTP` (mismo patrón que `tests/unit/inc1/test_notificador_smtp.py`) para
  el test unitario. Mailhog real queda pendiente de instalación manual, sin bloquear el cierre
  de esta US — se documenta como nota en Fase 8, no como tarea de Fase 3.
- **Sin cambios en `.env.example` ni `pyproject.toml`:** las variables `SMTP_HOST`/`PORT`/
  `USER`/`PASSWORD`/`FROM` ya son genéricas en `src/settings.py` (no tienen prefijo de BC) y
  ya cubren lo que necesita `SmtpCanalEnvio`. No se agrega `aiosmtplib` como dependencia.

## Componentes a Implementar

### 1. BC Notificaciones — Ports (entities)

- [x] `src/notificaciones/entities/ports/canal_envio_port.py`
  - `CanalEnvioPort` (ABC): `enviar(destinatario_email: str, asunto: str, cuerpo: str) -> None`
  - Abstracción del canal de envío (RF-14, extensibilidad a futuro)
- [x] `src/notificaciones/entities/ports/comision_consulta_port.py`
  - `DestinatarioNotificacion` (`@dataclass(frozen=True)`): `estudiante_id: UUID`, `nombre: str`, `email: str`
  - `ComisionConsultaPort` (ABC):
    - `listar_comisiones_por_materia(materia_id: UUID) -> list[UUID]` — solo comisiones activas, usado cuando `comisiones_ids` llega vacío
    - `listar_destinatarios(comision_ids: list[UUID]) -> list[DestinatarioNotificacion]` — roster combinado sin duplicados

### 2. BC Notificaciones — Adapters (frameworks)

- [x] `src/notificaciones/frameworks/adapters/smtp_canal_envio.py`
  - `SmtpCanalEnvio(CanalEnvioPort)` — mismo patrón que `SmtpNotificador` de Identidad:
    `enviar()` delega a un método estático síncrono vía `asyncio.to_thread`, arma
    `EmailMessage` (`Subject`/`From`/`To` + `set_content(cuerpo)`), abre `smtplib.SMTP` contra
    `settings.smtp_host`/`smtp_port`, hace `starttls()`+`login()` solo si `settings.smtp_user`
    está seteado
  - No captura excepciones — el manejo de fallos ("loguear y continuar") es responsabilidad
    del Use Case consumidor (`US-5.1.2`/`US-5.1.3`), no de este adapter (mismo criterio que la
    invariante de la spec)
- [x] `src/notificaciones/frameworks/adapters/comision_consulta_port_in_process.py`
  - `ComisionConsultaPortInProcess(ComisionConsultaPort)` — envuelve
    `SQLAlchemyComisionQueryRepository` de Identidad (mismo patrón que
    `src/analytics/frameworks/adapters/comision_consulta_port_in_process.py`, `US-4.2.2`)
  - `listar_comisiones_por_materia`: llama `listar_comisiones_por_materia(materia_id)` de
    Identidad (activas por default) y devuelve solo los `id`
  - `listar_destinatarios(comision_ids)`: llama `listar_estudiantes_con_email(comision_id)` por
    cada comisión, combina resultados y deduplica por `id` (un `dict[UUID, DestinatarioNotificacion]`
    preserva el primero visto)

### 3. BC Notificaciones — Composition root (frameworks)

- [x] `src/notificaciones/frameworks/dependencies.py`
  - `get_canal_envio_port() -> CanalEnvioPort` → `SmtpCanalEnvio()`
  - `get_comision_consulta_port(session: AsyncSession) -> ComisionConsultaPort` → `ComisionConsultaPortInProcess(session)`
  - Sin controller/router — el BC no expone endpoint HTTP propio (spec §Impacto arquitectónico); estas factories quedan listas para que `US-5.1.2`/`US-5.1.3` las inyecten en sus Use Cases

### 4. BC Identidad — Extensión de `ComisionQueryPort`

- [ ] `src/identidad/entities/ports/comision_query_port.py`
  - Agregar `EstudianteConEmail` (`@dataclass(frozen=True)`): `id: UUID`, `nombre: str`, `email: str`
  - Agregar método abstracto `listar_estudiantes_con_email(comision_id: UUID) -> list[EstudianteConEmail]`
  - `listar_estudiantes` (existente) no se modifica — coexisten
  - ✅ Hecho — también se actualizó `tests/unit/inc1/_fakes.py::FakeComisionQueryRepository`
    con el método nuevo (`feedback_fakes_unit_tests_desactualizados`)
- [x] `src/identidad/interface_adapters/gateways/comision_query_repository.py`
  - Implementar `listar_estudiantes_con_email`: mismo query que `listar_estudiantes` (join
    `UsuarioModel`/`EstudianteModel` por `comision_id`), agregando `email=modelo.email` al DTO

### 5. BC Actividad Evaluativa — Contrato de `NotificacionPort` (sin cablear)

- [x] `src/actividad_evaluativa/entities/ports/notificacion_port.py`
  - `NotificacionPort` (ABC):
    - `notificar_apertura(actividad_id: UUID, materia_id: UUID, titulo: str, fecha_apertura: datetime, fecha_cierre: datetime, comisiones_ids: list[UUID]) -> None`
    - `notificar_cierre(actividad_id: UUID, materia_id: UUID, titulo: str, comisiones_ids: list[UUID]) -> None`
  - Docstring aclara: contrato only en esta US, ningún adapter lo implementa todavía, ningún
    Use Case lo invoca — se cablea recién en `US-5.1.2` (`NotificacionPortInProcess`,
    `BC-notificaciones-modelo.md` §5)

**Estado:** ✅ COMPLETADO — 8/8 tareas completadas

## Métricas de Tiempo (tracker real, no estimaciones humanas — ver `PRIN-001`)

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 1min 6s |
| 1 — Generación de Escenarios BDD | 0min 43s |
| 2 — Generación del Plan de Implementación | 4min 19s |
| 3 — Implementación Guiada por Tareas | 3min 57s |
| 4 — Tests Unitarios | 3min 0s |
| 5 — Tests de Integración | 4min 21s |
| 6 — Validación BDD | 5min 19s |
| 7 — Quality Gates | 12min 51s |
| 8 — Documentación | (en curso) |
| **Total (Fases 0-7)** | **~37 min** |

## Lecciones aprendidas

- Gap real detectado en Fase 2 (no en Fase 0): la spec proponía `aiosmtplib` como librería
  candidata sin confirmar, pero ya existía un adapter SMTP funcionando en Identidad
  (`ADR-012`, `smtplib` + `asyncio.to_thread`) con las mismas variables de entorno —
  decisión con Víctor: reusar ese patrón en vez de sumar una dependencia nueva.
- Sin Mailhog/Mailtrap instalado en este entorno — se optó por un servidor SMTP-stub embebido
  en los tests (mismo patrón ya usado en `tests/integration/inc1/test_invitaciones_api_integration.py`)
  en vez de bloquear el cierre de la US con una instalación de infraestructura.
- Extender un puerto ya consumido por otros BCs (`ComisionQueryPort` de Identidad) obliga a
  actualizar todos los Fakes que lo implementan en `tests/unit/` — se encontraron y corrigieron
  dos (`tests/unit/inc1/_fakes.py` y un fake local en `tests/unit/inc4/test_comisiones_query_controller.py`),
  ninguno anticipado en el plan original.
- Coverage gate (93.1%) quedó por debajo del umbral (95%) exclusivamente por deuda preexistente
  no introducida por esta US (`tiene_comisiones_asignadas`/`tiene_comisiones_creadas` sin test
  de integración) — reportado como chip aparte (`task_363ab6a5`) en vez de ensanchar el alcance.
