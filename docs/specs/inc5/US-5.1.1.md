# US-5.1.1: Infraestructura del BC Notificaciones

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5.1`
**Tipo**: `feat backend` (técnica)
**Agregado principal afectado**: — (BC reactivo sin aggregate propio, `BC-notificaciones-modelo.md` §2)
**Bounded Context**: Notificaciones (nuevo) + Identidad (query nueva)

---

## Descripcion (lenguaje de negocio)

Como **Sistema**,
quiero **contar con los puertos y adapters de infraestructura del BC Notificaciones — resolución
de destinatarios con email y envío por SMTP real de prueba**,
para **que `US-5.1.2`/`US-5.1.3` puedan disparar el envío de un email real sin tener que
resolver de nuevo el mecanismo de destinatarios ni el canal de envío**.

---

## Contexto del dominio

### Problema

`BC-notificaciones-modelo.md` §5 diseñó tres puertos nuevos que no existen todavía en ningún
BC: `CanalEnvioPort` (propio de Notificaciones, abstrae el medio de envío), `ComisionConsultaPort`
(copia propia de Notificaciones hacia Identidad — **no** reutiliza el `ComisionQueryPort` ya
existente porque ninguna copia actual expone `email`, solo `id`/`nombre`, pensadas para
selectores de UI) y `NotificacionPort` (dueño de Actividad Evaluativa, punto de disparo — se
define en esta US como contrato, y se cablea con su implementación real recién en `US-5.1.2`
cuando exista al menos un método real que llamar; sin llamador real todavía, este puerto queda
sin consumidor hasta esa US). Esta US arma la infraestructura de punta a punta del lado de
Notificaciones e Identidad; `US-5.1.2`/`US-5.1.3` la consumen para los dos disparos concretos de
RF-14.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| BC nuevo | `src/notificaciones/` | Primer BC puramente reactivo — sin aggregate, sin persistencia propia (`BC-notificaciones-modelo.md` §2) |
| Port (nuevo, Notificaciones) | `CanalEnvioPort` | `enviar(destinatario_email, asunto, cuerpo) -> None` — abstracción del canal de envío (RF-14 pide extensibilidad a otros medios) |
| Adapter (nuevo, Notificaciones) | `SmtpCanalEnvio` | Implementa `CanalEnvioPort` vía `aiosmtplib` contra SMTP local de prueba (Mailhog/Mailtrap), configurado por `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` |
| DTO (nuevo, Notificaciones) | `DestinatarioNotificacion` | `estudiante_id`, `nombre`, `email` |
| Port (nuevo, Notificaciones) | `ComisionConsultaPort` | `listar_comisiones_por_materia(materia_id) -> list[UUID]` (solo cuando `comisiones_ids` llega vacío) y `listar_destinatarios(comision_ids: list[UUID]) -> list[DestinatarioNotificacion]` (roster combinado, sin duplicados) |
| Adapter (nuevo, Notificaciones) | adapter in-process | Implementa `ComisionConsultaPort` invocando el query nuevo de Identidad (siguiente fila), mismo patrón que `MateriaConsultaPort`/`ComisionConsultaPort` de Analytics (`US-4.2.2`) |
| Port (extendido, Identidad) | `ComisionQueryPort.listar_estudiantes_con_email(comision_id) -> list[EstudianteConEmail]` | Método nuevo, separado de `listar_estudiantes` (que no expone `email` y sigue igual para sus consumidores actuales — Analytics, Banco de Preguntas) |
| DTO (nuevo, Identidad) | `EstudianteConEmail` | `id`, `nombre`, `email` — mismo criterio de DTO mínimo por consumidor que `EstudianteResumen` |
| Port (nuevo, Actividad Evaluativa) | `NotificacionPort` | Contrato only en esta US (`notificar_apertura(...)`/`notificar_cierre(...)`, ambos `-> None`, nunca propagan excepción) — sin implementación in-process todavía, se cablea en `US-5.1.2` |
| Composition root (nuevo, Notificaciones) | `src/notificaciones/frameworks/dependencies.py` | Arma `SmtpCanalEnvio` + adapter de `ComisionConsultaPort` |

---

## Especificacion del comportamiento

### Precondicion

- `BL-008` cerrada, `BC-notificaciones-modelo.md` aprobado (`US-5.0.1`).
- Servidor SMTP de prueba local disponible (Mailhog, a instalar/documentar en esta US —
  `docs/plans/CHECKLIST-INSTALACION.md` gana una entrada nueva, mismo criterio que PostgreSQL
  vía Homebrew).

### Postcondicion

- `ComisionConsultaPort.listar_destinatarios([comision_x_id, comision_y_id])` devuelve el
  roster combinado de ambas comisiones, sin duplicados si un estudiante está inscripto en más
  de una.
- `ComisionConsultaPort.listar_comisiones_por_materia(materia_id)` devuelve todas las comisiones
  activas de la materia — usado solo cuando `comisiones_ids` llega vacío desde el disparo
  (`US-5.1.2`/`US-5.1.3`).
- `Identidad.ComisionQueryPort.listar_estudiantes_con_email(comision_id)` devuelve el mismo
  roster que `listar_estudiantes(comision_id)` (mismos estudiantes), con `email` incluido.
  Comisión sin inscriptos → lista vacía en ambos.
- `CanalEnvioPort.enviar(email, asunto, cuerpo)` (`SmtpCanalEnvio`) entrega el mensaje al
  servidor SMTP configurado — verificable contra la bandeja de Mailhog en un smoke test manual,
  sin asumir contenido de negocio todavía (esta US no define el asunto/cuerpo real de RF-14,
  eso es `US-5.1.2`/`US-5.1.3`).
- `NotificacionPort` (Actividad Evaluativa) queda declarado como interfaz, sin implementación
  cableada — ningún Use Case de Actividad Evaluativa lo invoca todavía.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Notificaciones nunca importa código de `src/identidad/` directamente — `ComisionConsultaPort` es el único punto de acceso, mismo patrón arquitectónico que el resto de comunicación entre BCs (`CLAUDE.md`). |
| — | `listar_estudiantes_con_email` es un método nuevo de un puerto ya existente, no reemplaza `listar_estudiantes` — ambos coexisten para no romper a Analytics/Banco de Preguntas. |
| — | `SmtpCanalEnvio` no propaga excepciones hacia quien lo invoca en esta US — solo expone `enviar()`; la política de "loguear y continuar" ante un fallo (`BC-notificaciones-modelo.md` §6 decisión 4) es responsabilidad del Use Case que la use en `US-5.1.2`/`US-5.1.3`, no de esta US. |

---

## Criterios de aceptacion

```gherkin
Feature: Infraestructura del BC Notificaciones (US-5.1.1)

  Scenario: Roster combinado de varias comisiones sin duplicados
    Given un estudiante inscripto en las comisiones A y B
    And otro estudiante inscripto solo en la comisión A
    When se invoca ComisionConsultaPort.listar_destinatarios([A, B])
    Then el roster devuelto tiene 2 destinatarios, sin el primero repetido

  Scenario: Resolver todas las comisiones de una materia
    Given una materia con 3 comisiones activas y 1 inactiva
    When se invoca ComisionConsultaPort.listar_comisiones_por_materia(materia_id)
    Then el roster devuelto tiene las 3 comisiones activas

  Scenario: Comisión sin estudiantes
    Given una comisión recién creada, sin inscripciones
    When se invoca ComisionConsultaPort.listar_destinatarios([comision_id])
    Then el roster devuelto está vacío

  Scenario: Query de Identidad expone email sin romper el consumidor existente
    Given una comisión con 2 estudiantes inscriptos
    When se invoca ComisionQueryPort.listar_estudiantes_con_email(comision_id)
    Then cada elemento incluye id, nombre y email
    And ComisionQueryPort.listar_estudiantes(comision_id) sigue devolviendo solo id y nombre

  Scenario: Envío real contra el SMTP local de prueba
    Given el servidor Mailhog corriendo localmente
    When se invoca CanalEnvioPort.enviar("estudiante@example.com", "Asunto de prueba", "Cuerpo de prueba")
    Then el mensaje aparece en la bandeja de Mailhog con ese asunto y destinatario
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — crea el quinto BC del sistema (`src/notificaciones/`, primer BC puramente reactivo)
  y fija la librería de envío de email (`aiosmtplib`, async, consistente con el resto del
  stack — a confirmar/ajustar en el plan si aparece un impedimento técnico). No amerita ADR
  nuevo — instancia `ADR-006`, ya cerrado.

