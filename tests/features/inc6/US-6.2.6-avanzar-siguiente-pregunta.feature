@US-6.2.6
Feature: Docente avanza a la siguiente pregunta (US-6.2.6)
  Como Docente
  Quiero pasar a la siguiente pregunta cuando terminé de comentar la anterior
  Para controlar el ritmo de la clase, con una pausa deliberada entre pregunta y pregunta

  @backend @happy-path
  Scenario: Avance exitoso
    Given una sesión en la pregunta 1 de 5, ya cerrada
    When el Docente avanza
    Then pregunta_actual_indice pasa a 1 con las opciones ocultas y la pregunta sin cerrar
    And todos los conectados reciben el enunciado de la pregunta 2, sin opciones

  @backend @happy-path
  Scenario: Avance hasta la penúltima pregunta
    Given una sesión en la pregunta 4 de 5, ya cerrada
    When el Docente avanza
    Then queda en la pregunta 5

  @backend @error-case
  Scenario: Rechazo si la pregunta actual no fue cerrada
    Given una pregunta con las opciones mostradas y sin cerrar
    When el Docente intenta avanzar
    Then el sistema rechaza con PreguntaActualNoCerrada (422)

  @backend @error-case
  Scenario: Rechazo en la última pregunta
    Given una sesión en la última pregunta, ya cerrada
    When el Docente intenta avanzar
    Then el sistema rechaza con NoQuedanPreguntas (422)

  @backend @error-case
  Scenario: Rechazo si la sesión no está en curso
    Given una sesión EnEspera o Finalizada
    When el Docente intenta avanzar
    Then el sistema rechaza con SesionNoEnCurso (422)

  @backend @error-case
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta avanzar
    Then el sistema rechaza con SesionNoExiste (404)

  @backend @security
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta avanzar
    Then el sistema responde 403
