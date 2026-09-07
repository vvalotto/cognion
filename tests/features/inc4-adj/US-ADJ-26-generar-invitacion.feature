@US-ADJ-26
Feature: Docente genera el link de invitación de una Comisión (US-ADJ-26)
  Como Docente
  Quiero generar el link de invitación de una Comisión donde estoy asignado
  Para que pueda compartirlo manualmente con mis Estudiantes y se registren

  @happy-path
  Scenario: Docente asignado genera el link de invitación con éxito
    Given una comisión con un docente asignado
    When ese Docente hace POST /comisiones/{comision_id}/invitaciones sin email_destinatario
    Then recibe 201 con un token no vacío

  @happy-path
  Scenario: Generar un link nuevo produce una invitación distinta
    Given una comisión con un docente asignado
    And ese Docente ya generó una invitación para esa comisión
    When vuelve a hacer POST /comisiones/{comision_id}/invitaciones sin email_destinatario
    Then recibe 201 con un token distinto del anterior

  @regression
  Scenario: Generar la invitación con email_destinatario sigue funcionando
    Given una comisión con un docente asignado
    When ese Docente hace POST /comisiones/{comision_id}/invitaciones con email_destinatario
    Then recibe 201 con un token no vacío
    And se envía el email de invitación

  @error-case
  Scenario: Docente no asignado no puede generar la invitación
    Given una comisión sin el docente autenticado entre sus docentes_asignados
    When ese Docente hace POST /comisiones/{comision_id}/invitaciones
    Then recibe 422

  @error-case
  Scenario: Generar invitación de una Comisión inexistente
    Given un id de comisión que no existe
    When un Docente hace POST /comisiones/{id-inexistente}/invitaciones
    Then recibe 404

  @error-case
  Scenario: Administrador no puede generar invitaciones
    Given un Administrador autenticado
    When hace POST /comisiones/{comision_id}/invitaciones
    Then recibe 403
