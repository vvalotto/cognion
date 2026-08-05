@US-2.1.2
Feature: Comisión referencia Materia por puerto (US-2.1.2)
  Como equipo de desarrollo
  Quiero que Comisión.materia deje de ser un string libre y referencie la Materia
  dueña de BC Banco de Preguntas por un puerto de dominio
  Para tener una única fuente de verdad de qué materias existen, sin imports
  directos entre BCs

  @migracion @happy-path
  Scenario: Migración de datos existentes
    Given una Comisión persistida en BL-002 con materia = "Ingeniería de Software" (string)
    And una Materia con nombre "Ingeniería de Software" creada en US-2.1.1
    When se ejecuta la migración de datos
    Then la Comisión queda con materia_id apuntando a esa Materia

  @crear-comision @happy-path
  Scenario: Alta de comisión con materia_id válido
    Given un Administrador autenticado
    And una Materia existente con id <materia_id>
    When ejecuta CrearComision(materia_id=<materia_id>, horario, administrador_id)
    Then el sistema valida la existencia de la Materia a través de MateriaPort
    And la Comisión se persiste con ese materia_id

  @crear-comision @error
  Scenario: Alta de comisión valida la materia por el puerto
    Given un Administrador autenticado
    When ejecuta CrearComision(materia_id=<id inexistente>, horario, administrador_id)
    Then el sistema rechaza la operación con MateriaNoExiste
    And no se crea ninguna Comisión

  @arquitectura
  Scenario: Sin imports directos entre BCs
    Given el código de src/identidad/
    When se revisan sus imports
    Then ningún módulo de src/identidad/ importa directamente src/banco_preguntas/
    And la única comunicación es a través de src/identidad/entities/ports/materia_port.py
