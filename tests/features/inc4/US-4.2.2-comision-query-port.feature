@US-4.2.2
Feature: Consulta de comisiones por materia y estudiantes por comisión (US-4.2.2)
  Como Docente
  Quiero que el sistema sepa qué comisiones tiene una materia y qué estudiantes integran una
  comisión
  Para poder elegir en cascada Materia → Comisión → Estudiante en las pantallas de desempeño
  (RF-16, RF-17)

  @happy-path
  Scenario: Materia con comisiones
    Given una materia X con 2 comisiones
    When un Docente hace GET /materias/X/comisiones
    Then recibe 200 con las 2 comisiones (id, horario)

  @happy-path
  Scenario: Comisión con estudiantes
    Given una comisión con 3 estudiantes inscriptos
    When un Docente hace GET /comisiones/{comision_id}/estudiantes
    Then recibe 200 con los 3 estudiantes

  @edge-case
  Scenario: Comisión sin estudiantes
    Given una comisión recién creada, sin inscripciones
    When un Docente hace GET /comisiones/{comision_id}/estudiantes
    Then recibe 200 con lista vacía

  @error-case
  Scenario: Materia inexistente
    Given un id de materia que no existe
    When un Docente hace GET /materias/{id-inexistente}/comisiones
    Then recibe 404

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /materias/X/comisiones
    Then recibe 403

  @integration
  Scenario: Analytics consume el adapter in-process
    Given el mismo estado de datos que el escenario "Materia con comisiones"
    When ComisionConsultaPort.listar_comisiones_por_materia(X) se invoca in-process
    Then devuelve el mismo resultado que el endpoint HTTP equivalente
