@US-3.1.3
Feature: Estudiante inicia su evaluación con set aleatorio fijo (US-3.1.3)
  Como Estudiante
  Quiero iniciar mi evaluación dentro de una actividad de período abierto y recibir un set de
  preguntas propio
  Para empezar a responder sabiendo que ese set no cambia si me reconecto (RF-12, RNF
  Confiabilidad)

  @backend @happy-path
  Scenario: Estudiante inicia su evaluación por primera vez
    Given una ActividadEvaluativaPeriodoAbierto vigente con cantidad_preguntas=10
    And un Estudiante autenticado sin Evaluacion previa para esa actividad
    When ejecuta IniciarEvaluacion(actividad_id, estudiante_id)
    Then el sistema crea una Evaluacion con estado EnCurso
    And preguntas_asignadas tiene exactamente 10 PreguntaAsignada
    And se emite el evento EvaluacionIniciada

  @backend @happy-path
  Scenario: Reconexión — idempotencia sin nuevo set
    Given una Evaluacion EnCurso ya existente para (actividad_id, estudiante_id)
    When el mismo Estudiante ejecuta IniciarEvaluacion(actividad_id, estudiante_id) de nuevo
    Then el sistema devuelve la misma Evaluacion existente
    And preguntas_asignadas es idéntico al set original (mismo orden, mismas preguntas)
    And no se emite un nuevo evento EvaluacionIniciada

  @backend @happy-path
  Scenario: Dos estudiantes reciben sets distintos
    Given una ActividadEvaluativaPeriodoAbierto vigente con más preguntas activas que cantidad_preguntas
    When dos Estudiantes distintos ejecutan IniciarEvaluacion cada uno por su cuenta
    Then cada uno recibe su propia Evaluacion con un set de preguntas propio

  @backend @error
  Scenario: Rechazo antes de la apertura
    Given una ActividadEvaluativaPeriodoAbierto con fecha_apertura futura
    When un Estudiante ejecuta IniciarEvaluacion(actividad_id, estudiante_id)
    Then el sistema rechaza la operación con FueraDePeriodo

  @backend @error
  Scenario: Rechazo después del cierre
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre pasada
    When un Estudiante sin Evaluacion previa ejecuta IniciarEvaluacion(actividad_id, estudiante_id)
    Then el sistema rechaza la operación con FueraDePeriodo
