@US-2.1.8
Feature: Infraestructura de frontend del Banco de Preguntas (US-2.1.8)
  Como Equipo de desarrollo
  Quiero las rutas y el cliente API del BC Banco de Preguntas montados en el frontend
  Para tener la base sobre la que se construyen las pantallas de materias, banco y
  carga de preguntas (US-2.1.9 a US-2.1.13)

  @infra @happy-path
  Scenario: Ruta protegida por rol
    Given un Usuario autenticado con rol distinto de docente
    When intenta navegar a /materias
    Then el sistema lo redirige fuera de la ruta (mismo comportamiento que RequireRole en US-1.1.9)

  @infra @happy-path
  Scenario: Cliente API disponible
    Given el módulo banco-preguntas-api.ts
    When se invoca cualquiera de sus funciones
    Then reutiliza el mismo manejo de JWT/401/403 que api-client.ts (US-1.1.6)
