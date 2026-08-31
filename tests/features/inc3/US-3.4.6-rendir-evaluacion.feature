@US-3.4.6
Feature: Rendir evaluación — responder, pausar y reanudar (US-3.4.6)
  Como Estudiante
  Quiero responder mis preguntas una a una, con la certeza de que cada respuesta confirmada
  queda guardada, y poder pausar y retomar sin perder nada
  Para rendir la evaluación de forma confiable aunque se corte la conexión
  (RNF Confiabilidad, RF-12)

  @backend @happy-path
  Scenario: Confirmar una respuesta
    Given un Estudiante en la pregunta actual de una Evaluacion EnCurso
    When elige una opción y confirma
    Then el sistema persiste la Respuesta de inmediato
    And avanza a la siguiente pregunta

  @backend @confiabilidad
  Scenario: Reconexión sin pérdida
    Given un Estudiante que ya confirmó 3 de 10 respuestas
    When recarga la página o vuelve a entrar más tarde
    Then retoma en la misma Evaluacion, con las 3 respuestas ya marcadas como respondidas
    And no se genera un nuevo set de preguntas

  @backend @happy-path
  Scenario: Pausar y salir
    Given un Estudiante en una Evaluacion EnCurso
    When toca "Pausar y salir"
    Then el sistema suspende la Evaluacion
    And navega a la pantalla de evaluación suspendida

  @backend @happy-path
  Scenario: Reanudar desde suspendida
    Given un Estudiante con una Evaluacion Suspendida
    When toca "Continuar" en la pantalla de evaluación suspendida
    Then vuelve a rendir en el mismo punto donde quedó

  @backend @happy-path
  Scenario: El contenido de la pregunta no expone la respuesta correcta
    Given una pregunta asignada dentro de una Evaluacion EnCurso
    When el Estudiante consulta el contenido de la pregunta actual
    Then ve el enunciado y las opciones
    And ninguna opción indica si es correcta
