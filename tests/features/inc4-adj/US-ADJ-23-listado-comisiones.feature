@US-ADJ-23
Feature: Administrador ve el listado de Comisiones de una Materia (US-ADJ-23)
  Como Administrador
  Quiero ver el listado de Comisiones de una Materia, con horario, Docentes asignados y
  cantidad de Estudiantes inscriptos
  Para poder gestionar Comisiones (crear, asignar Docente) sin depender de consultas
  manuales en la base de datos

  @happy-path
  Scenario: Comisión con Docente asignado y Estudiantes inscriptos
    Given una materia con una comisión que tiene un docente asignado y 3 estudiantes inscriptos
    When un Administrador hace GET /materias/{materia_id}/comisiones
    Then recibe 200 con la comisión, incluido el id del docente asignado

  @happy-path
  Scenario: Comisión sin Docente asignado
    Given una materia con una comisión sin ningún docente asignado
    When un Administrador hace GET /materias/{materia_id}/comisiones
    Then recibe 200 con la comisión y docentes_asignados vacío

  @edge-case
  Scenario: Materia sin comisiones
    Given una materia sin ninguna comisión
    When un Administrador hace GET /materias/{materia_id}/comisiones
    Then recibe 200 con lista vacía

  @error-case
  Scenario: Materia inexistente
    Given un id de materia que no existe
    When un Administrador hace GET /materias/{id-inexistente}/comisiones
    Then recibe 404

  @regression
  Scenario: Docente sigue teniendo acceso al mismo endpoint
    Given una materia con una comisión
    When un Docente hace GET /materias/{materia_id}/comisiones
    Then recibe 200, mismo comportamiento que antes de esta US

  @regression
  Scenario: Docente sigue teniendo acceso al listado de estudiantes de una comisión
    Given una comisión con estudiantes inscriptos
    When un Docente hace GET /comisiones/{comision_id}/estudiantes
    Then recibe 200 con los estudiantes

  @error-case
  Scenario: Estudiante no tiene acceso al listado de comisiones
    Given un Estudiante autenticado
    When hace GET /materias/{materia_id}/comisiones
    Then recibe 403

  @error-case
  Scenario: Estudiante no tiene acceso al listado de estudiantes de una comisión
    Given un Estudiante autenticado
    When hace GET /comisiones/{comision_id}/estudiantes
    Then recibe 403
