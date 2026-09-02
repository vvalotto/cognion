@US-3.4.5
Feature: Materias y actividades del Estudiante (US-3.4.5)
  Como Estudiante
  Quiero ver mis materias y, dentro de cada una, las actividades disponibles con su estado
  Para saber qué tengo pendiente de rendir, sin confundir actividades que todavía no abrieron
  o que ya cerré (RF-11, RF-12)

  @happy-path
  Scenario: Ver materias de mi comisión
    Given un Estudiante autenticado con comisión asignada
    When entra a /mis-actividades/materias
    Then ve una tarjeta por materia de su comisión

  @happy-path
  Scenario: Actividad pendiente de responder
    Given una actividad dentro de su período vigente, sin Evaluacion Finalizada del Estudiante
    When entra al listado de actividades de esa materia
    Then la ve con Badge "Pendiente de responder"

  @edge-case
  Scenario: Actividad que todavía no abrió
    Given una actividad con fecha_apertura futura
    When el Estudiante entra al listado
    Then la ve con Badge "Todavía no abrió"

  @happy-path
  Scenario: Actividad ya finalizada por el Estudiante
    Given una actividad donde el Estudiante ya tiene una Evaluacion Finalizada
    When entra al listado
    Then la ve con Badge "Finalizada — ver revisión"

  @edge-case
  Scenario: Materia sin actividades visibles
    Given una materia de su comisión sin actividades creadas
    When el Estudiante entra a su listado
    Then ve la grilla vacía sin actividades pendientes
