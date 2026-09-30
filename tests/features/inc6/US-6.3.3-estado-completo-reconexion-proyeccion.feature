@US-6.3.3
Feature: Estado completo de la sesión para reconectar la proyección (US-6.3.3)
  Como Docente
  Quiero que si recargo la pantalla de proyección vuelva exactamente al punto de la clase
  Para no perder el histograma, el ranking ni el conteo de respuestas frente al aula

  @backend @happy-path
  Scenario: El conteo de respuestas y el total de participantes
    Given una sesión con 5 participantes y 3 respuestas a la pregunta actual
    When el Docente consulta el estado
    Then total_participantes es 5 y cantidad_respuestas es 3

  @backend @happy-path
  Scenario: Sin pregunta actual el conteo es cero
    Given una sesión EnEspera
    When se consulta el estado
    Then cantidad_respuestas es 0 y resultado_pregunta es nulo

  @backend @happy-path
  Scenario: Con la pregunta cerrada el Docente recupera histograma y ranking
    Given una pregunta cerrada con respuestas registradas
    When el Docente consulta el estado
    Then resultado_pregunta trae la distribución y el ranking con nombres

  @backend @happy-path
  Scenario: Con la pregunta abierta no hay resultado todavía
    Given una pregunta con las opciones mostradas y sin cerrar
    When el Docente consulta el estado
    Then resultado_pregunta es nulo

  @backend @error-case
  Scenario: El Estudiante nunca recibe el ranking
    Given una pregunta cerrada
    When un Estudiante consulta el estado
    Then resultado_pregunta es nulo

  @backend @happy-path
  Scenario: El estado anterior sigue funcionando
    Given un cliente que consume solo los campos de US-6.2.8
    When consulta el estado
    Then recibe los mismos campos de siempre
