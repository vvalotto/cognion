@US-1.1.6
Feature: Infraestructura de frontend (US-1.1.6)
  Como Desarrollador
  Quiero routing y un cliente API con manejo de sesión (JWT) en frontend/
  Para que las pantallas de Identidad (US-1.1.7 a US-1.1.9) tengan la infraestructura
  mínima sobre la que construirse

  @infra @happy-path
  Scenario: El cliente adjunta el JWT en un request a un endpoint protegido
    Given una sesión con un JWT guardado
    When el cliente API ejecuta un request a un endpoint protegido
    Then el request incluye el header "Authorization: Bearer <token>"

  @infra @error
  Scenario: Un 401 del backend limpia la sesión y redirige a login
    Given una sesión con un JWT guardado (vencido o inválido)
    When el backend responde 401 a cualquier request
    Then el cliente limpia el JWT guardado
    And el router navega a "/login"

  @infra @error
  Scenario: Un 403 del backend muestra acceso denegado sin filtrar el recurso
    Given una sesión con un JWT válido pero rol insuficiente
    When el backend responde 403 a un request
    Then la UI muestra un mensaje genérico de acceso denegado
    And el mensaje no revela qué recurso se intentó acceder
