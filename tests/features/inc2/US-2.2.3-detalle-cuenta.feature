@US-2.2.3
Feature: Detalle de una cuenta (US-2.2.3)
  Como Administrador
  Quiero ver el detalle completo de una cuenta puntual
  Para confirmar su estado antes de decidir si necesita un reseteo de contraseña o
  desbloqueo (RF-03)

  @detalle-cuenta @happy-path
  Scenario: Detalle de un Estudiante
    Given un Usuario con perfil Estudiante asignado a una Comisión
    When un Administrador ejecuta ObtenerCuenta(usuario_id)
    Then el sistema devuelve sus datos incluyendo comision_id

  @detalle-cuenta @happy-path
  Scenario: Detalle de un Docente
    Given un Usuario con perfil Docente
    When un Administrador ejecuta ObtenerCuenta(usuario_id)
    Then el sistema devuelve sus datos con comision_id en null

  @detalle-cuenta @error
  Scenario: Cuenta inexistente
    Given ningún Usuario tiene el id provisto
    When un Administrador ejecuta ObtenerCuenta(usuario_id)
    Then el sistema rechaza con UsuarioNoExiste
