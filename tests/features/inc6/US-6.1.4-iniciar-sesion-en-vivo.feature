@US-6.1.4
Feature: Docente inicia la sesión en vivo (US-6.1.4)
  Como Docente
  Quiero iniciar la sesión en vivo cuando ya se unieron los estudiantes que quiero esperar
  Para arrancar la dinámica — todos los conectados ven al mismo tiempo el enunciado de la
  primera pregunta (RF-08)

  @backend @happy-path
  Scenario: Inicio exitoso
    Given una sesión en vivo en estado EnEspera con al menos un Estudiante unido
    When el Docente la inicia
    Then el estado pasa a EnCurso con pregunta_actual_indice=0
    And todos los conectados al canal reciben el enunciado de la primera pregunta, sin opciones

  @backend @happy-path
  Scenario: Inicio sin ningún Estudiante unido todavía
    Given una sesión en vivo en estado EnEspera sin ningún Estudiante unido
    When el Docente la inicia
    Then la operación se acepta igual — el dominio no exige un mínimo de participantes

  @backend @error
  Scenario: Rechazo por sesión ya iniciada
    Given una sesión en vivo ya en estado EnCurso
    When el Docente intenta iniciarla de nuevo
    Then el sistema rechaza la operación con SesionYaIniciada (422)

  @backend @error
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión en vivo
    When el Docente intenta iniciarla
    Then el sistema rechaza la operación con SesionNoExiste (404)

  @backend @error
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta iniciar una sesión en vivo
    Then el sistema responde 403
