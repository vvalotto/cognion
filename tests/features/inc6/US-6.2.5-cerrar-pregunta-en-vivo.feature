@US-6.2.5
Feature: Docente cierra la pregunta actual (US-6.2.5)
  Como Docente
  Quiero cerrar la pregunta cuando quiero y que aparezcan la respuesta correcta, cuántos eligieron cada opción y el ranking
  Para comentar el resultado en el aula antes de pasar a la siguiente

  @backend @happy-path
  Scenario: Cierre exitoso
    Given una pregunta con las opciones mostradas y varios Estudiantes que respondieron
    When el Docente cierra la pregunta
    Then pregunta_actual_cerrada pasa a verdadero y se persiste PreguntaEnVivoCerrada
    And todos los conectados reciben un único mensaje con la respuesta correcta, el histograma y el ranking
    And la respuesta HTTP es 200

  @backend @happy-path
  Scenario: El ranking del mensaje refleja los puntajes acumulados
    Given tres Estudiantes con distintos puntajes acumulados
    When el Docente cierra la pregunta
    Then el ranking viene ordenado por puntaje descendente con su posición

  @backend @happy-path
  Scenario: El histograma cuenta las respuestas por opción
    Given 5 respuestas a la opción "0" y 3 a la opción "2"
    When el Docente cierra la pregunta
    Then la distribución informa 5 para "0" y 3 para "2"

  @backend @edge-case
  Scenario: Cerrar sin ninguna respuesta
    Given una pregunta con las opciones mostradas y ninguna respuesta
    When el Docente la cierra
    Then se acepta, con distribución vacía y el ranking con todos en su puntaje actual

  @backend @error
  Scenario: Rechazo si las opciones no se mostraron
    Given una pregunta con solo el enunciado presentado
    When el Docente intenta cerrarla
    Then el sistema rechaza con OpcionesNoMostradasTodavia (422)

  @backend @error
  Scenario: Rechazo si ya estaba cerrada
    Given una pregunta ya cerrada
    When el Docente intenta cerrarla de nuevo
    Then el sistema rechaza con PreguntaYaCerrada (422) sin emitir otro evento

  @backend @error
  Scenario: Rechazo si la sesión no está en curso
    Given una sesión EnEspera
    When el Docente intenta cerrar la pregunta
    Then el sistema rechaza con SesionNoEnCurso (422)

  @backend @error
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta cerrar la pregunta
    Then el sistema rechaza con SesionNoExiste (404)

  @backend @error
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta cerrar la pregunta
    Then el sistema responde 403
