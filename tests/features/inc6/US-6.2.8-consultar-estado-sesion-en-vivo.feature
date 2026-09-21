@US-6.2.8
Feature: Consultar el estado de la sesión en vivo (US-6.2.8)
  Como Docente o Estudiante
  Quiero volver a ver el estado de la sesión si se me cae la conexión o entro tarde
  Para retomar exactamente donde estaba la clase, sin perder mi lugar

  @backend @happy-path
  Scenario: Estado de una sesión en espera
    Given una sesión EnEspera
    When un Docente consulta el estado
    Then recibe estado EnEspera sin pregunta actual

  @backend @happy-path
  Scenario: Estado con el enunciado presentado y las opciones ocultas
    Given una sesión EnCurso con solo el enunciado presentado
    When un Estudiante consulta el estado
    Then recibe el enunciado sin opciones y sin respuesta correcta

  @backend @happy-path
  Scenario: Estado con las opciones mostradas
    Given una pregunta con las opciones mostradas
    When un Estudiante consulta el estado
    Then recibe las opciones, el instante en que se mostraron y el tiempo límite
    And no recibe la respuesta correcta

  @backend @happy-path
  Scenario: Estado con la pregunta cerrada
    Given una pregunta cerrada
    When un Estudiante consulta el estado
    Then recibe también la respuesta correcta

  @backend @happy-path
  Scenario: El Estudiante ve su propio avance
    Given un Estudiante que ya respondió la pregunta actual con 1200 puntos acumulados
    When consulta el estado
    Then ya_respondio es verdadero y puntaje_acumulado es 1200

  @backend @happy-path
  Scenario: Listado de participantes para la sala de espera
    Given tres Estudiantes unidos
    When el Docente lista los participantes
    Then recibe los tres en orden de unión

  @backend @happy-path
  Scenario: El Docente ve el ranking en cualquier momento
    Given una sesión EnCurso con puntajes acumulados
    When el Docente consulta el ranking
    Then recibe el ranking ordenado con posición

  @backend @error-case
  Scenario: El Estudiante ve el ranking solo al finalizar
    Given una sesión EnCurso
    When un Estudiante consulta el ranking
    Then el sistema responde 403
    But con la sesión Finalizada recibe el ranking completo

  @backend @error-case
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When se consulta el estado
    Then el sistema responde 404

  @backend @error-case
  Scenario: Rechazo por rol en los participantes
    Given un usuario autenticado con rol Estudiante
    When intenta listar los participantes
    Then el sistema responde 403
