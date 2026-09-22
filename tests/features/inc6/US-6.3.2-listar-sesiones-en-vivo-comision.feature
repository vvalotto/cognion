@US-6.3.2
Feature: Listar las sesiones en vivo de una Comisión (US-6.3.2)
  Como Estudiante o Docente
  Quiero ver qué sesiones en vivo hay disponibles para mi Comisión
  Para entrar a la que está en marcha sin que nadie me pase un enlace

  @backend @happy-path
  Scenario: El Estudiante ve las sesiones activas de su Comisión
    Given una sesión EnEspera y otra EnCurso de la Comisión del Estudiante
    When el Estudiante lista las sesiones
    Then recibe las dos, con el nombre de la Materia y el estado

  @backend @happy-path
  Scenario: El Estudiante no ve las de otra Comisión
    Given una sesión activa de otra Comisión
    When el Estudiante lista las sesiones
    Then no aparece

  @backend @happy-path
  Scenario: Las sesiones finalizadas no se listan por defecto
    Given una sesión Finalizada de la Comisión
    When el Estudiante lista las sesiones
    Then no aparece

  @backend @happy-path
  Scenario: El Docente recupera la sesión activa de una Comisión
    Given una sesión EnCurso de la Comisión
    When el Docente lista las sesiones pasando la Comisión
    Then recibe esa sesión con su estado

  @backend @happy-path
  Scenario: El Docente puede pedir también las finalizadas
    Given una sesión Finalizada de la Comisión
    When el Docente lista con estado Finalizada
    Then recibe esa sesión

  @backend @error-case
  Scenario: El Docente debe indicar la Comisión
    Given un Docente autenticado
    When lista las sesiones sin comision_id
    Then el sistema responde 422

  @backend @error-case
  Scenario: El Estudiante no puede pedir otra Comisión
    Given un Estudiante autenticado
    When lista las sesiones pasando la comision_id de otra Comisión
    Then el sistema responde 403

  @backend @happy-path
  Scenario: Sin sesiones
    Given una Comisión sin sesiones activas
    When se listan
    Then la respuesta es una lista vacía

  @backend @happy-path
  Scenario: Orden por recientes
    Given dos sesiones activas creadas en momentos distintos
    When se listan
    Then la más reciente aparece primero
