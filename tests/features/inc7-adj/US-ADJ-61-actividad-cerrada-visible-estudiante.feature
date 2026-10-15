@US-ADJ-61
Feature: La actividad cerrada se ve como cerrada para el Estudiante (US-ADJ-61)
  Como Estudiante que no llegó a rendir una actividad que el Docente cerró (o que venció)
  Quiero ver que está cerrada y no "pendiente de responder"
  Para no pensar que todavía puedo hacerla

  @listado @cerrada @happy-path
  Scenario: Una actividad cerrada manualmente y sin rendir se lista como cerrada
    Given una actividad con cerrada_manualmente = true
    And un Estudiante de su comisión sin Evaluacion finalizada
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "cerrada"

  @listado @cerrada
  Scenario: Una actividad vencida por fecha y sin rendir se lista como cerrada
    Given una actividad con fecha_cierre en el pasado y cerrada_manualmente = false
    And un Estudiante de su comisión sin Evaluacion finalizada
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "cerrada"

  @listado @regresion
  Scenario: Una actividad vigente sigue pendiente
    Given una actividad con fecha_apertura en el pasado y fecha_cierre en el futuro
    And un Estudiante de su comisión sin Evaluacion finalizada
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "pendiente"

  @listado @regresion
  Scenario: Una actividad que todavía no abrió sigue igual
    Given una actividad con fecha_apertura en el futuro
    And un Estudiante de su comisión sin Evaluacion finalizada
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "todavia_no_abrio"

  @listado @prioridad
  Scenario: Quien ya rindió ve finalizada aunque la actividad esté cerrada
    Given una actividad cerrada y un Estudiante con una Evaluacion finalizada de ella
    When el Estudiante lista las actividades de la materia
    Then la actividad tiene estado "finalizada" y trae su evaluacion_id
