@US-1.1.9
Feature: Alta de Docente desde la UI (US-1.1.9)
  Como Administrador autenticado
  Quiero dar de alta una cuenta de Docente desde una pantalla web
  Para poder asignarla luego a una comisión y que ese Docente genere invitaciones

  @happy-path
  Scenario: Alta exitosa de un Docente
    Given un Administrador autenticado
    When completa el formulario de alta de Docente con datos válidos
    Then el sistema crea el Usuario con perfil Docente
    And muestra la pantalla de confirmación
    And aclara que el Docente todavía no está asignado a ninguna comisión

  @error
  Scenario: Alta rechazada por email duplicado
    Given un Administrador autenticado
    And un Usuario ya existe con el email que se va a usar
    When completa el formulario de alta de Docente con ese email
    Then el sistema muestra el error en el propio formulario

  @error @rbac
  Scenario: Acceso sin sesión
    Given ningún actor autenticado
    When intenta acceder a la pantalla de alta de Docente
    Then el sistema redirige a login

  @error @rbac
  Scenario: Acceso con rol insuficiente
    Given un Docente autenticado (no Administrador)
    When intenta acceder a la pantalla de alta de Docente
    Then el sistema muestra acceso denegado
