@US-2.1.9
Feature: Listado y alta de materias (US-2.1.9)
  Como Docente
  Quiero ver el listado de materias y dar de alta una nueva desde la UI
  Para acceder al banco de cada materia y crear materias nuevas sin usar la API
  directamente (RF-04)

  @backend @happy-path
  Scenario: GET /materias devuelve la cantidad de preguntas activas por materia
    Given una materia con 3 preguntas activas y 1 pregunta eliminada (baja lógica)
    When se hace GET /materias
    Then la materia aparece en la respuesta con cantidad_preguntas_activas = 3

  @frontend @happy-path
  Scenario: Ver el listado de materias
    Given un Docente autenticado con materias existentes
    When navega a la pantalla de materias
    Then ve una tarjeta por cada materia con su cantidad de preguntas activas

  @frontend @happy-path
  Scenario: Alta exitosa de materia
    Given un Docente autenticado en el listado de materias
    When completa el formulario de nueva materia con un nombre no usado
    Then el sistema crea la materia y su banco
    And vuelve al listado, mostrando la materia nueva

  @frontend @error
  Scenario: Rechazo por nombre duplicado
    Given una materia existente con nombre "Ingeniería de Software"
    When un Docente intenta crear una materia con ese mismo nombre
    Then el sistema muestra un error inline en el formulario
    And no navega fuera de la pantalla de alta
