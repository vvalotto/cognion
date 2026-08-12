@US-1.1.7
Feature: Login desde la UI (US-1.1.7)
  Como Docente, Administrador o Estudiante con una cuenta ya creada
  Quiero autenticarme desde una pantalla de login
  Para recibir un JWT con mi rol y poder operar el resto del sistema según mis permisos (RF-02)

  @happy-path
  Scenario: Login exitoso
    Given un Usuario con cuenta existente y contraseña "Docente#2026"
    When completa el formulario de login con su email y esa contraseña
    Then el sistema guarda el JWT recibido
    And redirige a la vista correspondiente a su rol

  @error
  Scenario: Login rechazado por credenciales inválidas
    Given un Usuario con cuenta existente
    When completa el formulario de login con una contraseña incorrecta
    Then el sistema muestra la pantalla de error de login
    And el mensaje no distingue si el email existe

  @error
  Scenario: Login rechazado por email inexistente
    Given ningún Usuario registrado con el email ingresado
    When completa el formulario de login
    Then el sistema muestra la misma pantalla de error que ante contraseña incorrecta
