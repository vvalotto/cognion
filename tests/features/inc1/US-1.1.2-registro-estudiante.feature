@US-1.1.2
Feature: Registro de Estudiante vía invitación válida (US-1.1.2)
  Como Estudiante que recibí un link de invitación
  Quiero completar mi registro con ese link
  Para quedar asignado automáticamente a la comisión del docente que me invitó,
  sin aprobación adicional (RF-01)

  @registro-estudiante @happy-path
  Scenario: Registro exitoso con invitación vigente
    Given una Invitación vigente (no vencida, no usada) para la Comisión "IS-2026-C1"
    When el Estudiante ejecuta RegistrarEstudiante(token, nombre, email, password)
    Then el sistema crea un Usuario con perfil Estudiante en la misma transacción
    And Estudiante.comision_id queda asignado a "IS-2026-C1"
    And la Invitación queda marcada como usada
    And se emiten los eventos InvitacionAceptada y UsuarioRegistrado
    And el Estudiante NO queda autenticado automáticamente

  @registro-estudiante @error
  Scenario: Rechazo por email ya registrado
    Given una Invitación vigente
    And un Usuario ya existe con el email que se intenta registrar
    When el Estudiante ejecuta RegistrarEstudiante con ese email
    Then el sistema rechaza la operación con EmailYaRegistrado
    And la Invitación no se marca como usada
