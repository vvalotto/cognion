@US-2.1.10
Feature: Listado y filtro del banco de preguntas (US-2.1.10)
  Como Docente
  Quiero ver la tabla de preguntas de una materia y filtrarla por unidad, tema,
  dificultad e importancia
  Para encontrar rápidamente las preguntas que necesito (RF-06)

  @frontend @happy-path
  Scenario: Ver el banco sin filtros
    Given un Docente autenticado navega al banco de "Ingeniería de Software"
    When la pantalla carga
    Then ve todas las preguntas activas de esa materia en la tabla

  @frontend @happy-path
  Scenario: Filtrar por dificultad
    Given el Docente en la pantalla del banco
    When selecciona dificultad = "Alto"
    Then la tabla se actualiza mostrando solo preguntas activas con dificultad Alto

  @frontend @edge-case
  Scenario: Filtro sin resultados
    Given el Docente en la pantalla del banco
    When aplica una combinación de filtros sin preguntas que la cumplan
    Then la tabla queda vacía, sin mensaje de error
