@US-3.3.2
Feature: Docente cierra una actividad manualmente antes de tiempo (US-3.3.2)
  Como Docente
  Quiero cerrar una actividad antes de su fecha de cierre programada, finalizando de inmediato
  cualquier evaluación que siga en curso
  Para cortar la actividad cuando ya no tiene sentido seguir esperando, sin tener que esperar
  al vencimiento pasivo del período

  @backend @happy-path
  Scenario: Cerrar una actividad sin evaluaciones activas
    Given una ActividadEvaluativaPeriodoAbierto vigente sin ninguna Evaluacion EnCurso o Suspendida
    When el Docente ejecuta CerrarActividad
    Then se emite ActividadEvaluativaCerrada
    And cerrada_manualmente pasa a true

  @backend @happy-path
  Scenario: Cerrar una actividad finaliza en cascada las evaluaciones EnCurso
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existen dos Evaluacion EnCurso de esa actividad
    When el Docente ejecuta CerrarActividad
    Then se emite ActividadEvaluativaCerrada
    And ambas Evaluacion pasan a Finalizada
    And cada una emite EvaluacionFinalizada con actor "sistema"

  @backend @happy-path
  Scenario: Cerrar una actividad finaliza en cascada las evaluaciones Suspendidas tambien
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existe una Evaluacion Suspendida de esa actividad
    When el Docente ejecuta CerrarActividad
    Then la Evaluacion pasa a Finalizada

  @backend @error
  Scenario: Cerrar una actividad ya cerrada es rechazado
    Given una ActividadEvaluativaPeriodoAbierto con cerrada_manualmente = true
    When el Docente ejecuta CerrarActividad de nuevo
    Then se rechaza con ActividadYaCerrada
    And no se emite un segundo ActividadEvaluativaCerrada

  @backend @error
  Scenario: Modificar el periodo despues de un cierre manual es rechazado
    Given una ActividadEvaluativaPeriodoAbierto con cerrada_manualmente = true
    When el Docente ejecuta ModificarPeriodoDisponibilidad
    Then se rechaza con ActividadYaCerrada

  @backend @error
  Scenario: Cerrar una actividad inexistente se rechaza
    When el Docente ejecuta CerrarActividad sobre un actividad_id que no existe
    Then se rechaza con ActividadNoExiste
