# language: es
@US-6.3.7
Feature: Docente proyecta histograma, ranking y resultado final (US-6.3.7)

  @happy-path
  Scenario: El histograma muestra la distribución y marca la correcta
    Given una pregunta cerrada con respuestas repartidas
    When se muestra el resultado
    Then hay una barra por opción con su cantidad y la correcta lleva borde blanco y ✓

  @edge-case
  Scenario: Opciones sin respuestas se muestran en cero
    Given una opción que nadie eligió
    When se muestra el histograma
    Then aparece con barra de 0

  @happy-path
  Scenario: Paso automático al ranking
    Given el histograma en pantalla
    When pasan 6 segundos
    Then la pantalla pasa al ranking

  @happy-path
  Scenario: Adelantar el ranking
    Given el histograma en pantalla
    When el Docente pulsa "Ver ranking ahora"
    Then pasa al ranking de inmediato

  @happy-path
  Scenario: Ranking Top 3 con nombres
    Given 6 participantes con puntajes distintos
    When se muestra el ranking
    Then aparecen solo los 3 primeros, con nombre y puntaje, en orden descendente

  @edge-case
  Scenario: Menos de 3 participantes
    Given 2 participantes
    When se muestra el ranking
    Then aparecen esos 2

  @edge-case
  Scenario: Nadie participó
    Given una pregunta que nadie respondió y sin participantes
    When se muestra el ranking
    Then dice "Nadie participó"

  @happy-path
  Scenario: Siguiente pregunta
    Given el ranking con preguntas restantes
    When el Docente pulsa "Siguiente pregunta"
    Then vuelve a la pregunta sola con la siguiente pregunta

  @edge-case
  Scenario: En la última pregunta no hay "Siguiente"
    Given el ranking de la última pregunta
    When se observa la pantalla
    Then solo está "Finalizar sesión"

  @happy-path
  Scenario: Finalizar antes de tiempo
    Given el ranking en la pregunta 2 de 5
    When el Docente pulsa "Finalizar sesión"
    Then se muestra el podio final

  @happy-path
  Scenario: Podio final
    Given la sesión finalizada
    When se muestra el resultado final
    Then se ve el podio Top 3 con nombres y "¡Gracias por participar!"

  @edge-case
  Scenario: Recargar tras el cierre
    Given una pregunta cerrada y el Docente que recarga la proyección
    When vuelve a cargar
    Then recupera el histograma o el ranking sin perder los datos

  @edge-case
  Scenario: Recargar con la sesión finalizada
    Given una sesión finalizada
    When el Docente abre la proyección
    Then ve el podio final
