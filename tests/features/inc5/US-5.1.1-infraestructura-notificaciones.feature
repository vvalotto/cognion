@US-5.1.1
Feature: Infraestructura del BC Notificaciones (US-5.1.1)
  Como Sistema
  Quiero contar con los puertos y adapters de infraestructura del BC Notificaciones —
  resolución de destinatarios con email y envío por SMTP real de prueba
  Para que US-5.1.2/US-5.1.3 puedan disparar el envío de un email real sin tener que resolver
  de nuevo el mecanismo de destinatarios ni el canal de envío

  @happy-path
  Scenario: Roster combinado de varias comisiones sin duplicados
    Given un estudiante inscripto en las comisiones A y B
    And otro estudiante inscripto solo en la comisión A
    When se invoca ComisionConsultaPort.listar_destinatarios([A, B])
    Then el roster devuelto tiene 2 destinatarios, sin el primero repetido

  @happy-path
  Scenario: Resolver todas las comisiones de una materia
    Given una materia con 3 comisiones activas y 1 inactiva
    When se invoca ComisionConsultaPort.listar_comisiones_por_materia(materia_id)
    Then el roster devuelto tiene las 3 comisiones activas

  @edge-case
  Scenario: Comisión sin estudiantes
    Given una comisión recién creada, sin inscripciones
    When se invoca ComisionConsultaPort.listar_destinatarios([comision_id])
    Then el roster devuelto está vacío

  @integration
  Scenario: Query de Identidad expone email sin romper el consumidor existente
    Given una comisión con 2 estudiantes inscriptos
    When se invoca ComisionQueryPort.listar_estudiantes_con_email(comision_id)
    Then cada elemento incluye id, nombre y email
    And ComisionQueryPort.listar_estudiantes(comision_id) sigue devolviendo solo id y nombre

  @integration
  Scenario: Envío real contra el SMTP local de prueba
    Given el servidor SMTP de prueba corriendo localmente
    When se invoca CanalEnvioPort.enviar("estudiante@example.com", "Asunto de prueba", "Cuerpo de prueba")
    Then el mensaje aparece en la bandeja del servidor de prueba con ese asunto y destinatario
