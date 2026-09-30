@US-6.2.2
Feature: Docente muestra las opciones de la pregunta actual (US-6.2.2)
  Como Docente
  Quiero revelar las opciones de la pregunta cuando ya leí el enunciado en voz alta
  Para decidir yo cuándo arranca el temporizador y todos empiezan a responder al mismo tiempo

  @backend @happy-path
  Scenario: Mostrar opciones de una pregunta de opción múltiple
    Given una sesión EnCurso con el enunciado de la primera pregunta presentado
    When el Docente muestra las opciones
    Then opciones_mostradas pasa a verdadero y queda registrado el instante
    And todos los conectados reciben las opciones sin indicar la correcta
    And la respuesta HTTP es 200

  @backend @happy-path
  Scenario: Mostrar opciones de una pregunta de Verdadero/Falso
    Given una sesión EnCurso cuya pregunta actual es de Verdadero/Falso
    When el Docente muestra las opciones
    Then el mensaje indica el tipo de pregunta y no trae lista de opciones

  @backend @error
  Scenario: Rechazo si las opciones ya estaban mostradas
    Given una pregunta con las opciones ya mostradas
    When el Docente intenta mostrarlas de nuevo
    Then el sistema rechaza con OpcionesYaMostradas (422) sin emitir un evento nuevo

  @backend @error
  Scenario: Rechazo si la sesión no está en curso
    Given una sesión en estado EnEspera
    When el Docente intenta mostrar las opciones
    Then el sistema rechaza con SesionNoEnCurso (422)

  @backend @error
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta mostrar las opciones
    Then el sistema rechaza con SesionNoExiste (404)

  @backend @error
  Scenario: Rechazo por rol
    Given un usuario autenticado con rol Estudiante
    When intenta mostrar las opciones
    Then el sistema responde 403
