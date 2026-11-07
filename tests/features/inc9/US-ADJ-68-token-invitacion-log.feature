@US-ADJ-68
Feature: El log de acceso no muestra el token de las invitaciones (US-ADJ-68)
  Como responsable de operar Cognión
  Quiero que el registro de accesos no guarde el código secreto de las invitaciones
  Para que nadie que lea el log pueda usar una invitación que todavía no se usó

  @token-en-ruta @happy-path
  Scenario: La consulta de una invitación vigente no deja el token en el log
    Given una invitación vigente de una comisión
    When el estudiante consulta la invitación por su enlace
    Then el log de acceso muestra la ruta de invitaciones con el token enmascarado
    And el token completo no aparece en la salida del servidor

  @token-en-ruta @error
  Scenario: Una invitación ya usada, vencida o inexistente tampoco deja el token
    Given un token de invitación que no corresponde a ninguna invitación vigente
    When se consulta la invitación por su enlace
    Then el log de acceso muestra la ruta de invitaciones con el token enmascarado
    And el token completo no aparece en la salida del servidor

  @token-en-ruta
  Scenario: La línea conserva el método y el estado
    Given una invitación vigente de una comisión
    When el estudiante consulta la invitación por su enlace
    Then la línea del log conserva el método GET y el código de estado de la respuesta

  @sin-regresion
  Scenario: Generar una invitación se registra como siempre
    Given una comisión de un Docente
    When el Docente genera una invitación para la comisión
    Then el log de acceso muestra la ruta de la comisión con su identificador y "invitaciones" sin enmascarar

  @sin-regresion
  Scenario: Las otras formas de token siguen enmascaradas
    Given una invitación vigente de una comisión
    When se abre el enlace de registro con el token en la consulta
    Then el log de acceso muestra "token=***" y el token completo no aparece

  @borde
  Scenario: Un segmento corto no se toca
    Given un texto de log con un segmento de menos de 20 caracteres después de "/invitaciones/"
    When el filtro de logging lo procesa
    Then el texto queda igual
