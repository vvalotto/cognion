@US-ADJ-64
Feature: Logging local — emails de consola visibles y tokens enmascarados (US-ADJ-64)
  Como Docente que usa Cognión en su propia máquina, sin servidor de correo
  Quiero ver en el log del servidor los emails que el sistema "enviaría"
  Y que ese log no guarde completos los tokens de acceso de las personas
  Para recuperar una cuenta sin depender del correo y que nadie reutilice una sesión leyendo el log

  @consola @happy-path
  Scenario: Recuperar contraseña en modo consola
    Given un servidor real con EMAIL_MODO=consola y una cuenta registrada
    When se solicita la recuperación de contraseña de esa cuenta
    Then la salida del servidor contiene "Email (modo consola)", el destinatario y el link de recuperación

  @consola
  Scenario: Invitación por email en modo consola
    Given un servidor real con EMAIL_MODO=consola y una comisión con docente
    When el docente genera una invitación indicando un email destinatario
    Then la salida del servidor contiene el link de registro de esa invitación

  @consola
  Scenario: Aviso de apertura de actividad
    Given un servidor real con EMAIL_MODO=consola, una comisión con un estudiante y un docente
    When el docente crea una actividad para esa comisión
    Then la salida del servidor contiene el aviso de apertura dirigido al estudiante

  @tokens @invariante
  Scenario: El JWT no queda en el log del canal en vivo
    Given un servidor real y un usuario con un JWT válido
    When ese usuario abre una conexión WebSocket con su token
    Then la línea de acceso contiene "token=***"
    And el JWT no aparece en ninguna parte de la salida

  @tokens
  Scenario: La invitación no queda en el log de acceso
    Given un servidor real y una invitación generada
    When se pide la página de registro con el token de la invitación
    Then la línea de acceso contiene "token=***"
    And el token de la invitación no aparece en la salida

  @tokens @error
  Scenario: Un token inválido tampoco queda escrito
    Given un servidor real
    When se abre una conexión WebSocket con un token inválido
    Then la línea de rechazo no contiene el valor del token

  @regresion
  Scenario: Lo demás del log no cambia
    Given un servidor real
    When se pide el health check
    Then la línea de acceso mantiene el formato de uvicorn sin enmascarados

  @configuracion @error
  Scenario Outline: Nivel de log configurable
    Given la variable LOG_LEVEL con el valor <valor>
    When se carga la configuración
    Then el resultado es <resultado>

    Examples:
      | valor   | resultado                                           |
      | INFO    | nivel INFO para los loggers de la aplicación        |
      | WARNING | nivel WARNING para los loggers de la aplicación     |
      | ruidoso | un error que lista los valores válidos              |
