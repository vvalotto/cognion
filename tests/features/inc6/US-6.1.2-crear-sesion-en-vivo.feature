@US-6.1.2
Feature: Docente crea una sesión en vivo (US-6.1.2)
  Como Docente
  Quiero crear una sesión en vivo para una Comisión puntual, indicando cuántas preguntas y
  cuánto tiempo por pregunta
  Para arrancarla en clase con el set de preguntas ya fijado de antemano, igual para todos los
  que se unan (RF-08)

  @backend @happy-path
  Scenario: Creación exitosa
    Given una Comisión existente cuya Materia tiene un Banco con preguntas activas suficientes
    When el Docente crea una sesión en vivo con cantidad_preguntas=10 y tiempo_limite_por_pregunta_segundos=30
    Then la sesión queda en estado EnEspera con 10 preguntas fijadas al azar
    And la respuesta HTTP es 201 con el sesion_id creado

  @backend @error
  Scenario: Preguntas insuficientes en el banco
    Given una Comisión cuya Materia tiene un Banco con solo 5 preguntas activas
    When el Docente intenta crear una sesión en vivo con cantidad_preguntas=10
    Then el sistema rechaza la operación con PreguntasInsuficientes (422)
    And no se crea ninguna sesión

  @backend @error
  Scenario: Tiempo límite inválido
    Given una Comisión con preguntas suficientes
    When el Docente intenta crear una sesión en vivo con tiempo_limite_por_pregunta_segundos=0
    Then el sistema rechaza la operación con TiempoLimiteInvalido (422)

  @backend @error
  Scenario: Comisión inexistente
    Given un comision_id que no corresponde a ninguna Comisión
    When el Docente intenta crear una sesión en vivo
    Then el sistema rechaza la operación con ComisionNoExiste (404)

  @backend @error
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta crear una sesión en vivo
    Then el sistema responde 403
