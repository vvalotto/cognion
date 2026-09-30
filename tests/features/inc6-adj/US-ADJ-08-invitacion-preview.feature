@US-ADJ-08
Feature: Vista previa de la invitación antes de registrarse (US-ADJ-08)
  Como Estudiante que abre un link de invitación
  Quiero ver a qué materia y comisión me voy a unir antes de completar el formulario
  Para confirmar que el link es el correcto antes de crear mi cuenta

  @happy-path
  Scenario: Invitación vigente muestra materia y horario de la comisión
    Given una Invitación vigente para una Comisión de una Materia existente
    When se consulta GET /identidad/invitaciones/{token} con ese token
    Then la respuesta tiene status code 200
    And la respuesta contiene el nombre de la Materia
    And la respuesta contiene el horario de la Comisión
    And la respuesta no contiene el docente_id de la invitación
    And la respuesta no contiene ningún email destinatario

  @error
  Scenario: Token inexistente
    Given un token que no corresponde a ninguna Invitación
    When se consulta GET /identidad/invitaciones/{token} con ese token
    Then la respuesta tiene status code 404

  @error
  Scenario: Invitación vencida
    Given una Invitación cuyo expira_en ya pasó
    When se consulta GET /identidad/invitaciones/{token} con ese token
    Then la respuesta tiene status code 422

  @error
  Scenario: Invitación ya usada
    Given una Invitación con usada_en distinto de null
    When se consulta GET /identidad/invitaciones/{token} con ese token
    Then la respuesta tiene status code 422

  @error @sin-efecto
  Scenario: Consultar la invitación no la consume
    Given una Invitación vigente
    When se consulta GET /identidad/invitaciones/{token} con ese token dos veces seguidas
    Then ambas respuestas tienen status code 200
    And la Invitación sigue vigente (usada_en sigue en null)
