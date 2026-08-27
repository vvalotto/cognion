Feature: Finalización de la evaluación y revisión completa (US-3.2.3)

  Scenario: Estudiante finaliza una evaluación en curso
    Given una Evaluacion EnCurso con algunas respuestas registradas
    When el Estudiante ejecuta FinalizarEvaluacion(evaluacion_id)
    Then el estado pasa a Finalizada
    And se emite el evento EvaluacionFinalizada

  Scenario: Estudiante finaliza una evaluación suspendida
    Given una Evaluacion Suspendida
    When el Estudiante ejecuta FinalizarEvaluacion(evaluacion_id)
    Then el estado pasa a Finalizada

  Scenario: Rechazo al finalizar una evaluación ya finalizada
    Given una Evaluacion Finalizada
    When el Estudiante intenta FinalizarEvaluacion de nuevo
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  Scenario: Revisión disponible tras finalizar
    Given una Evaluacion Finalizada con 3 preguntas asignadas, 2 respondidas correctamente y 1 incorrectamente
    When el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)
    Then el sistema devuelve el detalle de las 3 preguntas
    And la pregunta incorrecta incluye la respuesta correcta
    And las preguntas correctas no incluyen la respuesta correcta
    And el resumen indica 2 correctas y 1 incorrecta sobre 3

  Scenario: Revisión incluye preguntas no respondidas como incorrectas
    Given una Evaluacion Finalizada con una PreguntaAsignada sin ninguna Respuesta
    When el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)
    Then esa pregunta aparece con respondida = false
    And cuenta como incorrecta en el resumen
    And incluye la respuesta correcta

  Scenario: Revisión usa la respuesta vigente ante reintentos
    Given una Evaluacion Finalizada con 2 Respuesta para la misma pregunta, la primera incorrecta y la segunda (más reciente) correcta
    When el Estudiante ejecuta ObtenerRevisionEvaluacion(evaluacion_id)
    Then esa pregunta aparece como correcta con la respuesta más reciente

  Scenario: Rechazo de la revisión antes de finalizar (EnCurso)
    Given una Evaluacion EnCurso
    When el Estudiante intenta ObtenerRevisionEvaluacion
    Then el sistema rechaza la operación con EvaluacionNoFinalizada

  Scenario: Rechazo de la revisión antes de finalizar (Suspendida)
    Given una Evaluacion Suspendida
    When el Estudiante intenta ObtenerRevisionEvaluacion
    Then el sistema rechaza la operación con EvaluacionNoFinalizada
