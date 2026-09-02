@US-3.1.2
Feature: Docente crea una actividad de período abierto (US-3.1.2)
  Como Docente
  Quiero crear una actividad de período abierto indicando la materia, la ventana de
  disponibilidad, la cantidad de preguntas y los intentos permitidos
  Para habilitar a mis estudiantes a rendir una evaluación de forma asincrónica dentro de esa
  ventana (RF-11)

  @backend @happy-path
  Scenario: Docente crea una actividad válida
    Given un Docente autenticado
    And la materia "Ingeniería de Software" tiene 20 preguntas activas en su banco
    When ejecuta CrearActividadPeriodoAbierto con cantidad_preguntas=10 y cantidad_intentos_permitidos=1
    Then el sistema persiste ActividadEvaluativaPeriodoAbierto con cerrada_manualmente=false
    And se emite el evento ActividadEvaluativaCreada

  @backend @error
  Scenario: Rechazo por preguntas insuficientes
    Given una materia con solo 5 preguntas activas en su banco
    When un Docente ejecuta CrearActividadPeriodoAbierto con cantidad_preguntas=10
    Then el sistema rechaza la operación con PreguntasInsuficientes
    And no se persiste ninguna actividad

  @backend @error
  Scenario: Rechazo por período inválido
    Given un Docente autenticado
    When ejecuta CrearActividadPeriodoAbierto con fecha_apertura posterior a fecha_cierre
    Then el sistema rechaza la operación con PeriodoInvalido

  @backend @error
  Scenario: Rechazo por cantidad de intentos inválida
    Given un Docente autenticado
    When ejecuta CrearActividadPeriodoAbierto con cantidad_intentos_permitidos=0
    Then el sistema rechaza la operación con CantidadIntentosInvalida

  @backend @error
  Scenario: Rechazo por materia inexistente
    Given un materia_id que no existe en BC Banco de Preguntas
    When un Docente ejecuta CrearActividadPeriodoAbierto con ese materia_id
    Then el sistema rechaza la operación con MateriaNoExiste
