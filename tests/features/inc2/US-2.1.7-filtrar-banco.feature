@US-2.1.7
Feature: Filtrado del banco de preguntas (US-2.1.7)
  Como Docente
  Quiero filtrar el banco de una materia por cualquier combinación de unidad temática, tema,
  dificultad e importancia
  Para encontrar rápidamente las preguntas que necesito al armar una sesión

  Background:
    Given un Docente autenticado

  @filtrar-banco @happy-path
  Scenario: Filtro combinado por dificultad e importancia
    Given un Banco con preguntas de distinta dificultad e importancia
    When ejecuta FiltrarBanco con dificultad "Alto" e importancia "Alto"
    Then el sistema devuelve solo las preguntas activas que matchean ambos filtros

  @filtrar-banco @happy-path
  Scenario: Sin filtros adicionales
    Given un Banco con 5 preguntas activas y 1 inactiva
    When ejecuta FiltrarBanco sin más filtros que la materia
    Then el sistema devuelve las 5 preguntas activas
    And no incluye la pregunta inactiva

  @filtrar-banco @sin-resultados
  Scenario: Ningún resultado
    Given un Banco sin preguntas de dificultad "Bajo"
    When ejecuta FiltrarBanco con dificultad "Bajo"
    Then el sistema devuelve una lista vacía
