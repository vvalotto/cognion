@US-1.1.1
Feature: Generación de invitación por Docente (US-1.1.1)
  Como Docente
  Quiero generar un link de invitación para una Comisión a la que estoy asignado
  Para que un Estudiante pueda registrarse a través de ese link y quedar asignado
  automáticamente a mi comisión (RF-01)

  Background:
    Given un Docente autenticado

  @generar-invitacion @happy-path
  Scenario: Docente asignado genera invitación
    Given el Docente está presente en docentes_asignados de la Comisión "IS-2026-C1"
    When ejecuta GenerarInvitacion(comision_id, docente_id)
    Then el sistema persiste una Invitación con token único
    And expira_en queda fijado a 7 días desde ahora
    And se envía un email con el link de invitación
    And se emite el evento InvitacionGenerada

  @generar-invitacion @error
  Scenario: Rechazo por Docente no asignado a la comisión
    Given el Docente NO está presente en docentes_asignados de la Comisión "IS-2026-C2"
    When intenta ejecutar GenerarInvitacion sobre esa comisión
    Then el sistema rechaza la operación con DocenteNoAsignadoAComision
    And ninguna Invitación se crea

  # Nota (`US-ADJ-57`): el Docente que llama es el mismo bajo prueba en este escenario, así que
  # la autorización (403, `ComisionNoAutorizada`) se resuelve antes que la validación de negocio
  # de arriba (422) — ambas comparten la misma causa. La validación 422 original sigue vigente
  # cuando el docente *destino* de la invitación es un tercero distinto de quien llama, ya
  # asignado a la comisión (ver `US-ADJ-26-generar-link-invitacion.feature`).
