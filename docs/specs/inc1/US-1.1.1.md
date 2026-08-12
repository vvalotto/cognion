# US-1.1.1: Docente genera link de invitación para una comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Invitación`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **generar un link de invitación para una Comisión a la que estoy asignado**
para **que un Estudiante pueda registrarse a través de ese link y quedar asignado
automáticamente a mi comisión (RF-01)**.

---

## Contexto del dominio

### Problema

Sin invitación no hay forma de registrar un Estudiante — el registro no es abierto, requiere
un token emitido por un Docente autorizado sobre una comisión concreta. Depende de `US-1.1.0`
(debe existir el `Docente` y la `Comisión`, con el Docente en `docentes_asignados`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Invitación` | Token único, vigencia de 7 días, uso único |
| Command | `GenerarInvitacion(comision_id, docente_id)` | Crea la invitación |
| Domain Event | `InvitacionGenerada` | Señala la emisión |
| Port | `NotificadorPort` (adaptador SMTP, BC Identidad) | Envío del link por email (`ADR-012`) |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- `docente_id` (derivado del JWT) está presente en `Comisión.docentes_asignados` de
  `comision_id`.

### Postcondicion

- `Invitación` persistida con `token` único, `generada_en = ahora`,
  `expira_en = generada_en + 7 días` (calculado una única vez, `ADR-012`).
- Email enviado al destinatario indicado con el link de invitación (side-effect directo del
  handler, mismo comando — sin policy separada, `BC-identidad-modelo.md` §5, hot spot 3).
- Evento `InvitacionGenerada`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-08 | Un Docente debe estar en `docentes_asignados` de la `Comisión` para poder ejecutar `GenerarInvitacion` sobre ella — `DocenteNoAsignadoAComision` si no. |
| INV-ID-02 | `expira_en = generada_en + 7 días`, fijo al generar — no se recalcula ni se extiende en v1. |
| — | El `token` generado es único en todo el sistema. |

---

## Criterios de aceptacion

```gherkin
Feature: Generación de invitación por Docente

  Scenario: Docente asignado genera invitación
    Given un Docente autenticado presente en docentes_asignados de la Comisión "IS-2026-C1"
    When ejecuta GenerarInvitacion(comision_id, docente_id)
    Then el sistema persiste una Invitación con token único
    And expira_en queda fijado a 7 días desde ahora
    And se envía un email con el link de invitación
    And se emite el evento InvitacionGenerada

  Scenario: Rechazo por Docente no asignado a la comisión
    Given un Docente autenticado que NO está en docentes_asignados de la Comisión "IS-2026-C2"
    When intenta ejecutar GenerarInvitacion sobre esa comisión
    Then el sistema rechaza la operación con DocenteNoAsignadoAComision
    And ninguna Invitación se crea
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente (`ADR-012`)

**Capa(s) afectadas:**
- [x] Entities — `Invitación`, evento `InvitacionGenerada`
- [x] Use Cases — `GenerarInvitacionUseCase`
- [x] Interface Adapters — controller, `InvitacionRepositoryPort`, `NotificadorPort`
- [x] Frameworks — endpoint FastAPI, modelo SQLAlchemy + migración, adaptador SMTP
- [ ] Frontend — sin wireframe aprobado para esta pantalla; se opera por API en esta iteración

---

## Fuente de verdad UX

No aplica — `wireframes-identidad.md` no incluye una pantalla de "generar invitación"
(§4, fuera de alcance del wireframe actual). Esta US no toca `frontend/`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/invitacion.py` | Aggregate `Invitación` |
| `src/identidad/entities/eventos.py` | Agregar `InvitacionGenerada` |
| `src/identidad/entities/ports/invitacion_repository_port.py` | Puerto de persistencia |
| `src/identidad/entities/ports/notificador_port.py` | Puerto de envío de email (reutilizable desde `US-1.1.2`/`US-1.1.3`) |
| `src/identidad/use_cases/generar_invitacion.py` | Orquesta validación INV-ID-08, generación de token, envío |
| `src/identidad/interface_adapters/controllers/invitaciones_controller.py` | Validación de entrada, mapeo a use case |
| `src/identidad/interface_adapters/gateways/invitacion_repository.py` | Implementación SQLAlchemy |
| `src/identidad/frameworks/smtp/notificador_smtp.py` | Adaptador SMTP propio (`ADR-012`) |
| `src/identidad/frameworks/api/invitaciones_router.py` | Endpoint FastAPI (requiere rol `docente`) |
| `src/identidad/frameworks/db/models.py` | Modelo SQLAlchemy `invitacion` |
| `src/identidad/frameworks/db/migrations/` | Migración Alembic |

---

## Referencias

- Relacionada con: `US-1.1.0`, `US-1.1.2`, `US-1.1.3`, `ADR-012`
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` (§3, §4 `Invitación`)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
