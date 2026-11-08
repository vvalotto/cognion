@US-ADJ-69
Feature: El login avisa "te queda 1 intento" tras el 2.º fallo (US-ADJ-69)
  Como persona que usa una contraseña equivocada al entrar
  Quiero que el segundo error me avise de que me queda un solo intento
  Para no bloquear mi cuenta sin darme cuenta y poder recuperar la contraseña a tiempo

  @aviso @happy-path
  Scenario: El primer fallo no avisa
    Given una cuenta existente sin intentos fallidos
    When se intenta iniciar sesión con una contraseña incorrecta
    Then la respuesta es 401
    And la respuesta no informa intentos restantes

  @aviso @happy-path
  Scenario: El segundo fallo avisa que queda 1 intento
    Given una cuenta existente con 1 intento fallido
    When se intenta iniciar sesión con una contraseña incorrecta
    Then la respuesta es 401
    And la respuesta informa que queda 1 intento

  @aviso @error
  Scenario: El tercer fallo bloquea la cuenta y el siguiente intento responde 403
    Given una cuenta existente con 2 intentos fallidos
    When se intenta iniciar sesión con una contraseña incorrecta
    Then la respuesta es 401
    And la respuesta no informa intentos restantes
    And el siguiente intento de iniciar sesión responde 403

  @aviso @seguridad
  Scenario: Un email inexistente nunca recibe el aviso
    Given un email que no corresponde a ninguna cuenta
    When se intenta iniciar sesión 3 veces con ese email
    Then todas las respuestas son 401 sin intentos restantes

  @aviso @contador
  Scenario: Un login correcto reinicia el contador
    Given una cuenta existente con 1 intento fallido
    When se inicia sesión con la contraseña correcta
    And se intenta iniciar sesión con una contraseña incorrecta
    Then la respuesta es 401
    And la respuesta no informa intentos restantes

  @aviso @ultimo-administrador
  Scenario: El último Administrador también recibe el aviso
    Given el único Administrador operativo con 1 intento fallido
    When se intenta iniciar sesión con una contraseña incorrecta
    Then la respuesta es 401
    And la respuesta informa que queda 1 intento
