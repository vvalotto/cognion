@US-ADJ-38
Feature: Solicitar recuperación de contraseña (US-ADJ-38)
  Como cualquier persona con una cuenta en el sistema que olvidó su contraseña
  Quiero pedir un link de recuperación ingresando mi email
  Para poder definir una contraseña nueva sin depender del Administrador

  @recuperacion-password @happy-path
  Scenario: Solicitar recuperación con un email de cuenta existente
    Given un Usuario con email "docente@fiuner.edu.ar" registrado
    When se solicita POST /identidad/recuperar-password/solicitar con ese email
    Then la respuesta es 202 Accepted con el mensaje genérico
    And se crea un TokenRecuperacionPassword para ese Usuario, vigente 1 hora

  @recuperacion-password @seguridad
  Scenario: Solicitar recuperación con un email que no existe
    Given ningún Usuario tiene el email "inexistente@fiuner.edu.ar"
    When se solicita POST /identidad/recuperar-password/solicitar con ese email
    Then la respuesta es 202 Accepted con el mismo mensaje genérico que el caso exitoso
    And no se crea ningún TokenRecuperacionPassword

  @recuperacion-password @invariante
  Scenario: Solicitar dos veces invalida el token anterior
    Given un Usuario ya tiene un TokenRecuperacionPassword activo sin usar
    When se solicita una nueva recuperación para el mismo email
    Then el token anterior queda invalidado
    And se crea un token nuevo, distinto del anterior

  @recuperacion-password @resiliencia
  Scenario: Un fallo de envío de email no bloquea la respuesta
    Given el canal de envío de Notificaciones falla al intentar enviar
    When se solicita una recuperación con un email de cuenta existente
    Then la respuesta sigue siendo 202 Accepted
    And el TokenRecuperacionPassword queda creado igual
