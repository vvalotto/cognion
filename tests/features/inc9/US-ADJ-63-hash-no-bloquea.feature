@US-ADJ-63
Feature: El hash de contraseñas no bloquea el event loop (US-ADJ-63)
  Como Docente que conduce una sesión en vivo mientras otros usuarios entran a la plataforma
  Quiero que el inicio de sesión de una persona no congele la aplicación para todos los demás
  Para que la proyección y las respuestas de los alumnos no se traben cuando alguien inicia sesión

  @rendimiento @happy-path
  Scenario: Verificar contraseñas no congela al resto de la aplicación
    Given una tarea que registra el paso del tiempo cada 10 milisegundos
    When se verifican 3 contraseñas a la vez con el hasher real
    Then el mayor hueco entre dos registros de tiempo es menor al umbral de bloqueo
    And las 3 verificaciones dan el resultado correcto

  @rendimiento
  Scenario: Crear el hash de una contraseña tampoco congela al resto
    Given una tarea que registra el paso del tiempo cada 10 milisegundos
    When se calculan 3 hashes a la vez con el hasher real
    Then el mayor hueco entre dos registros de tiempo es menor al umbral de bloqueo
    And cada hash verifica contra su contraseña original

  @compatibilidad
  Scenario: Un hash generado antes del cambio se verifica después
    Given un hash bcrypt generado con la implementación anterior
    When se verifica la contraseña original con el hasher nuevo
    Then la verificación es correcta
    And una contraseña distinta es rechazada

  @compatibilidad
  Scenario: El hash nuevo conserva el algoritmo y el costo
    When se calcula el hash de una contraseña con el hasher nuevo
    Then el hash tiene el formato bcrypt con costo 12

  @funcional
  Scenario: El inicio de sesión se comporta igual
    Given un Estudiante con una contraseña conocida
    When inicia sesión con la contraseña correcta y con una incorrecta
    Then la correcta entrega un token y la incorrecta es rechazada

  @guarda
  Scenario: Ningún caso de uso llama al hasher sin esperar
    Given el código de los casos de uso de Identidad
    When se revisan las llamadas al hasher
    Then todas esperan el resultado y ninguna usa la forma que bloquea
