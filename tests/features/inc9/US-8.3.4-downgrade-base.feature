@US-8.3.4
Feature: alembic downgrade base funciona (US-8.3.4)
  Como responsable de operar Cognión
  Quiero poder deshacer las migraciones de la base hasta el estado vacío
  Para volver atrás una versión mala o ensayar una instalación limpia sin armar la base a mano

  @downgrade @happy-path
  Scenario: Deshacer todas las migraciones deja la base sin tablas de la aplicación
    Given una base descartable migrada hasta la última revisión
    When se deshacen todas las migraciones hasta la base vacía
    Then la operación termina sin error
    And no quedan tablas de la aplicación

  @downgrade
  Scenario: Migrar, deshacer y volver a migrar termina en la misma revisión
    Given una base descartable migrada hasta la última revisión
    When se deshacen todas las migraciones hasta la base vacía
    And se vuelve a migrar hasta la última revisión
    Then todas las operaciones terminaron sin error
    And la base queda en la misma revisión que antes

  @idempotencia
  Scenario: Migrar dos veces no cambia nada
    Given una base descartable migrada hasta la última revisión
    When se vuelve a migrar hasta la última revisión
    Then la operación termina sin error
    And la base queda en la misma revisión que antes

  @compatibilidad
  Scenario: La restricción de la comisión del estudiante tiene el nombre que usa el downgrade
    Given una base descartable migrada hasta la última revisión
    Then la clave foránea de la comisión del estudiante se llama "estudiante_comision_id_fkey"

  @downgrade @paso-a-paso
  Scenario: Deshacer solo la migración de la comisión del estudiante
    Given una base descartable migrada hasta la revisión "dd44a181d7fc"
    When se deshace una migración
    Then la operación termina sin error
    And la tabla de estudiantes ya no tiene la columna de la comisión
