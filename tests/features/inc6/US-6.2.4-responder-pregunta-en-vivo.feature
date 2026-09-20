@US-6.2.4
Feature: Estudiante responde una pregunta en vivo (US-6.2.4)
  Como Estudiante
  Quiero responder la pregunta tocando una opción y ver al instante si acerté y cuántos puntos llevo
  Para saber cómo voy sin esperar a que el Docente cierre la pregunta

  @backend @happy-path
  Scenario: Respuesta correcta a tiempo
    Given una pregunta con las opciones mostradas y un Estudiante unido
    When el Estudiante elige la opción correcta dentro del tiempo límite
    Then se registra la respuesta con tiempo_respuesta medido por el servidor
    And la respuesta HTTP trae es_correcta=true, el puntaje de esa pregunta y el puntaje acumulado
    And todos los conectados reciben el conteo actualizado de respuestas, sin desglose por opción

  @backend @happy-path
  Scenario: Respuesta incorrecta
    Given una pregunta con las opciones mostradas
    When el Estudiante elige una opción incorrecta
    Then se registra la respuesta con puntaje 0 y es_correcta=false

  @backend @happy-path
  Scenario: Las proyecciones se actualizan junto con el evento
    Given un Estudiante que responde una pregunta
    When se registra la respuesta
    Then su puntaje acumulado en el ranking y el histograma de esa opción reflejan la respuesta

  @backend @error
  Scenario: Un solo intento por pregunta
    Given un Estudiante que ya respondió la pregunta actual
    When intenta responderla de nuevo
    Then el sistema rechaza con RespuestaYaRegistrada (422) y no cambia su puntaje

  @backend @error
  Scenario: Rechazo por tiempo agotado
    Given una pregunta cuyas opciones se mostraron hace más del tiempo límite
    When el Estudiante intenta responder
    Then el sistema rechaza con TiempoAgotado (422)

  @backend @error
  Scenario: Rechazo antes de que se muestren las opciones
    Given una pregunta con solo el enunciado presentado
    When el Estudiante intenta responder
    Then el sistema rechaza con OpcionesNoMostradasTodavia (422)

  @backend @error
  Scenario: Rechazo si la pregunta ya fue cerrada
    Given una pregunta cerrada por el Docente
    When el Estudiante intenta responder
    Then el sistema rechaza con PreguntaYaCerrada (422)

  @backend @error
  Scenario: Rechazo si no es la pregunta actual
    Given una sesión en la pregunta 2
    When el Estudiante responde con el pregunta_id de la pregunta 1
    Then el sistema rechaza con PreguntaNoActual (422)

  @backend @error
  Scenario: Estudiante que no se unió
    Given un Estudiante que nunca se unió a la sesión
    When intenta responder
    Then el sistema rechaza con ParticipacionNoExiste (404)

  @backend @error
  Scenario: Doble envío simultáneo
    Given dos envíos simultáneos de la misma respuesta del mismo Estudiante
    When se procesan
    Then uno se registra y el otro recibe RespuestaYaRegistrada (422)

  @backend @error
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Docente
    When intenta responder
    Then el sistema responde 403
