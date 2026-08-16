@US-2.1.11
Feature: Carga de pregunta desde la UI (US-2.1.11)
  Como Docente
  Quiero elegir el tipo de pregunta (Opción Múltiple o Verdadero/Falso) y completar
  el formulario correspondiente
  Para cargar preguntas al banco desde la UI, sin usar la API directamente (RF-04, RF-05)

  @frontend @happy-path
  Scenario: Elegir tipo Opción Múltiple
    Given un Docente en la pantalla de selección de tipo
    When elige "Opción múltiple"
    Then el sistema muestra el formulario con lista de opciones y radio de correcta

  @frontend @happy-path
  Scenario: Carga exitosa de Opción Múltiple
    Given un Docente en el formulario de Opción Múltiple con 3 opciones y una marcada correcta
    When completa el texto y guarda
    Then el sistema crea la pregunta
    And vuelve al banco filtrado, mostrando la pregunta nueva

  @frontend @edge-case
  Scenario: Rechazo de cliente por opciones inválidas
    Given un Docente en el formulario de Opción Múltiple sin ninguna opción marcada como correcta
    When intenta guardar
    Then el formulario bloquea el envío con un mensaje de validación
    And no se llama al backend

  @frontend @happy-path
  Scenario: Carga exitosa de Verdadero/Falso
    Given un Docente en el formulario de Verdadero/Falso
    When completa el texto, elige "Verdadero" y guarda
    Then el sistema crea la pregunta
    And vuelve al banco filtrado
