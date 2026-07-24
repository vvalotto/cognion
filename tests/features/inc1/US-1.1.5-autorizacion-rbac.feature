@US-1.1.5
Feature: Autorización por rol (RBAC) (US-1.1.5)
  Como Sistema
  Quiero verificar el rol del Usuario autenticado en cada request a un recurso protegido
  Para que un Estudiante no pueda acceder a la gestión del banco de preguntas ni a analytics
  globales, y un Docente no pueda acceder a las herramientas de administración de cuentas
  (RF-02)

  @autorizacion @happy-path
  Scenario: Acceso concedido con rol suficiente
    Given un JWT válido con rol "administrador"
    When se solicita un endpoint de administración de cuentas
    Then el sistema concede el acceso y ejecuta el handler

  @autorizacion @error
  Scenario: Estudiante rechazado en gestión del banco de preguntas
    Given un JWT válido con rol "estudiante"
    When se solicita un endpoint de gestión del banco de preguntas
    Then el sistema responde 403 Forbidden

  @autorizacion @error
  Scenario: Estudiante rechazado en analytics globales
    Given un JWT válido con rol "estudiante"
    When se solicita un endpoint de analytics globales
    Then el sistema responde 403 Forbidden

  @autorizacion @error
  Scenario: Docente rechazado en administración de cuentas
    Given un JWT válido con rol "docente"
    When se solicita un endpoint de administración de cuentas (US-1.1.0)
    Then el sistema responde 403 Forbidden

  @autorizacion @error
  Scenario: Request sin JWT
    Given un request a un recurso protegido sin header Authorization
    When se procesa el request
    Then el sistema responde 401 Unauthorized

  @autorizacion @error
  Scenario: JWT expirado
    Given un JWT cuyo exp ya pasó (más de 60 minutos desde la emisión, ADR-013)
    When se solicita cualquier recurso protegido
    Then el sistema responde 401 Unauthorized
