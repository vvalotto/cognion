@US-ADJ-25
Feature: Administrador asigna un Docente a una Comisión (US-ADJ-25)
  Como Administrador
  Quiero asignar un Docente a una Comisión existente
  Para que ese Docente pueda generar el link de invitación de esa Comisión

  @happy-path
  Scenario: Consultar el detalle de una Comisión sin Docente asignado
    Given una comisión sin ningún docente asignado
    When un Administrador hace GET /comisiones/{comision_id}
    Then recibe 200 con docentes_asignados vacío

  @happy-path
  Scenario: Consultar el detalle de una Comisión con Docente asignado
    Given una comisión con un docente asignado
    When un Administrador hace GET /comisiones/{comision_id}
    Then recibe 200 con el id del docente asignado

  @happy-path
  Scenario: Administrador asigna un Docente a una Comisión
    Given una comisión sin ningún docente asignado
    And un usuario con perfil Docente
    When un Administrador hace POST /comisiones/{comision_id}/docentes con ese docente
    Then recibe 200 con el docente en docentes_asignados

  @edge-case
  Scenario: Asignar el mismo Docente dos veces es idempotente
    Given una comisión con un docente asignado
    When un Administrador hace POST /comisiones/{comision_id}/docentes con el mismo docente
    Then recibe 200 con el docente una sola vez en docentes_asignados

  @error-case
  Scenario: Detalle de una Comisión inexistente
    Given un id de comisión que no existe
    When un Administrador hace GET /comisiones/{id-inexistente}
    Then recibe 404

  @error-case
  Scenario: Asignar un usuario que no es Docente
    Given una comisión sin ningún docente asignado
    And un usuario con perfil Estudiante
    When un Administrador hace POST /comisiones/{comision_id}/docentes con ese usuario
    Then recibe 422

  @regression
  Scenario: Docente sigue teniendo acceso al detalle de una Comisión
    Given una comisión con un docente asignado
    When un Docente hace GET /comisiones/{comision_id}
    Then recibe 200

  @error-case
  Scenario: Estudiante no tiene acceso al detalle de una Comisión
    Given un Estudiante autenticado
    When hace GET /comisiones/{comision_id}
    Then recibe 403
