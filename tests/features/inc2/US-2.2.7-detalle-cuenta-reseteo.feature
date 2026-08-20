@US-2.2.7
Feature: Detalle de cuenta y reseteo desde la UI (US-2.2.7)
  Como Administrador
  Quiero ver el detalle de una cuenta y, si hace falta, resetear su contraseña
  Para resolver un bloqueo o un pedido de recuperación completo, desde la aplicación
  (RF-03)

  @frontend @happy-path
  Scenario: Ver el detalle de una cuenta bloqueada
    Given un Administrador navega al detalle de una cuenta con bloqueada = true
    Then ve una alerta indicando que la cuenta está bloqueada

  @frontend @happy-path
  Scenario: Resetear contraseña exitosamente
    Given un Administrador en el formulario de reseteo de una cuenta
    When ingresa una contraseña nueva válida y confirma
    Then el sistema ejecuta el reseteo
    And navega a la pantalla de confirmación
    And la cuenta ya no aparece como bloqueada al volver a consultarla

  @frontend @happy-path
  Scenario: Cancelar el reseteo
    Given un Administrador en el formulario de reseteo
    When hace clic en "Cancelar"
    Then el sistema vuelve al detalle de la cuenta sin ejecutar ningún cambio
