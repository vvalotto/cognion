@US-6.3.1
Feature: Nombres de los Estudiantes en la sala de espera y el ranking (US-6.3.1)
  Como Docente
  Quiero ver el nombre de cada Estudiante en la sala de espera y en el ranking
  Para que la proyección en el aula muestre personas y no identificadores

  @backend @happy-path
  Scenario: La sala de espera trae los nombres
    Given tres Estudiantes con nombre unidos a una sesión
    When el Docente lista los participantes
    Then cada participante trae su nombre además de su identificador

  @backend @happy-path
  Scenario: El broadcast de participantes trae los nombres
    Given un Docente conectado por WebSocket a una sesión
    When un Estudiante se une a la sesión
    Then el mensaje participantes_actualizados incluye el nombre de cada participante

  @backend @happy-path
  Scenario: El cierre de pregunta trae los nombres en el ranking
    Given una sesión con respuestas registradas para la pregunta actual
    When el Docente cierra la pregunta
    Then el ranking del mensaje pregunta_cerrada incluye el nombre de cada Estudiante

  @backend @happy-path
  Scenario: El ranking final trae los nombres
    Given una sesión finalizada con puntajes acumulados
    When se consulta el ranking de la sesión
    Then cada fila trae el nombre del Estudiante

  @backend @happy-path
  Scenario: El evento sesion_finalizada trae los nombres
    Given una sesión EnCurso con puntajes acumulados
    When el Docente finaliza la sesión
    Then el ranking del mensaje sesion_finalizada incluye el nombre de cada Estudiante

  @backend @error-case
  Scenario: Un Estudiante sin nombre resoluble no rompe el mensaje
    Given un participante cuya cuenta ya no existe en Identidad
    When se publica el ranking de la sesión
    Then esa fila trae el nombre "Estudiante sin nombre"
    And el resto de las filas trae su nombre real

  @backend @performance
  Scenario: El rendimiento del cierre de pregunta se mantiene
    Given 60 participantes que respondieron la pregunta actual
    When se mide el cierre de pregunta 30 veces
    Then el p95 del use case sigue siendo menor o igual a 100 ms
