@US-2.2.9
Feature: Login refleja el estado de cuenta bloqueada (US-2.2.9)
  Como Usuario que intenta iniciar sesión con una cuenta bloqueada
  Quiero ver un mensaje explícito de bloqueo
  Para no confundirlo con un error de contraseña incorrecta

  @frontend @error
  Scenario: Intento de login sobre cuenta bloqueada
    Given un Usuario con su cuenta bloqueada
    When intenta iniciar sesión con cualquier contraseña
    Then el sistema muestra la alerta de "Cuenta bloqueada"
    And deshabilita el formulario de login
    And indica que debe contactar a un Administrador

  @frontend @regression
  Scenario: Login con credenciales inválidas en cuenta no bloqueada
    Given un Usuario con su cuenta activa
    When intenta iniciar sesión con una contraseña incorrecta
    Then el sistema muestra el mensaje genérico de credenciales inválidas
    And no menciona bloqueo de cuenta
