@US-ADJ-36
Feature: Contraseña segura — política ampliada (US-ADJ-36)
  Como Administrador del sistema
  Quiero exigir contraseñas más largas y con mezcla de tipos de caracteres
  Para reducir el riesgo de cuentas comprometidas por fuerza bruta o diccionario

  @password-segura @happy-path
  Scenario: Contraseña que cumple las 4 reglas es aceptada
    Given una contraseña nueva "Segura#2026x"
    When se valida con Usuario.validar_password_nueva
    Then la validación no lanza ninguna excepción

  @password-segura @error
  Scenario: Contraseña demasiado corta es rechazada
    Given una contraseña nueva "Ab1#567"
    When se valida con Usuario.validar_password_nueva
    Then el sistema rechaza con PasswordDemasiadoCorta

  @password-segura @error
  Scenario: Contraseña larga sin mayúscula es rechazada
    Given una contraseña nueva "segura#2026x"
    When se valida con Usuario.validar_password_nueva
    Then el sistema rechaza con PasswordSinComplejidadSuficiente

  @password-segura @error
  Scenario: Contraseña larga sin número es rechazada
    Given una contraseña nueva "Segura#abcdx"
    When se valida con Usuario.validar_password_nueva
    Then el sistema rechaza con PasswordSinComplejidadSuficiente

  @password-segura @error
  Scenario: Contraseña larga sin símbolo es rechazada
    Given una contraseña nueva "Segura2026xx"
    When se valida con Usuario.validar_password_nueva
    Then el sistema rechaza con PasswordSinComplejidadSuficiente

  @password-segura @gap-cerrado @happy-path
  Scenario: Administrador da de alta un Docente con contraseña válida
    Given un Administrador autenticado
    When ejecuta CrearUsuario con password "Segura#2026x" y perfil Docente
    Then el Usuario se crea exitosamente

  @password-segura @gap-cerrado @error
  Scenario: Administrador intenta dar de alta un Docente con contraseña débil
    Given un Administrador autenticado
    When ejecuta CrearUsuario con password "abc123" y perfil Docente
    Then el sistema rechaza con PasswordDemasiadoCorta
    And ningún Usuario se crea

  @password-segura @gap-cerrado @happy-path
  Scenario: Estudiante se registra vía invitación con contraseña válida
    Given una Invitación vigente para una Comisión
    When ejecuta RegistrarEstudiante con password "Segura#2026x"
    Then el Usuario se crea exitosamente con perfil Estudiante

  @password-segura @gap-cerrado @error
  Scenario: Estudiante intenta registrarse vía invitación con contraseña débil
    Given una Invitación vigente para una Comisión
    When ejecuta RegistrarEstudiante con password "abc123"
    Then el sistema rechaza con PasswordDemasiadoCorta
    And ningún Usuario se crea
    And la Invitación sigue sin usarse
