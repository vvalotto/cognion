@US-3.4.7
Feature: Finalización y revisión de la evaluación (US-3.4.7)
  Como Estudiante
  Quiero finalizar mi evaluación cuando termine, y ver de inmediato el detalle de cada
  pregunta con lo que respondí y si estuvo bien
  Para conocer mi resultado sin esperar a que el docente lo publique (RF-13)

  @happy-path
  Scenario: Finalizar manualmente
    Given un Estudiante en la pantalla de rendir con al menos una pregunta respondida
    When elige finalizar
    Then el sistema finaliza la Evaluacion
    And navega a la pantalla de revisión

  @happy-path
  Scenario: Ver revisión con aciertos y errores
    Given una Evaluacion Finalizada con 7 respuestas correctas y 3 incorrectas
    When el Estudiante entra a la revisión
    Then ve el resumen "7 correctas, 3 incorrectas, 10 total"
    And cada pregunta incorrecta muestra también la respuesta correcta

  @edge-case
  Scenario: Acceso posterior desde el listado
    Given una actividad ya finalizada por el Estudiante
    When entra al listado de actividades y elige esa tarjeta
    Then va directo a la revisión, sin pasar por la pantalla de rendir
