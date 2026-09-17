@US-ADJ-41
Feature: Autoregistro de Docente (US-ADJ-41)
  Como un Docente que todavía no tiene cuenta en el sistema
  Quiero crear mi propia cuenta sin depender de que un Administrador me dé de alta
  Para empezar a usar la plataforma sin fricción

  @autoregistro-docente @happy-path
  Scenario: Autoregistro exitoso con datos válidos
    Given ningún Usuario tiene el email "docente.nuevo.bddadj41@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/docente con datos válidos
    Then la respuesta es 201 Created con los datos del Usuario creado
    And el Usuario tiene perfil Docente y queda activo de inmediato

  @autoregistro-docente @error
  Scenario: Rechazo por email ya registrado
    Given un Usuario ya existe con el email "docente.duplicado.bddadj41@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/docente con ese mismo email
    Then la respuesta es 409 Conflict
    And no se crea ningún Usuario nuevo

  @autoregistro-docente @error
  Scenario: Rechazo por contraseña insegura
    Given ningún Usuario tiene el email "docente.debil.bddadj41@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/docente con una contraseña débil
    Then la respuesta es 422 Unprocessable Content
    And no se crea ningún Usuario nuevo

  @autoregistro-docente @happy-path
  Scenario: La cuenta autoregistrada puede loguearse de inmediato
    Given un Docente se autoregistró exitosamente con el email "docente.login.bddadj41@fiuner.edu.ar"
    When hace POST /identidad/login con ese email y esa contraseña
    Then la respuesta es 200 OK con un JWT válido
