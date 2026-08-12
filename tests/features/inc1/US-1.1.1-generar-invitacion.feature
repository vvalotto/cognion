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
