@US-3.4.4
Feature: Detalle, extensión de plazo y cierre manual de una actividad (US-3.4.4)
  Como Docente
  Quiero ver el detalle de una actividad, extender su plazo si hace falta, o cerrarla
  manualmente antes de tiempo
  Para ajustar una actividad vigente sin depender de la API directa (RF-11b)

  @happy-path
  Scenario: Ver detalle de una actividad
    Given un Docente en el listado de actividades
    When elige una actividad
    Then ve apertura, cierre, cantidad de preguntas, intentos, evaluaciones activas y finalizadas

  @happy-path
  Scenario: Extender plazo exitosamente
    Given un Docente en el detalle de una actividad no cerrada
    When va a "Extender plazo" y guarda una fecha de cierre posterior
    Then el sistema actualiza el cierre
    And vuelve al detalle mostrando el nuevo valor

  @edge-case
  Scenario: Rechazo del servidor al intentar acortar con evaluaciones activas
    Given una actividad con evaluaciones activas
    When el Docente intenta guardar un cierre anterior al actual
    Then el backend responde 422 NoSePuedeAcortarConEvaluacionesActivas
    And el formulario muestra el error inline sin navegar

  @happy-path
  Scenario: Cierre manual de una actividad
    Given un Docente en el detalle de una actividad no cerrada
    When confirma "Sí, cerrar actividad ahora"
    Then el sistema cierra la actividad y finaliza en cascada sus evaluaciones activas
    And vuelve al detalle mostrando el estado Cerrada
