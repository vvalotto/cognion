@US-5.1.2
Feature: Notificación de apertura de una Actividad Evaluativa de período abierto (US-5.1.2)
  Como Estudiante
  Quiero recibir un email cuando el Docente crea una actividad de período abierto a la que
  tengo acceso
  Para enterarme de que hay una evaluación disponible sin depender de revisar el portal por mi
  cuenta (RF-14)

  @happy-path
  Scenario: Actividad restringida a comisiones específicas
    Given una materia con las comisiones A (2 estudiantes) y B (1 estudiante)
    When un Docente crea una actividad de período abierto restringida a [A, B]
    Then se envían 3 emails, uno por cada estudiante de A y B
    And cada email contiene el título, fecha de apertura, fecha de cierre y materia

  @happy-path
  Scenario: Actividad sin restricción de comisión
    Given una materia con las comisiones A y B, sin ninguna otra comisión
    When un Docente crea una actividad de período abierto sin comisiones_ids
    Then se envían emails a todos los estudiantes de A y B

  @edge-case
  Scenario: Fallo de envío a un destinatario no aborta el resto
    Given una actividad restringida a la comisión A con 2 estudiantes
    And el envío al primer estudiante falla (SMTP no disponible momentáneamente)
    When se dispara la notificación de apertura
    Then el segundo estudiante igual recibe su email
    And la creación de la actividad responde 201 igual

  @edge-case
  Scenario: Materia sin comisiones
    Given una materia recién creada, sin ninguna comisión
    When un Docente crea una actividad de período abierto sin comisiones_ids
    Then no se envía ningún email
    And la creación de la actividad responde 201 igual
