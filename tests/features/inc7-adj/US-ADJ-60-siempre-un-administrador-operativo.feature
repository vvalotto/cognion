@US-ADJ-60
Feature: Siempre existe al menos un Administrador operativo (US-ADJ-60)
  Como dueño del sistema
  Quiero que nunca pueda quedar sin ningún Administrador que pueda operarlo
  Para no depender de una intervención manual en la base de datos para recuperar el control

  @baja @invariante @happy-path
  Scenario: Dar de baja a un Administrador sin Comisiones es siempre baja lógica
    Given dos Administradores operativos A y B, y A no creó ninguna Comisión
    When un Administrador da de baja a A
    Then la respuesta es 200 con el detalle de A
    And A sigue existiendo en la tabla usuario con deshabilitada = true

  @baja @invariante
  Scenario: No se puede dar de baja al último Administrador operativo
    Given un único Administrador operativo A
    When se hace DELETE /usuarios/{A}
    Then la respuesta es 409 con codigo "ultimo_administrador_operativo"
    And A sigue con deshabilitada = false

  @baja @invariante
  Scenario: Un Administrador bloqueado no cuenta como operativo
    Given un Administrador A operativo y un Administrador B con bloqueada = true
    When se hace DELETE /usuarios/{A}
    Then la respuesta es 409 con codigo "ultimo_administrador_operativo"

  @baja
  Scenario: Dar de baja a un Administrador ya deshabilitado es idempotente
    Given un Administrador A deshabilitado y un Administrador B operativo
    When se hace DELETE /usuarios/{A}
    Then la respuesta es 200
    And B sigue operativo

  @bloqueo @invariante
  Scenario: Tres logins fallidos del último Administrador lo bloquean solo por un tiempo
    Given un único Administrador operativo A
    When se hacen 3 POST /identidad/login con una contraseña incorrecta
    Then A queda con bloqueada = true y bloqueada_hasta = ahora + 15 minutos
    And el siguiente login responde 403 con codigo "cuenta_bloqueada_temporal"
    And el detail trae reintentar_en_segundos mayor que 0

  @bloqueo
  Scenario: El bloqueo temporal se levanta solo al vencer
    Given A bloqueado temporalmente con bloqueada_hasta ya vencida
    When A hace login con su contraseña correcta
    Then la respuesta es 200 con un JWT válido
    And A queda con bloqueada = false y bloqueada_hasta = NULL

  @bloqueo @invariante
  Scenario: Habiendo otro Administrador operativo el bloqueo sigue siendo permanente
    Given dos Administradores operativos A y B
    When A falla 3 veces el login
    Then A queda con bloqueada = true y bloqueada_hasta = NULL
    And el detail del 403 es el texto plano de cuenta bloqueada

  @bloqueo @cambio-password
  Scenario: Tres fallos al cambiar la propia contraseña también son temporales para el último
    Given un único Administrador operativo A autenticado
    When A envía 3 veces PUT /usuarios/me/password con una contraseña actual incorrecta
    Then A queda con bloqueada = true y bloqueada_hasta = ahora + 15 minutos

  @bloqueo
  Scenario: Docente y Estudiante conservan el bloqueo permanente
    Given un Docente operativo
    When falla 3 veces el login
    Then queda con bloqueada = true y bloqueada_hasta = NULL

  @bloqueo @reseteo
  Scenario: Un reseteo de contraseña limpia el bloqueo temporal
    Given A bloqueado temporalmente
    When otro Administrador resetea su contraseña
    Then A queda con bloqueada = false y bloqueada_hasta = NULL

  @frontend
  Scenario: La confirmación de baja de un Administrador no promete un borrado
    Given estoy en la pantalla "Eliminar cuenta" de un Administrador
    Then el aviso dice que la cuenta se deshabilita y se puede reactivar
    And no dice que se borra en forma permanente
