@US-3.4.2
Feature: Listado de materias y actividades del Docente (US-3.4.2)
  Como Docente
  Quiero ver mis materias y, dentro de cada una, el listado de actividades ya creadas
  Para ubicar rápidamente una actividad existente antes de crear una nueva o entrar a su
  detalle (RF-11)

  @happy-path
  Scenario: Ver materias
    Given un Docente autenticado con materias asignadas
    When entra a /actividad-evaluativa/materias
    Then ve una tarjeta por materia

  @happy-path
  Scenario: Ver actividades de una materia
    Given un Docente en /actividad-evaluativa/materias
    When elige una materia
    Then ve el listado de sus actividades con estado (En curso / Programada / Cerrada)

  @edge-case
  Scenario: Materia sin actividades
    Given una materia sin actividades creadas
    When el Docente entra a su listado
    Then ve la grilla vacía con la acción "+ Nueva actividad" disponible
