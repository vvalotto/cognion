@US-3.2.4
Feature: VerificadorDeVencimientos - suspension y finalizacion automaticas (US-3.2.4)
  Como Sistema
  Quiero disparar automáticamente lo que un actor humano no disparó a tiempo
  Para que ninguna evaluación quede indefinidamente EnCurso sin actividad, ni sobreviva
  pasivamente al cierre del período (RNF Confiabilidad)

  @backend @happy-path
  Scenario: Regla 1 suspende una Evaluacion inactiva
    Given una Evaluacion EnCurso cuya ultima_actividad_en supera el UMBRAL_INACTIVIDAD
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion pasa a Suspendida
    And se emite EvaluacionSuspendida con actor "sistema"

  @backend @happy-path
  Scenario: Regla 1 no afecta una Evaluacion EnCurso con actividad reciente
    Given una Evaluacion EnCurso cuya ultima_actividad_en es menor al UMBRAL_INACTIVIDAD
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion sigue EnCurso
    And no se emite ningun evento nuevo

  @backend @happy-path
  Scenario: Regla 2 finaliza una Evaluacion EnCurso de una actividad vencida
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el pasado
    And una Evaluacion EnCurso de esa actividad
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion pasa a Finalizada
    And se emite EvaluacionFinalizada con actor "sistema"

  @backend @happy-path
  Scenario: Regla 2 finaliza una Evaluacion Suspendida de una actividad vencida
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el pasado
    And una Evaluacion Suspendida de esa actividad
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion pasa a Finalizada

  @backend @happy-path
  Scenario: Regla 2 no afecta evaluaciones de una actividad todavia vigente
    Given una ActividadEvaluativaPeriodoAbierto con fecha_cierre en el futuro
    And una Evaluacion EnCurso de esa actividad
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion sigue EnCurso

  @backend @confiabilidad
  Scenario: Idempotencia - segunda corrida sobre lo ya procesado es un no-op
    Given una Evaluacion que ya fue Suspendida por una corrida anterior de VerificarVencimientosUseCase
    When se ejecuta VerificarVencimientosUseCase de nuevo
    Then la Evaluacion sigue Suspendida
    And no se levanta ninguna excepcion
    And no se emite un segundo EvaluacionSuspendida

  @backend @confiabilidad
  Scenario: Evaluacion ya Finalizada nunca se reconsidera
    Given una Evaluacion Finalizada
    When se ejecuta VerificarVencimientosUseCase
    Then la Evaluacion no aparece en el resultado de EvaluacionActivaQueryPort.listar_no_finalizadas
