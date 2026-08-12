@US-1.1.0
Feature: Alta de usuarios y comisiones por Administrador (US-1.1.0)
  Como Administrador
  Quiero dar de alta cuentas de usuario (en particular Docentes), crear una Comisión
  y asignar uno o más Docentes a ella
  Para contar con la precondición mínima que necesita todo lo demás del BC Identidad:
  sin un Usuario con perfil Docente y sin una Comisión con al menos un Docente asignado,
  no existe forma de generar una invitación ni de probar el flujo de registro de punta a punta

  Background:
    Given un Administrador autenticado con JWT válido

  @alta-usuario @happy-path
  Scenario: Administrador crea un Docente
    When ejecuta CrearUsuario con nombre, email, password y perfil Docente
    Then el sistema crea un Usuario con perfil Docente en la misma transacción
    And la contraseña se persiste hasheada con bcrypt
    And se emite el evento UsuarioCreado

  @alta-usuario @error
  Scenario: Alta rechazada por email duplicado
    Given un Usuario ya existe con email "docente@fiuner.edu.ar"
    When el Administrador ejecuta CrearUsuario con ese mismo email
    Then el sistema rechaza la operación con EmailYaRegistrado
    And ningún Usuario nuevo se crea

  @alta-comision @happy-path
  Scenario: Administrador crea una Comisión
    When ejecuta CrearComision con materia "Ingeniería de Software" y horario
    Then el sistema persiste la Comisión con docentes_asignados vacío
    And se emite el evento ComisionCreada

  @asignacion-docente @happy-path
  Scenario: Administrador asigna un Docente a una Comisión
    Given una Comisión existente
    And un Usuario con perfil Docente
    When el Administrador ejecuta AsignarDocenteAComision sobre esa Comisión y ese Docente
    Then el Docente queda agregado a Comisión.docentes_asignados
    And se emite el evento DocenteAsignado

  @asignacion-docente @error
  Scenario: Rechazo al asignar un Usuario que no es Docente
    Given una Comisión existente
    And un Usuario existente con perfil Estudiante
    When el Administrador ejecuta AsignarDocenteAComision con ese Usuario
    Then el sistema rechaza la operación con UsuarioNoEsDocente
    And Comisión.docentes_asignados no cambia
