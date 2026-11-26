@US-12.2.1
Feature: Cada operación se guarda entera o no se guarda (US-12.2.1)
  Como administrador o docente que opera la plataforma
  Quiero que una operación se guarde entera o no se guarde
  Para que un fallo a mitad de camino no deje una materia sin banco ni un enlace de recuperación que se pueda usar dos veces

  @backend @happy-path
  Scenario: Crear una materia guarda la materia y su banco juntos
    Given un administrador
    When crea la materia "Programación"
    Then existe la materia "Programación"
    And esa materia tiene su banco

  @backend @error
  Scenario: Si falla el guardado del banco no queda la materia
    Given un administrador y un fallo al guardar el banco
    When crea la materia "Programación"
    Then la respuesta es un error de servidor
    And no existe la materia "Programación"

  @backend @error
  Scenario: Si falla marcar el token, la contraseña no cambia y el token sigue vigente
    Given un usuario con un token de recuperación vigente y un fallo al marcar el token como usado
    When confirma la nueva contraseña con ese token
    Then la respuesta es un error de servidor
    And la contraseña del usuario es la anterior
    And el token sigue sin usar

  @backend @error
  Scenario: Si falla consumir la invitación no queda el estudiante
    Given una invitación vigente y un fallo al consumir la invitación
    When un estudiante se registra con esa invitación
    Then la respuesta es un error de servidor
    And no existe el estudiante
    And la invitación sigue vigente

  @backend @error
  Scenario: Si falla el nuevo token, los tokens anteriores siguen vigentes
    Given un usuario con un token de recuperación vigente y un fallo al guardar el token nuevo
    When solicita recuperar su contraseña
    Then la respuesta es un error de servidor
    And el token anterior sigue vigente

  @backend @error
  Scenario: Si falla borrar al usuario, sus tokens no se pierden
    Given un administrador, un usuario con un token de recuperación y un fallo al borrar al usuario
    When elimina la cuenta de ese usuario
    Then la respuesta es un error de servidor
    And el usuario existe
    And su token de recuperación existe

  @backend @seguridad
  Scenario: Un error de seguridad conserva su efecto
    Given un usuario al que le falta un intento para bloquearse
    When ingresa una contraseña incorrecta
    Then la respuesta es de credenciales inválidas
    And la cuenta queda bloqueada

  @backend @error
  Scenario: Si falla el commit, el cliente no recibe un 200
    Given un administrador y un fallo al confirmar la transacción
    When crea la materia "Programación"
    Then la respuesta es un error de servidor
    And no existe la materia "Programación"
