# language: es
@US-6.3.8
Feature: Estudiante ve sesiones, se une y espera (US-6.3.8)

  Scenario: Las sesiones aparecen junto a las actividades de la materia
    Given una sesión EnEspera de la Comisión del Estudiante
    When el Estudiante abre las actividades de su materia
    Then ve la tarjeta de la sesión con su Badge "En espera"

  Scenario: Solo sesiones de su materia
    Given una sesión de otra materia de la misma Comisión
    When el Estudiante abre las actividades de su materia
    Then no aparece

  Scenario: Sin sesiones
    Given ninguna sesión activa
    When el Estudiante abre la pantalla
    Then ve el estado vacío

  Scenario: El listado se refresca solo
    Given la pantalla abierta sin sesiones
    When el Docente crea una sesión
    Then aparece en menos de 10 segundos sin recargar

  Scenario: Unirse a una sesión en espera
    Given la tarjeta de una sesión EnEspera
    When el Estudiante la toca
    Then se une y ve "¡Te uniste!" con la cantidad de participantes

  Scenario: Unión tardía a una sesión en curso
    Given una sesión EnCurso
    When el Estudiante la toca
    Then se une y entra a la etapa de la pregunta actual

  Scenario: El conteo de la sala es en vivo
    Given el Estudiante en la sala de espera
    When otro Estudiante se une
    Then el conteo aumenta sin recargar

  Scenario: Pasa solo a la pregunta cuando el Docente inicia
    Given el Estudiante en la sala de espera
    When llega pregunta_presentada
    Then sale de la sala sin tocar nada

  Scenario: Sesión ya finalizada
    Given una tarjeta que quedó vieja y la sesión ya finalizó
    When el Estudiante la toca
    Then ve el mensaje y la lista se refresca

  Scenario: Recargar la sala
    Given el Estudiante en la sala de espera
    When recarga la pantalla
    Then vuelve a la sala sin perder su participación
