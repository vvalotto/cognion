@US-ADJ-59
Feature: Una cuenta deshabilitada no puede iniciar sesión (US-ADJ-59)
  Como Administrador
  Quiero que dar de baja una cuenta impida que esa persona vuelva a entrar al sistema
  Para que la baja sea real y no solo un cambio de color en el listado

  @login @deshabilitada @happy-path @invariante
  Scenario: Login con contraseña correcta sobre una cuenta deshabilitada
    Given un Usuario Docente con deshabilitada = true
    When se hace POST /identidad/login con su email y su contraseña correcta
    Then la respuesta es 403
    And el detail tiene codigo "cuenta_deshabilitada"
    And no se emite ningún JWT

  @login @deshabilitada @invariante
  Scenario: El rechazo no depende de la contraseña ni consume intentos
    Given un Usuario con deshabilitada = true e intentos_fallidos_login = 0
    When se hace POST /identidad/login con una contraseña incorrecta
    Then la respuesta es 403 con codigo "cuenta_deshabilitada"
    And intentos_fallidos_login sigue en 0
    And bloqueada sigue en false

  @login @deshabilitada
  Scenario: Reactivar la cuenta restituye el acceso
    Given un Usuario que estuvo deshabilitado y fue reactivado con activar()
    When se hace POST /identidad/login con su email y su contraseña correcta
    Then la respuesta es 200 con un JWT válido

  @login @deshabilitada @bloqueada
  Scenario: Deshabilitada y bloqueada a la vez
    Given un Usuario con deshabilitada = true y bloqueada = true
    When se hace POST /identidad/login con su email
    Then la respuesta es 403 con codigo "cuenta_deshabilitada"

  @login @regresion
  Scenario: Una cuenta activa no cambia de comportamiento
    Given un Usuario con deshabilitada = false y bloqueada = false
    When se hace POST /identidad/login con su email y su contraseña correcta
    Then la respuesta es 200 con un JWT válido

  @login @regresion @bloqueada
  Scenario: Una cuenta bloqueada conserva su respuesta actual
    Given un Usuario con bloqueada = true y deshabilitada = false
    When se hace POST /identidad/login
    Then la respuesta es 403 con el detail en texto plano de cuenta bloqueada

  @frontend @login @deshabilitada
  Scenario: El login muestra la alerta de cuenta deshabilitada
    Given estoy en /login
    When ingreso las credenciales de una cuenta deshabilitada
    Then veo la alerta "Cuenta deshabilitada"
    And el formulario queda deshabilitado
    And no veo la alerta de "Cuenta bloqueada"
