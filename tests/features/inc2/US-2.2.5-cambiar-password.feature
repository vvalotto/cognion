@US-2.2.5
Feature: Cambio de contraseña propio (US-2.2.5)
  Como Usuario autenticado (Administrador, Docente o Estudiante)
  Quiero cambiar mi propia contraseña ingresando la actual y la nueva
  Para no depender del Administrador cuando simplemente quiero actualizarla (RF-19)

  @cambiar-password @happy-path
  Scenario: Cambio exitoso
    Given un Usuario autenticado con su contraseña actual correcta
    When ejecuta CambiarPassword(usuario_id, password_actual, "nuevaClave123")
    Then el sistema actualiza password_hash
    And intentos_fallidos_password vuelve a 0
    And se emite PasswordCambiada
    And el JWT en curso sigue siendo válido

  @cambiar-password @error
  Scenario: Contraseña actual incorrecta, sin llegar al límite
    Given un Usuario con intentos_fallidos_password = 1
    When ejecuta CambiarPassword con la contraseña actual incorrecta
    Then intentos_fallidos_password pasa a 2
    And el sistema rechaza con PasswordActualIncorrecta

  @cambiar-password @error
  Scenario: Tercer fallo consecutivo bloquea la cuenta
    Given un Usuario con intentos_fallidos_password = 2
    When ejecuta CambiarPassword con la contraseña actual incorrecta
    Then intentos_fallidos_password pasa a 3
    And bloqueada pasa a true
    And se emite CuentaBloqueada

  @cambiar-password @error
  Scenario: Rechazo por contraseña nueva demasiado corta
    Given un Usuario autenticado con su contraseña actual correcta
    When ejecuta CambiarPassword con password_nueva de 5 caracteres
    Then el sistema rechaza con PasswordDemasiadoCorta

  @cambiar-password @error
  Scenario: Cuenta ya bloqueada
    Given un Usuario con bloqueada = true
    When ejecuta CambiarPassword con cualquier dato
    Then el sistema rechaza con CuentaBloqueadaError sin verificar password_actual
