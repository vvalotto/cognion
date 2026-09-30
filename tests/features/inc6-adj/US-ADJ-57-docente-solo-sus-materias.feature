Feature: Cada Docente opera solo sobre sus materias (US-ADJ-57)

  Como Docente quiero ver y operar solo sobre las materias en las que tengo al menos una
  Comisión asignada, y dentro de ellas solo sobre mis Comisiones, para no ver ni modificar
  el trabajo ni los datos de estudiantes de otros Docentes. El Administrador no pierde
  ninguna capacidad.

  Background:
    Given el Docente A asignado a una Comisión de "Ingeniería de Software"
    And el Docente B asignado a una Comisión de "Gestión de Proyectos"

  Scenario: Solo ve sus materias
    When el Docente A abre el listado de materias
    Then ve "Ingeniería de Software" y no ve "Gestión de Proyectos"

  Scenario: No puede tocar un banco ajeno
    When el Docente A intenta cargar o editar una pregunta del banco de "Gestión de Proyectos"
    Then recibe 403 y el banco no cambia

  Scenario: Solo ve sus Comisiones
    Given el Docente A también ve una segunda Comisión de "Ingeniería de Software" a la que no está asignado
    When abre las Comisiones de la materia
    Then solo ve la suya

  Scenario: No puede crear una sesión en vivo en una Comisión ajena
    When el Docente A intenta crear una sesión en vivo en la Comisión del Docente B
    Then recibe 403

  Scenario: No ve reportes de otra materia
    When el Docente A pide un reporte de Analytics de "Gestión de Proyectos"
    Then recibe 403

  Scenario: El Administrador ve todo
    When el Administrador abre el listado de materias y de Comisiones
    Then ve ambas materias y todas sus Comisiones

  Scenario: Materia recién creada sin Docente
    Given una materia sin Comisiones con Docente asignado
    When cualquier Docente abre el listado de materias
    Then no aparece

  Scenario: Docente asignado opera sobre una actividad de período abierto sin restricción de Comisión
    Given una actividad de período abierto de "Ingeniería de Software" sin restricción de Comisión
    When el Docente A abre el detalle de esa actividad
    Then puede verla y modificarla (mismo criterio que su propia Comisión)
