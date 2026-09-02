@US-3.4.1
Feature: Infraestructura de frontend de Actividad Evaluativa (US-3.4.1)
  Como Equipo de desarrollo
  Quiero las rutas y el cliente API del BC Actividad Evaluativa montados en el frontend
  Para tener la base sobre la que se construyen las 6 US de pantallas siguientes
  (US-3.4.2 a US-3.4.7)

  @infra @happy-path
  Scenario: Ruta de docente protegida por rol
    Given un Usuario autenticado con rol distinto de docente
    When intenta navegar a /actividad-evaluativa/materias
    Then el sistema lo redirige fuera de la ruta (mismo comportamiento que RequireRole en US-1.1.9)

  @infra @happy-path
  Scenario: Ruta de estudiante protegida por rol
    Given un Usuario autenticado con rol distinto de estudiante
    When intenta navegar a /mis-actividades/materias
    Then el sistema lo redirige fuera de la ruta (mismo comportamiento que RequireRole en US-1.1.9)

  @infra @happy-path
  Scenario: Cliente API disponible
    Given el módulo actividad-evaluativa-api.ts
    When se invoca cualquiera de sus funciones
    Then reutiliza el mismo manejo de JWT/401/403 que api-client.ts (US-1.1.6)
