@US-2.1.1
Feature: Alta de materia y banco (US-2.1.1)
  Como Administrador
  Quiero dar de alta una materia y que se cree automáticamente su banco de preguntas
  Para tener un espacio donde cargar y clasificar las preguntas de esa materia (RF-04, RF-06)

  # Actor actualizado a Administrador — unificación con Comisión (hallazgo de UAT,
  # Incremento 5-ADJ): crear Materia pasa a ser exclusivo del Administrador, el Docente
  # consume el banco pero no crea la Materia. RF-04/RF-06 sin cambios de fondo.

  Background:
    Given un Administrador autenticado

  @crear-materia @happy-path
  Scenario: Administrador crea una materia nueva
    Given no existe ninguna Materia con nombre "Ingeniería de Software"
    When ejecuta CrearMateria(nombre="Ingeniería de Software")
    Then el sistema persiste la Materia con ese nombre
    And crea automáticamente su Banco asociado con materia_id apuntando a esa Materia
    And se emiten los eventos MateriaCreada y BancoCreado

  @crear-materia @error
  Scenario: Rechazo por nombre duplicado
    Given una Materia existente con nombre "Ingeniería de Software"
    When un Administrador ejecuta CrearMateria(nombre="Ingeniería de Software")
    Then el sistema rechaza la operación con MateriaYaExiste
    And no se crea ninguna Materia ni Banco nuevos

  @crear-materia @error
  Scenario: Rechazo por nombre vacío
    Given un Administrador autenticado
    When ejecuta CrearMateria(nombre="")
    Then el sistema rechaza la operación por nombre inválido
    And no se crea ninguna Materia ni Banco nuevos

  @crear-materia @error
  Scenario: Rechazo por rol Docente
    Given un Docente autenticado
    When intenta ejecutar CrearMateria(nombre="Rechazo Docente")
    Then el sistema rechaza la operación por rol insuficiente
