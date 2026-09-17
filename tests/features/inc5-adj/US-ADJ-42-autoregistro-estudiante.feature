@US-ADJ-42
Feature: Autoregistro de Estudiante (US-ADJ-42)
  Como un Estudiante que todavía no tiene cuenta en el sistema
  Quiero crear mi propia cuenta eligiendo mi Comisión
  Para empezar a rendir evaluaciones sin depender de una invitación de mi Docente

  @autoregistro-estudiante @happy-path
  Scenario: Autoregistro exitoso con datos válidos
    Given una Comisión existente
    And ningún Usuario tiene el email "estudiante.nuevo.bddadj42@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/estudiante con datos válidos y el id de esa Comisión
    Then la respuesta es 201 Created con los datos del Usuario creado
    And el Usuario tiene perfil Estudiante, queda asignado a esa Comisión y activo de inmediato

  @autoregistro-estudiante @error
  Scenario: Rechazo por email ya registrado
    Given una Comisión existente
    And un Usuario ya existe con el email "estudiante.duplicado.bddadj42@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/estudiante con ese mismo email
    Then la respuesta es 409 Conflict
    And no se crea ningún Usuario nuevo

  @autoregistro-estudiante @error
  Scenario: Rechazo por comisión inexistente
    Given ningún Usuario tiene el email "estudiante.sincomision.bddadj42@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/estudiante con un comision_id que no existe
    Then la respuesta es 422 Unprocessable Content
    And no se crea ningún Usuario nuevo

  @autoregistro-estudiante @error
  Scenario: Rechazo por contraseña insegura
    Given una Comisión existente
    And ningún Usuario tiene el email "estudiante.debil.bddadj42@fiuner.edu.ar"
    When se solicita POST /identidad/autoregistro/estudiante con una contraseña débil
    Then la respuesta es 422 Unprocessable Content
    And no se crea ningún Usuario nuevo

  @autoregistro-estudiante @happy-path
  Scenario: La cuenta autoregistrada puede loguearse de inmediato
    Given un Estudiante se autoregistró exitosamente con el email "estudiante.login.bddadj42@fiuner.edu.ar"
    When hace POST /identidad/login con ese email y esa contraseña
    Then la respuesta es 200 OK con un JWT válido