**Capa(s) afectadas:**
- [x] Entities (Notificaciones) — `CanalEnvioPort`, `ComisionConsultaPort`, `DestinatarioNotificacion` (nuevos)
- [ ] Use Cases (Notificaciones) — ninguno todavía, se agregan en `US-5.1.2`/`US-5.1.3`
- [ ] Interface Adapters (Notificaciones) — no aplica, sin controller HTTP propio (BC reactivo, sin endpoint expuesto)
- [x] Frameworks (Notificaciones) — `SmtpCanalEnvio`, adapter in-process de `ComisionConsultaPort`, `dependencies.py`
- [x] Entities (Identidad) — `ComisionQueryPort.listar_estudiantes_con_email` (nuevo método), `EstudianteConEmail` (DTO nuevo)
- [x] Interface Adapters (Identidad) — `SQLAlchemyComisionQueryRepository` implementa el método nuevo
- [x] Entities (Actividad Evaluativa) — `NotificacionPort` (contrato nuevo, sin implementación cableada)
- [ ] Frontend — no aplica, RF-14 no tiene pantalla propia

---

## Fuente de verdad UX

No aplica — BC sin pantalla propia (`BC-notificaciones-modelo.md`, encabezado).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/notificaciones/entities/ports/canal_envio_port.py` | Nuevo — `CanalEnvioPort` |
| `src/notificaciones/entities/ports/comision_consulta_port.py` | Nuevo — `ComisionConsultaPort`, `DestinatarioNotificacion` |
| `src/notificaciones/frameworks/adapters/smtp_canal_envio.py` | Nuevo — `SmtpCanalEnvio` (`aiosmtplib`) |
| `src/notificaciones/frameworks/adapters/comision_consulta_port_in_process.py` | Nuevo |
| `src/notificaciones/frameworks/dependencies.py` | Nuevo — composition root del BC |
| `src/identidad/entities/ports/comision_query_port.py` | Agrega `listar_estudiantes_con_email` + `EstudianteConEmail` |
| `src/identidad/interface_adapters/gateways/comision_query_repository.py` | Implementa el método nuevo |
| `src/actividad_evaluativa/entities/ports/notificacion_port.py` | Nuevo — `NotificacionPort` (contrato, sin adapter todavía) |
| `docs/plans/CHECKLIST-INSTALACION.md` | Entrada nueva — instalación/arranque de Mailhog local |
| `.env.example` (o equivalente) | Variables `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` |
| `tests/unit/inc5/`, `tests/integration/inc5/` | Tests de los 3 ports/adapters nuevos |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-notificaciones-modelo.md` §5, §6
- `ADR-006` (integración directa entre BCs)
- Sin dependencia de otra US de esta iteración — desbloquea `US-5.1.2` y `US-5.1.3`
- Candidatas: `docs/plans/inc5/inc5-candidatas.md` §Iteración 1
- Issue: [#307](https://github.com/vvalotto/cognion/issues/307)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
