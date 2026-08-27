@US-3.2.1
Feature: Estudiante confirma una respuesta con persistencia atómica (US-3.2.1)
  Como Estudiante
  Quiero confirmar mi respuesta a una pregunta de mi evaluación y que quede guardada al
  instante
  Para no perder esa respuesta si me desconecto justo después de confirmarla (RNF
  Confiabilidad, RF-13)

  @backend @happy-path
  Scenario: Estudiante confirma una respuesta válida (opción múltiple)
    Given una Evaluacion EnCurso con una PreguntaAsignada de tipo opción múltiple
    When el Estudiante ejecuta RegistrarRespuesta(evaluacion_id, pregunta_id, {opcion_indice: 1})
    Then el sistema crea una Respuesta con numero_intento=1 y es_correcta calculado
    And se emite el evento RespuestaRegistrada
    And la respuesta HTTP no informa si es_correcta

  @backend @happy-path
  Scenario: Segundo intento sobre la misma pregunta dentro del límite
    Given una Evaluacion EnCurso con cantidad_intentos_permitidos=2
    And ya existe una Respuesta previa (numero_intento=1) para esa pregunta
    When el Estudiante confirma una nueva respuesta para la misma pregunta
    Then el sistema crea una segunda Respuesta con numero_intento=2
    And ambas Respuesta conviven en la colección — la de numero_intento=2 es la vigente

  @backend @error
  Scenario: Rechazo por intentos agotados
    Given una Evaluacion EnCurso con cantidad_intentos_permitidos=1
    And ya existe una Respuesta previa para esa pregunta
    When el Estudiante intenta confirmar una nueva respuesta para la misma pregunta
    Then el sistema rechaza la operación con IntentosAgotados
    And no se persiste ninguna Respuesta nueva

  @backend @error
  Scenario: Rechazo por pregunta no asignada
    Given una Evaluacion EnCurso
    When el Estudiante ejecuta RegistrarRespuesta con un pregunta_id fuera de su set asignado
    Then el sistema rechaza la operación con PreguntaNoAsignada

  @backend @error
  Scenario: Rechazo sobre evaluación suspendida
    Given una Evaluacion en estado Suspendida
    When el Estudiante intenta RegistrarRespuesta
    Then el sistema rechaza la operación con EvaluacionSuspendida

  @backend @error
  Scenario: Rechazo sobre evaluación finalizada
    Given una Evaluacion en estado Finalizada
    When el Estudiante intenta RegistrarRespuesta
    Then el sistema rechaza la operación con EvaluacionYaFinalizada

  @backend @error
  Scenario: Rechazo fuera del período vigente
    Given una Evaluacion EnCurso cuya actividad ya pasó su fecha_cierre
    When el Estudiante intenta RegistrarRespuesta
    Then el sistema rechaza la operación con FueraDePeriodo

  @backend @confiabilidad
  Scenario: Persistencia atómica ante desconexión simulada
    Given un Estudiante que confirma una Respuesta
    When el proceso backend se reinicia inmediatamente después de la confirmación
    Then la Respuesta persiste en el event store al reiniciar el proceso
    And se reconstruye correctamente por replay del stream de la Evaluacion
