@US-12.1.2
Feature: Unirse, consultar y ver el ranking de una sesión en vivo exige pertenecer a la comisión (US-12.1.2)
  Como docente de una comisión
  Quiero que solo los miembros de mi comisión puedan unirse a mi sesión en vivo, consultar su estado y ver su ranking
  Para que un alumno de otra comisión no aparezca en mi ranking ni vea lo que no le corresponde

  @backend @happy-path
  Scenario: Estudiante de la comisión se une
    Given una sesión en vivo de la comisión C1 y un estudiante de C1
    When el estudiante se une a la sesión
    Then la unión se acepta

  @backend @error
  Scenario: Estudiante de otra comisión no puede unirse
    Given una sesión en vivo de la comisión C1 y un estudiante de la comisión C2
    When el estudiante intenta unirse a la sesión
    Then se rechaza con 403
    And el estudiante no figura entre los participantes

  @backend @error
  Scenario: Estudiante de otra comisión no consulta el estado
    Given una sesión en vivo de la comisión C1 y un estudiante de la comisión C2
    When el estudiante consulta el estado de la sesión
    Then se rechaza con 403

  @backend @error
  Scenario: Docente no asignado no consulta el estado
    Given una sesión en vivo de la comisión C1 y un docente asignado solo a C2
    When el docente consulta el estado de la sesión
    Then se rechaza con 403

  @backend @error
  Scenario: Estudiante de otra comisión no ve el ranking
    Given una sesión finalizada de la comisión C1 y un estudiante de la comisión C2
    When el estudiante pide el ranking
    Then se rechaza con 403

  @backend @happy-path
  Scenario: Docente asignado consulta estado y ranking
    Given una sesión en vivo de la comisión C1 y un docente asignado a C1
    When el docente consulta el estado y el ranking
    Then recibe la respuesta

  @backend @error
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When un usuario autenticado intenta unirse, consultar el estado o pedir el ranking
    Then se responde 404
