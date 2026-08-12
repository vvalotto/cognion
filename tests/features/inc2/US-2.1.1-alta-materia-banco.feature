@US-2.1.1
Feature: Alta de materia y banco (US-2.1.1)
  Como Docente
  Quiero dar de alta una materia y que se cree automáticamente su banco de preguntas
  Para tener un espacio donde cargar y clasificar las preguntas de esa materia (RF-04, RF-06)

  Background:
    Given un Docente autenticado

  @crear-materia @happy-path
  Scenario: Docente crea una materia nueva
    Given no existe ninguna Materia con nombre "Ingeniería de Software"
    When ejecuta CrearMateria(nombre="Ingeniería de Software")
    Then el sistema persiste la Materia con ese nombre
    And crea automáticamente su Banco asociado con materia_id apuntando a esa Materia
    And se emiten los eventos MateriaCreada y BancoCreado

  @crear-materia @error
  Scenario: Rechazo por nombre duplicado
    Given una Materia existente con nombre "Ingeniería de Software"
    When un Docente ejecuta CrearMateria(nombre="Ingeniería de Software")
    Then el sistema rechaza la operación con MateriaYaExiste
    And no se crea ninguna Materia ni Banco nuevos

  @crear-materia @error
  Scenario: Rechazo por nombre vacío
    Given un Docente autenticado
    When ejecuta CrearMateria(nombre="")
    Then el sistema rechaza la operación por nombre inválido
    And no se crea ninguna Materia ni Banco nuevos
