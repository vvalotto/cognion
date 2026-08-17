@US-2.1.13
Feature: Eliminación de pregunta desde la UI (US-2.1.13)
  Como Docente
  Quiero eliminar una pregunta desde la UI, con una confirmación previa que aclare que es una
  baja lógica
  Para evitar eliminaciones accidentales y entender que las sesiones pasadas no se ven afectadas

  @frontend @happy-path
  Scenario: Confirmar eliminación
    Given un Docente en la confirmación de eliminación de una pregunta
    When hace clic en "Sí, eliminar"
    Then el sistema ejecuta la baja lógica
    And vuelve al banco filtrado, la pregunta ya no aparece en la tabla

  @frontend @edge-case
  Scenario: Cancelar eliminación
    Given un Docente en la confirmación de eliminación de una pregunta
    When hace clic en "Cancelar"
    Then el sistema vuelve al banco filtrado
    And la pregunta sigue apareciendo en la tabla, sin cambios
