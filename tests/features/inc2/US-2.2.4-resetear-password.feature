@US-2.2.4
Feature: Reseteo de contraseña con desbloqueo (US-2.2.4)
  Como Administrador
  Quiero resetear la contraseña de una cuenta
  Para resolver tanto un pedido de recuperación como una cuenta bloqueada, sin que el
  docente tenga que intervenir (RF-03)

  @resetear-password @happy-path
  Scenario: Reseteo de cuenta bloqueada
    Given un Usuario con bloqueada = true
    When un Administrador ejecuta ResetearPassword(usuario_id, "nuevaClave123", administrador_id)
    Then el sistema actualiza password_hash
    And bloqueada pasa a false, los contadores vuelven a 0
    And se emiten PasswordReseteada y CuentaDesbloqueada

  @resetear-password @happy-path
  Scenario: Reseteo de cuenta activa (no bloqueada)
    Given un Usuario con bloqueada = false
    When un Administrador ejecuta ResetearPassword(usuario_id, "nuevaClave123", administrador_id)
    Then el sistema actualiza password_hash
    And se emite PasswordReseteada, sin CuentaDesbloqueada

  @resetear-password @error
  Scenario: Rechazo por contraseña demasiado corta
    Given un Usuario existente
    When un Administrador ejecuta ResetearPassword(usuario_id, "corta", administrador_id)
    Then el sistema rechaza con PasswordDemasiadoCorta
