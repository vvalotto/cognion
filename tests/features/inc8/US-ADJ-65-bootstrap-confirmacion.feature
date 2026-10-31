@US-ADJ-65
Feature: El comando que crea el Administrador pide la contraseña dos veces (US-ADJ-65)
  Como persona que instala Cognión y crea el primer Administrador por terminal
  Quiero escribir la contraseña dos veces y que el comando me avise si no coinciden
  Para no quedar fuera del sistema por un error de tipeo que no veo, porque la contraseña no se muestra

  @confirmacion @happy-path
  Scenario: Las dos entradas coinciden
    Given una instalación sin Administrador y una terminal interactiva
    When se escribe dos veces la misma contraseña válida
    Then se crea el Administrador
    And la salida es 0

  @confirmacion
  Scenario: No coinciden y luego sí
    Given una instalación sin Administrador y una terminal interactiva
    When la primera vez las dos entradas son distintas y la segunda vez iguales
    Then se muestra "Las contraseñas no coinciden."
    And se crea el Administrador
    And la salida es 0

  @confirmacion @error
  Scenario: No coinciden tres veces
    Given una instalación sin Administrador y una terminal interactiva
    When las dos entradas son distintas las tres veces
    Then no se crea ningún usuario
    And se muestra un mensaje claro de que no se creó nada
    And la salida es 1

  @invariante @error
  Scenario: Coinciden pero no cumplen las reglas
    Given una instalación sin Administrador y una terminal interactiva
    When se escribe dos veces la misma contraseña corta
    Then no se crea ningún usuario
    And se muestra el mensaje de contraseña rechazada
    And la salida es 1

  @regresion
  Scenario: ADMIN_PASSWORD definida no pide nada
    Given una instalación sin Administrador y la variable ADMIN_PASSWORD definida
    When se ejecuta el comando
    Then no se pide ninguna contraseña
    And se crea el Administrador
    And la salida es 0

  @regresion @error
  Scenario: Sin terminal y sin variable
    Given una instalación sin Administrador, sin terminal interactiva y sin ADMIN_PASSWORD
    When se ejecuta el comando
    Then se muestra el mensaje de siempre
    And la salida es 2

  @regresion
  Scenario: Ya existe un Administrador operativo
    Given una instalación con un Administrador operativo y una terminal interactiva
    When se ejecuta el comando
    Then no se pide ninguna contraseña
    And se muestra que ya existe un Administrador
    And la salida es 0
