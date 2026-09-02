# El escenario "Modificar una actividad ya cerrada manualmente se rechaza" (ActividadYaCerrada,
# INV-AE-04b) queda fuera de este feature: su precondición (cerrada_manualmente = true) recién
# se puede construir de punta a punta cuando exista CerrarActividad (US-3.3.2). La validación en
# sí está cubierta a nivel unitario en
# tests/unit/inc3/test_actividad_evaluativa_periodo_abierto.py
# (test_actividad_cerrada_manualmente_se_rechaza). Se agrega la verificación BDD end-to-end en
# el feature de US-3.3.2, una vez que esa US puede producir el estado real.
@US-3.3.1
Feature: Docente modifica el periodo de disponibilidad de una actividad vigente (US-3.3.1)
  Como Docente
  Quiero modificar la fecha de cierre de una actividad vigente
  Para responder a imprevistos (RF-11b) sin arriesgar el trabajo de un estudiante que ya
  está en curso

  @backend @happy-path
  Scenario: Extender el plazo siempre se permite
    Given una ActividadEvaluativaPeriodoAbierto vigente con fecha_cierre en el futuro
    And existe una Evaluacion EnCurso de esa actividad
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre posterior
    Then el comando se acepta
    And se emite PeriodoDisponibilidadModificado

  @backend @happy-path
  Scenario: Acortar el plazo sin evaluaciones activas se permite
    Given una ActividadEvaluativaPeriodoAbierto vigente sin ninguna Evaluacion EnCurso o Suspendida
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior
    Then el comando se acepta
    And se emite PeriodoDisponibilidadModificado

  @backend @error
  Scenario: Acortar el plazo con una evaluacion EnCurso se rechaza
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existe una Evaluacion EnCurso de esa actividad
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior
    Then se rechaza con NoSePuedeAcortarConEvaluacionesActivas
    And no se emite ningun evento

  @backend @error
  Scenario: Acortar el plazo con una evaluacion Suspendida tambien se rechaza
    Given una ActividadEvaluativaPeriodoAbierto vigente
    And existe una Evaluacion Suspendida de esa actividad
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior
    Then se rechaza con NoSePuedeAcortarConEvaluacionesActivas

  @backend @error
  Scenario: nueva_fecha_cierre anterior a fecha_apertura se rechaza
    Given una ActividadEvaluativaPeriodoAbierto vigente
    When el Docente ejecuta ModificarPeriodoDisponibilidad con una nueva_fecha_cierre anterior a fecha_apertura
    Then se rechaza con PeriodoInvalido

  @backend @error
  Scenario: Modificar una actividad inexistente se rechaza
    When el Docente ejecuta ModificarPeriodoDisponibilidad sobre un actividad_id que no existe
    Then se rechaza con ActividadNoExiste
