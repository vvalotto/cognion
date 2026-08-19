@US-2.2.1
Feature: Bloqueo automático de cuenta por 3 intentos fallidos consecutivos de login (US-2.2.1)
  Como sistema
  Quiero bloquear automáticamente una cuenta tras 3 intentos fallidos consecutivos de login
  Para frenar intentos de fuerza bruta sobre las credenciales, sin intervención manual (RF-19)

  @bloqueo-cuenta @happy-path
  Scenario: Fallo que no llega al límite
    Given un Usuario con intentos_fallidos_login = 1
    When falla un intento de IniciarSesion
    Then intentos_fallidos_login pasa a 2
    And el sistema rechaza con CredencialesInvalidas
    And bloqueada sigue en false

  @bloqueo-cuenta @error
  Scenario: Tercer fallo consecutivo bloquea la cuenta
    Given un Usuario con intentos_fallidos_login = 2
    When falla un intento de IniciarSesion
    Then intentos_fallidos_login pasa a 3
    And bloqueada pasa a true
    And se emite el evento CuentaBloqueada
    And el sistema rechaza con CredencialesInvalidas

  @bloqueo-cuenta @happy-path
  Scenario: Acierto resetea el contador
    Given un Usuario con intentos_fallidos_login = 2
    When IniciarSesion se ejecuta con credenciales correctas
    Then intentos_fallidos_login vuelve a 0

  @bloqueo-cuenta @error
  Scenario: Intento sobre cuenta ya bloqueada
    Given un Usuario con bloqueada = true
    When se ejecuta IniciarSesion con cualquier contraseña
    Then el sistema rechaza con CuentaBloqueadaError sin verificar la contraseña
    And intentos_fallidos_login no cambia
