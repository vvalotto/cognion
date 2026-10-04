@US-ADJ-62
Feature: Recuperar la contraseña desbloquea la cuenta (US-ADJ-62)
  Como usuario que se bloqueó por equivocarse con la contraseña
  Quiero que recuperarla con el link que me llega por email también me desbloquee
  Para volver a entrar sin depender de que un Administrador me destrabe

  @recuperacion-password @desbloqueo @happy-path
  Scenario: Recuperar la contraseña desbloquea una cuenta bloqueada por intentos fallidos
    Given un Usuario con bloqueada = true e intentos_fallidos_login = 3
    And un TokenRecuperacionPassword vigente de ese Usuario
    When se confirma una contraseña nueva válida con ese token
    Then Usuario.password_hash queda actualizado
    And Usuario.bloqueada es false
    And intentos_fallidos_login e intentos_fallidos_password son 0
    And se emite CuentaDesbloqueada

  @recuperacion-password @desbloqueo
  Scenario: Tras recuperar, el usuario puede iniciar sesión con la contraseña nueva
    Given un Usuario bloqueado que recuperó su contraseña
    When se hace POST /identidad/login con su email y la contraseña nueva
    Then la respuesta es 200 con un JWT válido

  @recuperacion-password @desbloqueo @administrador
  Scenario: Recuperar la contraseña libera al último Administrador bloqueado temporalmente
    Given el único Administrador con bloqueada = true y bloqueada_hasta en el futuro
    And un TokenRecuperacionPassword vigente de ese Administrador
    When se confirma una contraseña nueva válida con ese token
    Then queda con bloqueada = false y bloqueada_hasta = NULL

  @recuperacion-password @desbloqueo
  Scenario: Una cuenta no bloqueada no emite desbloqueo
    Given un Usuario con bloqueada = false
    And un TokenRecuperacionPassword vigente de ese Usuario
    When se confirma una contraseña nueva válida con ese token
    Then Usuario.password_hash queda actualizado
    And no se emite CuentaDesbloqueada

  @recuperacion-password @seguridad
  Scenario: Recuperar la contraseña no reactiva una cuenta deshabilitada
    Given un Usuario con deshabilitada = true
    And un TokenRecuperacionPassword vigente de ese Usuario
    When se confirma una contraseña nueva válida con ese token
    Then Usuario.deshabilitada sigue en true
    And el login responde 403 con codigo "cuenta_deshabilitada"

  @recuperacion-password @error @seguridad
  Scenario: Un token vencido no desbloquea nada
    Given un Usuario bloqueado con un TokenRecuperacionPassword vencido
    When se confirma una contraseña nueva válida con ese token
    Then la respuesta es un error TokenRecuperacionVencido
    And Usuario.bloqueada sigue en true

  @recuperacion-password @error @invariante
  Scenario: Una contraseña que no cumple la política no desbloquea
    Given un Usuario bloqueado con un TokenRecuperacionPassword vigente
    When se confirma una contraseña de menos de 12 caracteres
    Then la respuesta es un error PasswordDemasiadoCorta
    And Usuario.bloqueada sigue en true
    And el token sigue sin usar
