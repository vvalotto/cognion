# language: es
@US-6.3.6
Feature: Docente proyecta la pregunta y controla las opciones (US-6.3.6)

  @happy-path
  Scenario: Pregunta sola
    Given una sesión recién iniciada
    When el Docente abre la proyección
    Then ve el enunciado grande, "Pregunta 1 de N" y el botón "Mostrar opciones", sin opciones

  @happy-path
  Scenario: Mostrar las opciones arranca el temporizador
    Given la pregunta sola en pantalla
    When el Docente pulsa "Mostrar opciones"
    Then aparecen las opciones como cajas de color y el temporizador cuenta desde el tiempo límite

  @happy-path
  Scenario: Las opciones no revelan la correcta
    Given la pregunta con opciones
    When se observa la pantalla
    Then ninguna opción está marcada como correcta

  @happy-path
  Scenario: Verdadero/Falso
    Given una pregunta de Verdadero/Falso con las opciones mostradas
    When se observa la pantalla
    Then hay dos cajas, "Verdadero" y "Falso"

  @happy-path
  Scenario: El conteo se actualiza en vivo
    Given la pregunta con opciones y 5 participantes
    When llegan 3 respuestas
    Then el conteo muestra "3 / 5 ya respondieron"

  @edge-case
  Scenario: El temporizador en 0 no cierra la pregunta
    Given la pregunta con el temporizador en cero
    When pasan segundos más
    Then la pregunta sigue abierta hasta que el Docente pulsa "Cerrar pregunta"

  @happy-path
  Scenario: Cerrar la pregunta
    Given la pregunta con opciones
    When el Docente pulsa "Cerrar pregunta"
    Then se envía el comando y la pantalla pasa a la etapa de resultado

  @edge-case
  Scenario: Recargar en medio de la pregunta
    Given la pregunta con opciones abierta hace 10 segundos
    When el Docente recarga la proyección
    Then vuelve a la misma etapa con el temporizador descontando esos 10 segundos y el conteo actual

  @edge-case
  Scenario: Doble click en "Mostrar opciones"
    Given la pregunta sola
    When el Docente hace doble click
    Then se envía una sola request

  @edge-case
  Scenario: Reconexión
    Given la proyección con el canal caído
    When se reconecta
    Then la etapa y el conteo se recalculan desde el estado del servidor
