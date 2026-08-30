@US-3.4.3
Feature: Creación de actividad de período abierto desde la UI (US-3.4.3)
  Como Docente
  Quiero crear una actividad de período abierto indicando ventana de disponibilidad, cantidad
  de preguntas e intentos permitidos
  Para habilitar una evaluación que mis estudiantes puedan rendir sin coordinación en vivo
  (RF-11)

  @happy-path
  Scenario: Creación exitosa
    Given un Docente en el formulario de nueva actividad, con apertura/cierre/preguntas/intentos válidos
    When completa el formulario y guarda
    Then el sistema crea la actividad
    And vuelve al listado de actividades, mostrando la nueva

  @edge-case
  Scenario: Rechazo de cliente por período inválido
    Given un Docente con fecha de cierre anterior a la de apertura
    When intenta guardar
    Then el formulario bloquea el envío con un mensaje de validación
    And no se llama al backend

  @edge-case
  Scenario: Rechazo del servidor por preguntas insuficientes
    Given un Docente que pide más preguntas de las activas en el banco de la materia
    When guarda
    Then el backend responde 422 PreguntasInsuficientes
    And el formulario muestra el error inline
