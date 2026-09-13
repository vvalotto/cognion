@US-ADJ-39
Feature: Confirmar nueva contraseña con token de recuperación (US-ADJ-39)
  Como quien recibió un email de recuperación de contraseña
  Quiero definir una contraseña nueva usando el link recibido
  Para recuperar el acceso a mi cuenta sin necesitar la contraseña anterior

  @recuperacion-password @happy-path
  Scenario: Confirmar con un token vigente y contraseña válida
    Given un TokenRecuperacionPassword vigente y sin usar
    And una password_nueva que cumple INV-ID-11 ampliada
    When se hace POST /identidad/recuperar-password/confirmar con ese token y esa password
    Then la respuesta es 200 OK
    And Usuario.password_hash queda actualizado
    And el token queda marcado como usado

  @recuperacion-password @error
  Scenario: Confirmar con un token ya usado
    Given un TokenRecuperacionPassword ya usado
    When se hace POST /identidad/recuperar-password/confirmar con ese token
    Then la respuesta es un error TokenRecuperacionYaUsado
    And Usuario.password_hash no cambia

  @recuperacion-password @error @invariante
  Scenario: Confirmar con un token vencido
    Given un TokenRecuperacionPassword cuya expira_en ya pasó
    When se hace POST /identidad/recuperar-password/confirmar con ese token
    Then la respuesta es un error TokenRecuperacionVencido

  @recuperacion-password @error
  Scenario: Confirmar con un token inexistente
    Given ningún TokenRecuperacionPassword tiene el token dado
    When se hace POST /identidad/recuperar-password/confirmar con ese token
    Then la respuesta es un error TokenRecuperacionInvalido

  @recuperacion-password @error @invariante
  Scenario: Confirmar con una contraseña que no cumple la política
    Given un TokenRecuperacionPassword vigente y sin usar
    And una password_nueva de menos de 12 caracteres
    When se hace POST /identidad/recuperar-password/confirmar con ese token y esa password
    Then la respuesta es un error PasswordDemasiadoCorta
    And el token sigue sin usar

  @recuperacion-password @seguridad
  Scenario: Confirmar no desbloquea una cuenta bloqueada
    Given un Usuario bloqueado con un TokenRecuperacionPassword vigente
    When se confirma una contraseña nueva válida con ese token
    Then Usuario.password_hash queda actualizado
    And Usuario.bloqueada sigue en true
