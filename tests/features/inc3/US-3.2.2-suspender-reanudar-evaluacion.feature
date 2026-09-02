@US-3.2.2
Feature: Suspensión y reanudación explícita de la evaluación (US-3.2.2)
  Como Estudiante
  Quiero pausar mi evaluación de forma explícita y reanudarla más tarde
  Para interrumpirla deliberadamente sin perder mis respuestas, dejando registrado que fue
  una pausa consciente y no una simple desconexión

  @backend @happy-path
  Scenario: Estudiante suspende una evaluación en curso
    Given una Evaluacion EnCurso
    When el Estudiante ejecuta SuspenderEvaluacion(evaluacion_id)
    Then el estado pasa a Suspendida
    And se emite el evento EvaluacionSuspendida

  @backend @happy-path
  Scenario: Estudiante reanuda una evaluación suspendida
    Given una Evaluacion Suspendida con respuestas ya registradas
    When el Estudiante ejecuta ReanudarEvaluacion(evaluacion_id)
    Then el estado pasa a EnCurso
    And se emite el evento EvaluacionReanudada
    And las respuestas y el set de preguntas asignadas no cambian

  @backend @happy-path
  Scenario: Reanudar habilita volver a registrar respuestas
    Given una Evaluacion recién reanudada
    When el Estudiante confirma una respuesta
    Then el sistema la registra normalmente sin EvaluacionSuspendida

  @backend @error
  Scenario: Rechazo al suspender una evaluación ya suspendida
    Given una Evaluacion Suspendida
    When el Estudiante intenta SuspenderEvaluacion de nuevo
    Then el sistema rechaza la operación con EvaluacionYaSuspendida

  @backend @error
  Scenario: Rechazo al suspender una evaluación finalizada
    Given una Evaluacion Finalizada
    When el Estudiante intenta SuspenderEvaluacion
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  @backend @error
  Scenario: Rechazo al reanudar una evaluación en curso
    Given una Evaluacion EnCurso
    When el Estudiante intenta ReanudarEvaluacion
    Then el sistema rechaza la operación con EvaluacionNoSuspendida

  @backend @error
  Scenario: Rechazo al reanudar una evaluación finalizada
    Given una Evaluacion Finalizada
    When el Estudiante intenta ReanudarEvaluacion
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  @backend @error
  Scenario: Rechazo al reanudar fuera del período vigente
    Given una Evaluacion Suspendida cuya actividad ya pasó su fecha_cierre
    When el Estudiante intenta ReanudarEvaluacion
    Then el sistema rechaza la operación con FueraDePeriodo

  @backend @confiabilidad
  Scenario: Suspender no valida período vigente
    Given una Evaluacion EnCurso cuya actividad ya pasó su fecha_cierre
    When el Estudiante ejecuta SuspenderEvaluacion
    Then el sistema acepta la operación y el estado pasa a Suspendida
