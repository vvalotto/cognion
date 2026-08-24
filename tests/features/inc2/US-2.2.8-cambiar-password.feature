@US-2.2.8
Feature: Cambio de contraseña propio desde la UI (US-2.2.8)
  Como Usuario autenticado (Administrador, Docente o Estudiante)
  Quiero cambiar mi propia contraseña desde la aplicación
  Para actualizarla cuando quiera, sin pedirle ayuda al Administrador (RF-19)

  @frontend @happy-path
  Scenario: Cambio exitoso
    Given un Usuario autenticado en la pantalla "Cambiar mi contraseña"
    When ingresa su contraseña actual correcta y una nueva válida
    Then el sistema ejecuta el cambio
    And navega a la confirmación de éxito
    And no requiere volver a iniciar sesión

  @frontend @error
  Scenario: Contraseña actual incorrecta
    Given un Usuario autenticado en la pantalla "Cambiar mi contraseña"
    When ingresa una contraseña actual incorrecta
    Then el sistema muestra la alerta de error con los intentos restantes
    And los campos quedan vacíos para reintentar

  @frontend @error
  Scenario: La cuenta queda bloqueada tras el tercer fallo
    Given un Usuario con 2 intentos fallidos previos de este flujo
    When ingresa la contraseña actual incorrecta una vez más
    Then el sistema muestra que la cuenta quedó bloqueada
    And indica que debe contactar a un Administrador
