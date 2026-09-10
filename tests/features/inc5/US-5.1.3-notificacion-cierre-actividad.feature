@US-5.1.3
Feature: Notificación de cierre manual de una Actividad Evaluativa de período abierto (US-5.1.3)
  Como Estudiante
  Quiero recibir un email cuando el Docente cierra manualmente una actividad de período abierto
  a la que tengo acceso
  Para enterarme de que ya no puedo rendirla, sin depender de revisar el portal (RF-14)

  @happy-path
  Scenario: Cierre manual de actividad restringida a comisiones específicas
    Given una actividad vigente restringida a las comisiones A (2 estudiantes) y B (1 estudiante)
    When el Docente la cierra manualmente
    Then se envían 3 emails, uno por cada estudiante de A y B
    And cada email contiene el título y la materia

  @happy-path
  Scenario: Cierre manual de actividad sin restricción
    Given una actividad vigente sin comisiones_ids, en una materia con las comisiones A y B
    When el Docente la cierra manualmente
    Then se envían emails a todos los estudiantes de A y B

  @edge-case
  Scenario: Vencimiento natural del período no dispara notificación
    Given una actividad vigente cuya fecha_cierre ya pasó, sin cierre manual del Docente
    When VerificarVencimientosUseCase corre su verificación periódica
    Then la actividad pasa a estado cerrado
    And no se envía ningún email

  @edge-case
  Scenario: Fallo de envío a un destinatario no aborta el resto
    Given una actividad restringida a la comisión A con 2 estudiantes
    And el envío al primer estudiante falla (SMTP no disponible momentáneamente)
    When el Docente cierra la actividad manualmente
    Then el segundo estudiante igual recibe su email de cierre
    And el cierre responde 200 igual
