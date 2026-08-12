@US-1.1.8
Feature: Registro desde la UI (US-1.1.8)
  Como Estudiante que recibió un link de invitación por email
  Quiero completar mi registro desde una pantalla web
  Para quedar asignado automáticamente a mi comisión sin aprobación del docente (RF-01)

  @happy-path
  Scenario: Registro exitoso con invitación vigente
    Given una URL de registro con un token vigente
    When completa el formulario con nombre, email y contraseña válidos
    Then el sistema crea el Usuario con perfil Estudiante
    And muestra la pantalla de registro exitoso
    And el Estudiante no queda autenticado automáticamente

  @error
  Scenario: Registro rechazado por token vencido
    Given una URL de registro con un token cuyo expira_en ya pasó
    When completa el formulario
    Then el sistema muestra la pantalla de error de registro
    And el mensaje no distingue el motivo del rechazo

  @error
  Scenario: Registro rechazado por token ya usado
    Given una URL de registro con un token ya usado
    When completa el formulario
    Then el sistema muestra la misma pantalla de error que ante un token vencido

  @error
  Scenario: Registro rechazado por token inexistente
    Given una URL de registro con un token que no corresponde a ninguna invitación
    When completa el formulario
    Then el sistema muestra la misma pantalla de error que ante un token vencido

  @error
  Scenario: Registro rechazado por email ya registrado
    Given una URL de registro con un token vigente
    When completa el formulario con un email ya registrado
    Then el sistema muestra el error en el propio formulario
    And no navega a la pantalla de error de token
