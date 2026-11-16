@US-12.1.1
Feature: El canal en vivo solo lo abren quienes pertenecen a la comisión (US-12.1.1)
  Como docente de una comisión
  Quiero que solo los miembros de mi comisión puedan escuchar el canal de mi sesión en vivo
  Para que alguien de otra comisión no reciba los enunciados ni el ranking de mi clase

  @backend @happy-path
  Scenario: Docente asignado a la comisión conecta
    Given una sesión en vivo de la comisión C1 y un docente asignado a C1
    When el docente abre el canal de la sesión
    Then la conexión se acepta

  @backend @happy-path
  Scenario: Estudiante de la comisión conecta antes de unirse
    Given una sesión en vivo de la comisión C1 y un estudiante de C1 que todavía no se unió
    When el estudiante abre el canal de la sesión
    Then la conexión se acepta

  @backend @happy-path
  Scenario: Administrador conecta
    Given una sesión en vivo de la comisión C1 y un administrador
    When el administrador abre el canal de la sesión
    Then la conexión se acepta

  @backend @error
  Scenario: Estudiante de otra comisión es rechazado
    Given una sesión en vivo de la comisión C1 y un estudiante de la comisión C2
    When el estudiante abre el canal de la sesión
    Then la conexión se cierra con el código 1008

  @backend @error
  Scenario: Docente no asignado a la comisión es rechazado
    Given una sesión en vivo de la comisión C1 y un docente asignado solo a C2
    When el docente abre el canal de la sesión
    Then la conexión se cierra con el código 1008

  @backend @error
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When un usuario autenticado abre el canal
    Then la conexión se cierra con el código 1008

  @backend @sin-cambios
  Scenario: Sin token o con token inválido
    When se abre el canal sin token, o con un token inválido o vencido
    Then la conexión se cierra con el código 1008
