# language: es
@US-6.3.9
Feature: Estudiante responde y ve su resultado (US-6.3.9)

  Scenario: Espera de opciones
    Given una pregunta presentada sin opciones
    When el Estudiante la mira
    Then ve "Pregunta N de total", el enunciado y el mensaje de espera

  Scenario: Aparecen las tarjetas
    Given la espera de opciones
    When llega opciones_mostradas
    Then aparecen las tarjetas de color y arranca el temporizador

  Scenario: Responder con un toque
    Given las tarjetas visibles
    When el Estudiante toca una
    Then se envía la respuesta sin pedir confirmación y ve su resultado

  Scenario: Un solo intento
    Given una respuesta enviada
    When el Estudiante intenta tocar otra tarjeta
    Then las tarjetas están deshabilitadas y no se envía nada

  Scenario: Verdadero/Falso
    Given una pregunta de Verdadero/Falso
    When se muestran las opciones
    Then hay dos tarjetas y responde con el valor booleano

  Scenario: Tres opciones
    Given una pregunta de 3 opciones
    When se muestran las opciones
    Then hay tres tarjetas y la tercera ocupa el ancho completo

  Scenario: Resultado correcto sin ranking
    Given una respuesta correcta
    When se muestra el resultado
    Then ve "¡Correcto!", los puntos de la pregunta y su acumulado, sin ranking ni posición

  Scenario: Resultado incorrecto
    Given una respuesta incorrecta
    When se muestra el resultado
    Then ve "Incorrecto" y +0 puntos

  Scenario: Tiempo agotado al tocar
    Given un toque fuera del tiempo límite
    When el servidor responde TiempoAgotado
    Then ve "Se acabó el tiempo" con su acumulado

  Scenario: No respondió y se cerró la pregunta
    Given una pregunta abierta que el Estudiante dejó pasar
    When llega pregunta_cerrada
    Then ve "no respondiste (+0)" con su acumulado

  Scenario: Pasa a la siguiente pregunta solo
    Given el resultado de una pregunta
    When llega pregunta_presentada
    Then vuelve a la espera de opciones de la nueva pregunta

  Scenario: Resultado final con posición
    Given la sesión finalizada
    When el Estudiante ve el resultado final
    Then ve "Quedaste N° con X puntos", el Top 3 con nombres y su fila resaltada

  Scenario: Fuera del Top 3
    Given un Estudiante que quedó 5°
    When ve el resultado final
    Then ve el Top 3 y su propia fila con su posición debajo

  Scenario: Reconexión con la pregunta abierta
    Given un Estudiante que pierde la conexión con la pregunta abierta
    When se reconecta
    Then recupera la pregunta, el tiempo restante y su avance sin perder su participación

  Scenario: Recarga después de responder
    Given un Estudiante que ya respondió
    When recarga la pantalla
    Then ve su resultado y no puede volver a responder
