@US-1.1.3
Feature: Rechazo de registro con invitación no válida (US-1.1.3)
  Como Estudiante que intenta usar un link de invitación que ya no es válido
  Quiero recibir un rechazo explícito y comprensible
  Para entender que debo pedirle al docente un nuevo link,
  sin esperar una recuperación automática (ADR-012)

  @registro-estudiante @error
  Scenario: Token inexistente
    Given un token que no corresponde a ninguna Invitación
    When el Estudiante ejecuta RegistrarEstudiante(token, datos_usuario)
    Then el sistema rechaza la operación con InvitacionInvalida
    And ningún Usuario se crea
    And no se persiste ningún evento de dominio

  @registro-estudiante @error
  Scenario: Invitación vencida
    Given una Invitación cuyo expira_en ya pasó
    When el Estudiante ejecuta RegistrarEstudiante con ese token
    Then el sistema rechaza la operación con InvitacionVencida
    And ningún Usuario se crea
    And no se persiste ningún evento de dominio

  @registro-estudiante @error
  Scenario: Invitación ya usada
    Given una Invitación con usada_en distinto de null
    When el Estudiante ejecuta RegistrarEstudiante con ese token
    Then el sistema rechaza la operación con InvitacionYaUsada
    And ningún Usuario se crea
    And no se persiste ningún evento de dominio

  @registro-estudiante @error @ux
  Scenario Outline: La UI no distingue el motivo del rechazo
    Given el backend rechazó el registro con <excepcion>
    When se muestra el mensaje al Estudiante
    Then el mensaje es "Este link ya no es válido" en los tres casos
    And no se muestra el formulario de registro

    Examples:
      | excepcion           |
      | InvitacionInvalida  |
      | InvitacionVencida   |
      | InvitacionYaUsada   |
