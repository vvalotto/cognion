@US-6.2.7
Feature: Docente finaliza la sesión en vivo (US-6.2.7)
  Como Docente
  Quiero dar por terminada la sesión y que todos vean el ranking final
  Para cerrar la dinámica con el resultado de la clase

  @backend @happy-path
  Scenario: Finalización exitosa tras cerrar la última pregunta
    Given una sesión en la última pregunta, ya cerrada
    When el Docente finaliza la sesión
    Then el estado pasa a Finalizada
    And todos los conectados reciben el ranking final ordenado por puntaje

  @backend @happy-path
  Scenario: Finalización anticipada con preguntas sin presentar
    Given una sesión en la pregunta 2 de 5, ya cerrada
    When el Docente finaliza la sesión
    Then se acepta y la sesión queda Finalizada

  @backend @error-case
  Scenario: Después de finalizar no se puede unir nadie
    Given una sesión Finalizada
    When un Estudiante intenta unirse
    Then el sistema rechaza con SesionYaFinalizada (422)

  @backend @error-case
  Scenario: Rechazo si la pregunta actual no fue cerrada
    Given una pregunta actual sin cerrar
    When el Docente intenta finalizar
    Then el sistema rechaza con PreguntaActualNoCerrada (422)

  @backend @error-case
  Scenario: Rechazo si la sesión nunca se inició
    Given una sesión EnEspera
    When el Docente intenta finalizar
    Then el sistema rechaza con SesionNoEnCurso (422)

  @backend @error-case
  Scenario: Rechazo si ya estaba finalizada
    Given una sesión Finalizada
    When el Docente intenta finalizar de nuevo
    Then el sistema rechaza con SesionYaFinalizada (422) sin emitir otro evento

  @backend @error-case
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta finalizar
    Then el sistema rechaza con SesionNoExiste (404)

  @backend @error-case
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta finalizar la sesión
    Then el sistema responde 403
